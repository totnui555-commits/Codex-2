import hashlib
import hmac
import json
import time

from fastapi import HTTPException
from sqlalchemy import select

from .domain import emit, lock_org
from .models import Organization, Revenue
from .settings import settings


def ingest_stripe(db, org_id, raw, signature):
    secret = settings().stripe_webhook_secret
    if not secret:
        raise HTTPException(503, "Billing provider disconnected")
    parts = {}
    for p in signature.split(","):
        if "=" in p:
            k, v = p.split("=", 1)
            parts.setdefault(k, []).append(v)
    try:
        timestamp = int(parts["t"][0])
    except (KeyError, ValueError):
        raise HTTPException(400, "Invalid webhook signature")
    expected = hmac.new(secret.encode(), str(timestamp).encode() + b"." + raw, hashlib.sha256).hexdigest()
    if abs(time.time() - timestamp) > 300 or not any(
        hmac.compare_digest(expected, s) for s in parts.get("v1", [])
    ):
        raise HTTPException(400, "Invalid or stale webhook signature")
    try:
        event = json.loads(raw)
        obj = event["data"]["object"]
    except (ValueError, KeyError, TypeError):
        raise HTTPException(400, "Invalid billing event")
    if not db.get(Organization, org_id):
        raise HTTPException(404, "Organization not found")
    # Verified signatures alone do not establish tenant ownership.
    if obj.get("metadata", {}).get("organization_id") != org_id:
        raise HTTPException(403, "Billing tenant mismatch")
    if not event.get("livemode"):
        return {"ignored": "test_mode_not_real_revenue"}
    kind = event.get("type")
    if (
        kind == "checkout.session.completed"
        and obj.get("payment_status") == "paid"
        and obj.get("mode") == "payment"
    ):
        amount = obj.get("amount_total")
        transaction_kind = "confirmed_gross_revenue"
    elif kind == "refund.created" and obj.get("status") == "succeeded":
        amount = obj.get("amount")
        transaction_kind = "refund"
    else:
        return {"ignored": "unsupported_or_unsettled"}
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise HTTPException(400, "Invalid amount")
    currency = obj.get("currency", "").upper()
    if len(currency) != 3 or not currency.isalpha():
        raise HTTPException(400, "Invalid currency")
    lock_org(db, org_id)
    external_id = "stripe:" + str(obj["id"])
    previous = db.scalar(select(Revenue).where(Revenue.external_id == external_id))
    if previous:
        return {"duplicate": True, "id": previous.id}
    row = Revenue(
        organization_id=org_id,
        provider="stripe",
        external_id=external_id,
        kind=transaction_kind,
        amount_minor=-amount if transaction_kind == "refund" else amount,
        currency=currency,
        details={
            "event_id": event["id"],
            "source": "signed_live_webhook",
            "fees": "unknown",
            "net_cash_received": "unknown",
        },
    )
    db.add(row)
    db.flush()
    emit(
        db,
        org_id,
        "revenue",
        row.id,
        "revenue.verified",
        {"kind": transaction_kind, "amount_minor": row.amount_minor, "currency": currency},
    )
    return {"recorded": True, "id": row.id}
