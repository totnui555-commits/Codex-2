from datetime import timedelta

import httpx
import jwt
import pytest
from company_os.db import Session
from company_os.models import AgentRun, Organization, Reservation, Task, ToolCalls, now
from company_os.settings import settings
from conftest import create_task
from sqlalchemy import select


def active_run(client, project):
    task = create_task(client, project, agent_role="backend_engineer")
    with Session.begin() as db:
        org = db.get(Organization, project["organization_id"])
        org.mode = "build_autopilot"
        org.paid_execution_authorized = True
        run = AgentRun(
            organization_id=org.id,
            task_id=task["id"],
            agent_role="backend_engineer",
            provider="test_boundary_transport",
            status="running",
        )
        db.add(run)
        db.flush()
        row = db.get(Task, task["id"])
        row.status = "running"
        row.lease_owner = run.id
        row.lease_until = now() + timedelta(minutes=5)
        db.add(
            Reservation(
                organization_id=org.id,
                task_id=row.id,
                run_id=run.id,
                amount=100,
                state="reserved",
                period=now().strftime("%Y-%m"),
            )
        )
        return run.id, task["id"]


def headers(run_id, expires=True):
    with Session() as db:
        organization_id = db.get(AgentRun, run_id).organization_id
    claims = {"sub": run_id, "aud": "sandbox-model-gateway", "organization_id": organization_id}
    if expires:
        claims["exp"] = now() + timedelta(minutes=5)
    return {"Authorization": "Bearer " + jwt.encode(claims, settings().session_secret, algorithm="HS256")}


def configure(monkeypatch):
    monkeypatch.setattr(settings(), "codex_input_usd_per_million", 0.25)
    monkeypatch.setattr(settings(), "codex_output_usd_per_million", 2)
    monkeypatch.setattr(settings(), "thb_per_usd", 33.555)
    monkeypatch.setattr(settings(), "fx_observed_at", "2026-10-19")
    monkeypatch.setattr(settings(), "codex_provider", "openai")
    monkeypatch.setattr(settings(), "openai_api_key", "test-only-not-a-real-credential")


@pytest.mark.parametrize("policy", ["paid_off", "research_only", "stopped", "expired_lease"])
def test_revocation_blocks_before_upstream(owner_client, project, policy):
    run_id, task_id = active_run(owner_client, project)
    with Session.begin() as db:
        org = db.get(Organization, project["organization_id"])
        if policy == "paid_off":
            org.paid_execution_authorized = False
        elif policy == "research_only":
            org.mode = "research_only"
        elif policy == "stopped":
            org.stopped = True
        else:
            db.get(Task, task_id).lease_until = now() - timedelta(seconds=1)
    response = owner_client.post(
        f"/worker-gateway/{run_id}/v1/responses", headers=headers(run_id), json={"input": "hello"}
    )
    assert response.status_code == 403
    with Session() as db:
        assert db.scalar(select(ToolCalls)) is None


@pytest.mark.parametrize(
    "payload,status",
    [
        ([], 422),
        ({"tools": [None]}, 422),
        ({"stream": "true"}, 422),
        ({"tools": [{"type": "web_search"}]}, 403),
        ({"background": True}, 403),
    ],
)
def test_invalid_requests_do_not_consume_run_allowance(owner_client, project, payload, status):
    run_id, _ = active_run(owner_client, project)
    response = owner_client.post(
        f"/worker-gateway/{run_id}/v1/responses", headers=headers(run_id), json=payload
    )
    assert response.status_code == status
    with Session() as db:
        assert db.scalar(select(ToolCalls)) is None


def test_capabilities_require_expiration(owner_client, project):
    run_id, _ = active_run(owner_client, project)
    assert (
        owner_client.post(
            f"/worker-gateway/{run_id}/v1/responses", headers=headers(run_id, False), json={}
        ).status_code
        == 401
    )


