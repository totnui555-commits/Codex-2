import hashlib
import hmac
import json
import time
import base64
from datetime import timedelta
import httpx
import pytest
from sqlalchemy import select
from company_os.db import Session
from company_os.models import Revenue, Organization, Delivery, Message, Task, AgentRun, now
from company_os.settings import settings
from company_os.notifications import deliver_pending, ProviderDisconnected
from company_os.providers import validate_export, IntegrationBlocked, DaytonaFactory
from company_os.research import opportunity_score, DIMENSIONS, store_research
from company_os.security import redact
from conftest import create_task


def signature(payload, secret="whsec_test", timestamp=None):
    timestamp = timestamp or int(time.time())
    return (
        f"t={timestamp},v1="
        + hmac.new(secret.encode(), str(timestamp).encode() + b"." + payload, hashlib.sha256).hexdigest()
    )


def test_signed_revenue_no_fakes_replay_or_cross_tenant(owner_client, project, monkeypatch):
    monkeypatch.setattr(settings(), "stripe_webhook_secret", "whsec_test")
    payload = {
        "id": "evt1",
        "livemode": True,
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_1",
                "payment_status": "paid",
                "mode": "payment",
                "amount_total": 12345,
                "currency": "thb",
                "metadata": {"organization_id": project["organization_id"]},
            }
        },
    }
    raw = json.dumps(payload).encode()
    url = "/webhooks/stripe/" + project["organization_id"]
    assert owner_client.post(url, content=raw, headers={"stripe-signature": "bad"}).status_code == 400
    assert (
        owner_client.post(
            url, content=raw, headers={"stripe-signature": signature(raw, timestamp=int(time.time()) - 400)}
        ).status_code
        == 400
    )
    assert owner_client.post(url, content=raw, headers={"stripe-signature": signature(raw)}).json()[
        "recorded"
    ]
    assert owner_client.post(url, content=raw, headers={"stripe-signature": signature(raw)}).json()[
        "duplicate"
    ]
    with Session() as db:
        assert len(db.scalars(select(Revenue)).all()) == 1
    with Session.begin() as db:
        org = Organization(name="Other tenant")
        db.add(org)
        db.flush()
        other = org.id
    assert (
        owner_client.post(
            "/webhooks/stripe/" + other, content=raw, headers={"stripe-signature": signature(raw)}
        ).status_code
        == 403
    )
    payload["livemode"] = False
    payload["data"]["object"]["id"] = "test_session"
    raw = json.dumps(payload).encode()
    assert (
        owner_client.post(url, content=raw, headers={"stripe-signature": signature(raw)}).json()["ignored"]
        == "test_mode_not_real_revenue"
    )


def test_refund_debits_exact_minor_units(owner_client, project, monkeypatch):
    monkeypatch.setattr(settings(), "stripe_webhook_secret", "whsec_test")
    raw = json.dumps(
        {
            "id": "evt_refund",
            "livemode": True,
            "type": "refund.created",
            "data": {
                "object": {
                    "id": "re_1",
                    "status": "succeeded",
                    "amount": 4200,
                    "currency": "thb",
                    "metadata": {"organization_id": project["organization_id"]},
                }
            },
        }
    ).encode()
    assert (
        owner_client.post(
            "/webhooks/stripe/" + project["organization_id"],
            content=raw,
            headers={"stripe-signature": signature(raw)},
        ).status_code
        == 200
    )
    assert owner_client.get("/snapshot").json()["revenue"][0]["amount_minor"] == -4200


async def test_email_disconnected_and_ambiguous_fallback(owner_client):
    class Missing:
        async def send(self, *_):
            raise ProviderDisconnected("No OAuth connection")

    await deliver_pending(Missing())
    with Session.begin() as db:
        d = db.scalars(select(Delivery)).first()
        assert d.state == "disconnected"
        assert d.attempts == 0
        d.next_attempt_at = now() - timedelta(seconds=1)

    class Ambiguous:
        async def send(self, *_):
            raise httpx.ReadTimeout("Unknown outcome")

    await deliver_pending(Ambiguous())
    with Session() as db:
        d = db.scalars(select(Delivery)).first()
        assert d.state == "unknown"
        assert d.provider_id is None
        assert db.scalars(select(Message)).first().state == "open"


async def test_email_sent_requires_provider_receipt(owner_client):
    class Connected:
        async def send(self, *_):
            return "confirmed-message-id"

    await deliver_pending(Connected())
    with Session() as db:
        d = db.scalars(select(Delivery)).first()
        assert d.state == "sent" and d.provider_id == "confirmed-message-id"


def test_hostile_artifact_exports_and_redaction():
    data = b'print("hello")'
    file = {
        "path": "app/main.py",
        "content": base64.b64encode(data).decode(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    assert validate_export([file])
    for path in ["../../escape.py", "/etc/evil.py", ".github/workflows/run.json", ".env", "package.json"]:
        with pytest.raises(ValueError):
            validate_export([{**file, "path": path}])
    with pytest.raises(ValueError):
        validate_export([{**file, "sha256": "0" * 64}])
    assert redact({"api_key": "sk-secret", "text": "Bearer secrettoken"}) == {
        "api_key": "[REDACTED]",
        "text": "[REDACTED]",
    }


def test_sandbox_no_host_fallback(monkeypatch):
    monkeypatch.setattr(settings(), "daytona_api_key", "")
    with pytest.raises(IntegrationBlocked):
        DaytonaFactory()


def test_source_evidence_and_scoring(owner_client, project):
    assert opportunity_score({k: 50 for k in DIMENSIONS}) == 50
    with pytest.raises(ValueError):
        opportunity_score({"vanity": 100})
    source = {
        "title": "A real public discussion",
        "url": "https://news.ycombinator.com/item?id=123",
        "retrieved_at": now().isoformat(),
        "quality": "unvalidated_public_discussion",
    }
    with Session.begin() as db:
        assert len(store_research(db, project["organization_id"], [source])) == 1
        assert store_research(db, project["organization_id"], [source]) == []
    opportunity = owner_client.get("/snapshot").json()["opportunities"][0]
    r = owner_client.post("/opportunities/" + opportunity["id"] + "/incubate")
    assert r.status_code == 200
    assert owner_client.get("/snapshot").json()["tasks"][0]["title"] == "Validate customer pain and MVP scope"
    assert (
        owner_client.post("/opportunities/" + opportunity["id"] + "/incubate").json()["id"] == r.json()["id"]
    )


def test_gateway_requires_scoped_capability(client):
    assert client.post("/worker-gateway/fake/v1/responses", json={"model": "anything"}).status_code == 401
