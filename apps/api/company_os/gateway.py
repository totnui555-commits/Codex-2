"""Short-lived, run-scoped model gateway. No provider credentials enter hosted code."""

import json
from decimal import Decimal

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from .db import Session
from .domain import emit, lock_org
from .models import AgentRun, Project, Reservation, Task, ToolCalls
from .providers import coding_provider_endpoint, token_cost
from .settings import settings

router = APIRouter()


@router.post("/worker-gateway/{run_id}/v1/responses")
async def responses(run_id: str, request: Request):
    bearer = request.headers.get("authorization", "").removeprefix("Bearer ")
    try:
        claims = jwt.decode(
            bearer, settings().session_secret, algorithms=["HS256"], audience="sandbox-model-gateway"
        )
        if claims["sub"] != run_id:
            raise ValueError()
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Invalid run capability")
    raw = await request.body()
    if len(raw) > 64000:
        raise HTTPException(413, "Model input ceiling exceeded")
    try:
        payload = json.loads(raw)
    except ValueError:
        raise HTTPException(422, "Invalid request")
    with Session.begin() as db:
        run = db.get(AgentRun, run_id)
        if not run:
            raise HTTPException(403, "Unknown run")
        org = lock_org(db, run.organization_id)
        task = db.get(Task, run.task_id)
        if (
            run.status != "running"
            or org.stopped
            or task.status != "running"
            or db.get(Project, task.project_id).paused
        ):
            raise HTTPException(403, "Execution capability revoked")
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
    # Prevent model side effects through tools: Codex local tools are client-side only.
    allowed_tool_types = {"function", "custom"}
    if any(t.get("type") not in allowed_tool_types for t in payload.get("tools", [])):
        raise HTTPException(403, "Hosted model tools are disabled")
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
            raise HTTPException(502, "Model provider rejected the request")
    except httpx.HTTPError:
        await client.aclose()
        raise HTTPException(502, "Model provider unavailable; reservation retained for reconciliation")

    async def stream():
        usage = None
        try:
            async for line in upstream.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "response.completed":
                            usage = event["response"]["usage"]
                    except (ValueError, KeyError):
                        pass
                yield line + "\n"
        finally:
            await upstream.aclose()
            await client.aclose()
            with Session.begin() as db:
                call = db.get(ToolCalls, call_id)
                call.data = {**call.data, "state": "completed" if usage else "usage_unknown", "usage": usage}

    if payload.get("stream"):
        return StreamingResponse(stream(), media_type="text/event-stream")
    try:
        body = await upstream.aread()
        data = json.loads(body)
        with Session.begin() as db:
            call = db.get(ToolCalls, call_id)
            call.data = {**call.data, "state": "completed", "usage": data.get("usage")}
        return data
    finally:
        await upstream.aclose()
        await client.aclose()