def test_revocation_during_provider_request_keeps_cost_receipt(owner_client, project, monkeypatch):
    configure(monkeypatch)
    run_id, _ = active_run(owner_client, project)
    original = httpx.AsyncClient

    async def respond(request):
        with Session.begin() as db:
            db.get(Organization, project["organization_id"]).paid_execution_authorized = False
        return httpx.Response(200, json={"usage": {"input_tokens": 5, "output_tokens": 2}})

    monkeypatch.setattr(
        "company_os.gateway.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )
    response = owner_client.post(
        f"/worker-gateway/{run_id}/v1/responses", headers=headers(run_id), json={"input": "hello"}
    )
    assert response.status_code == 403
    with Session() as db:
        call = db.scalar(select(ToolCalls))
        assert call.data["state"] == "revoked"
        assert call.data["usage"]["input_tokens"] == 5
        assert db.scalar(select(Reservation)).state == "reserved"


def test_valid_request_forces_model_and_retains_missing_usage(owner_client, project, monkeypatch):
    configure(monkeypatch)
    run_id, _ = active_run(owner_client, project)
    original = httpx.AsyncClient

    async def respond(request):
        import json

        sent = json.loads(request.content)
        assert sent["model"] == settings().codex_model
        assert sent["max_output_tokens"] == 2000
        assert sent["store"] is False and sent["background"] is False
        return httpx.Response(200, json={"id": "boundary-test-response"})

    monkeypatch.setattr(
        "company_os.gateway.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )
    response = owner_client.post(
        f"/worker-gateway/{run_id}/v1/responses",
        headers=headers(run_id),
        json={"input": "hello", "model": "unapproved"},
    )
    assert response.status_code == 200
    with Session() as db:
        assert db.scalar(select(ToolCalls)).data["state"] == "usage_unknown"


def test_stream_revocation_stops_forwarding_and_retains_reservation(owner_client, project, monkeypatch):
    configure(monkeypatch)
    run_id, _ = active_run(owner_client, project)
    original = httpx.AsyncClient

    class ProviderStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b'data: {"type":"response.output_text.delta","delta":"before stop"}\n\n'
            with Session.begin() as db:
                db.get(Organization, project["organization_id"]).stopped = True
            yield b'data: {"type":"response.output_text.delta","delta":"must not forward"}\n\n'

    async def respond(request):
        return httpx.Response(200, stream=ProviderStream(), headers={"content-type": "text/event-stream"})

    monkeypatch.setattr(
        "company_os.gateway.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )
    response = owner_client.post(
        f"/worker-gateway/{run_id}/v1/responses",
        headers=headers(run_id),
        json={"input": "hello", "stream": True},
    )
    assert "before stop" in response.text
    assert "must not forward" not in response.text
    assert "Execution revoked" in response.text
    with Session() as db:
        assert db.scalar(select(ToolCalls)).data["state"] == "revoked"
        assert db.scalar(select(Reservation)).state == "reserved"


def test_gateway_works_under_actual_rls_runtime_role(owner_client, project, monkeypatch):
    from contextlib import contextmanager
    from sqlalchemy import text

    configure(monkeypatch)
    run_id, _ = active_run(owner_client, project)
    original = httpx.AsyncClient

    class RuntimeSessions:
        @staticmethod
        @contextmanager
        def begin():
            with Session.begin() as db:
                db.execute(text("SET LOCAL ROLE company_api"))
                yield db

    async def respond(request):
        return httpx.Response(200, json={"usage": {"input_tokens": 5, "output_tokens": 2}})

    monkeypatch.setattr("company_os.gateway.Session", RuntimeSessions)
    monkeypatch.setattr(
        "company_os.gateway.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )
    response = owner_client.post(
        f"/worker-gateway/{run_id}/v1/responses", headers=headers(run_id), json={"input": "hello"}
    )
    assert response.status_code == 200, response.text
    with Session() as db:
        assert db.scalar(select(ToolCalls)).data["state"] == "completed"
    assert owner_client.get("/audit/verify").json()["valid"]
