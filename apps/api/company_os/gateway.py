"""Short-lived, run-scoped model gateway. No provider credentials enter hosted code."""

import json
from contextlib import contextmanager
from decimal import Decimal

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text

from .db import Session
from .domain import emit, lock_org
from .models import AgentRun, Project, Reservation, Task, ToolCalls, now
from .providers import coding_provider_endpoint, token_cost
from .settings import settings

router = APIRouter()


@contextmanager
def gateway_session(organization_id):
    with Session.begin() as db:
        db.execute(text("SELECT set_config('app.organization_id', :id, true)"), {"id": organization_id})
        yield db


def validate_payload(payload):
    if not isinstance(payload, dict):
        raise HTTPException(422, "Expected a JSON object")
    if "stream" in payload and type(payload["stream"]) is not bool:
        raise HTTPException(422, "stream must be a boolean")
    if payload.get("background") not in (None, False):
        raise HTTPException(403, "Background provider execution is disabled")
    tools = payload.get("tools", [])
    if not isinstance(tools, list) or len(tools) > 64:
        raise HTTPException(422, "Expected at most 64 local tool definitions")
    if any(not isinstance(tool, dict) for tool in tools):
        raise HTTPException(422, "Invalid tool definition")
    if any(tool.get("type") not in {"function", "custom"} for tool in tools):
        raise HTTPException(403, "Hosted model tools are disabled")


def execution_active(db, run_id, organization_id):
    run = db.get(AgentRun, run_id)
    if not run or run.organization_id != organization_id:
        return False
    org = lock_org(db, run.organization_id)
    task = db.get(Task, run.task_id)
    return bool(
        org
        and task
        and run.status == "running"
        and task.status == "running"
        and not org.stopped
        and org.paid_execution_authorized
        and org.mode in {"build_autopilot", "approved_growth"}
        and task.lease_owner == run.id
        and task.lease_until
        and task.lease_until > now()
        and not db.get(Project, task.project_id).paused
        and db.scalar(
            select(Reservation.id).where(Reservation.run_id == run_id, Reservation.state == "reserved")
        )
    )


def finish_call(call_id, state, usage=None, *, organization_id):
    with gateway_session(organization_id) as db:
        call = db.get(ToolCalls, call_id)
        call.data = {**call.data, "state": state, "usage": usage}
        emit(
            db,
            organization_id,
            "tool_call",
            call.id,
            "model." + state,
            {"run_id": call.data["run_id"], "usage": usage},
        )


@router.post("/worker-gateway/{run_id}/v1/responses")
async def responses(run_id: str, request: Request):
    bearer = request.headers.get("authorization", "").removeprefix("Bearer ")
    try:
        claims = jwt.decode(
            bearer,
            settings().session_secret,
            algorithms=["HS256"],
            audience="sandbox-model-gateway",
            options={"require": ["exp", "sub", "aud", "organization_id"]},
        )
        if claims["sub"] != run_id or not isinstance(claims["organization_id"], str):
            raise ValueError()
        organization_id = claims["organization_id"]
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Invalid run capability")
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > 64000:
            raise HTTPException(413, "Model input ceiling exceeded")
        raw.extend(chunk)
    try:
        payload = json.loads(raw)
    except ValueError:
        raise HTTPException(422, "Invalid request")
    validate_payload(payload)
    with gateway_session(organization_id) as db:
        run = db.get(AgentRun, run_id)
        if not run:
            raise HTTPException(403, "Unknown run")
        org = lock_org(db, run.organization_id)
        if not execution_active(db, run_id, organization_id):
            raise HTTPException(403, "Execution capability revoked or lease expired")
        reservation = db.scalar(
            select(Reservation).where(Reservation.run_id == run_id, Reservation.state == "reserved")
        )
        if not reservation:
            raise HTTPException(403, "No active budget reservation")
        calls = db.scalars(select(ToolCalls).where(ToolCalls.organization_id == org.id)).all()
        prior = [c for c in calls if c.data.get("run_id") == run_id]
        # Reserve worst-case per request before provider I/O. No LLM self-reporting.
        ceiling = token_cost(len(raw) + 1000, 2000, coding=True)
        if (
            len(prior) >= 4
            or sum((Decimal(c.data["reserved_cost"]) for c in prior), Decimal(0)) + ceiling
            > reservation.amount
        ):
            raise HTTPException(429, "Run request or cost ceiling reached")
        call = ToolCalls(
            organization_id=org.id,
            data={"run_id": run_id, "state": "requested", "reserved_cost": str(ceiling), "usage": None},
        )
        db.add(call)
        db.flush()
        call_id = call.id
        emit(
            db,
            org.id,
            "tool_call",
            call.id,
            "model.requested",
            {"run_id": run_id, "maximum_output_tokens": 2000},
        )
    payload["model"] = settings().codex_model
    payload["max_output_tokens"] = 2000
    payload["store"] = False
    payload["background"] = False
    provider_url, provider_key = coding_provider_endpoint()
    client = httpx.AsyncClient(timeout=80)
    try:
        upstream = await client.send(
            client.build_request(
                "POST",
                provider_url,
                headers={"Authorization": "Bearer " + provider_key},
                json=payload,
            ),
            stream=True,
        )
        if upstream.status_code >= 400:
            await upstream.aclose()
            await client.aclose()
            finish_call(call_id, "provider_rejected", organization_id=organization_id)
            raise HTTPException(502, "Model provider rejected the request")
    except httpx.HTTPError:
        await client.aclose()
        finish_call(call_id, "usage_unknown", organization_id=organization_id)
        raise HTTPException(502, "Model provider unavailable; reservation retained for reconciliation")

    async def stream():
        usage = None
        revoked = False
        try:
            async for line in upstream.aiter_lines():
                with gateway_session(organization_id) as db:
                    active = execution_active(db, run_id, organization_id)
                if not active:
                    revoked = True
                    yield 'event: error\ndata: {"error":{"message":"Execution revoked"}}\n\n'
                    break
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if isinstance(event, dict) and event.get("type") == "response.completed":
                            usage = event["response"]["usage"]
                    except (ValueError, KeyError, TypeError):
                        pass
                yield line + "\n"
        finally:
            await upstream.aclose()
            await client.aclose()
            finish_call(
                call_id,
                "revoked" if revoked else ("completed" if usage else "usage_unknown"),
                usage,
                organization_id=organization_id,
            )

    if payload.get("stream"):
        return StreamingResponse(stream(), media_type="text/event-stream")
    try:
        body = await upstream.aread()
        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError()
        except (ValueError, TypeError):
            finish_call(call_id, "usage_unknown", organization_id=organization_id)
            raise HTTPException(502, "Invalid model response; reservation retained")
        usage = data.get("usage")
        with gateway_session(organization_id) as db:
            active = execution_active(db, run_id, organization_id)
        finish_call(
            call_id,
            "revoked" if not active else ("completed" if usage else "usage_unknown"),
            usage,
            organization_id=organization_id,
        )
        if not active:
            raise HTTPException(403, "Execution revoked during provider request")
        return data
    finally:
        await upstream.aclose()
        await client.aclose()
