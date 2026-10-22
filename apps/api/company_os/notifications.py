import base64
from datetime import timedelta
from email.message import EmailMessage

import httpx
from sqlalchemy import select

from .db import Session
from .domain import emit
from .models import Delivery, Message, now
from .settings import settings


class ProviderDisconnected(Exception):
    pass


class GmailProvider:
    async def send(self, subject, body):
        s = settings()
        if not s.email_send_authorized:
            raise ProviderDisconnected("Email send permission is not configured")
        token = s.gmail_access_token
        async with httpx.AsyncClient(timeout=20) as client:
            if s.gmail_refresh_token and s.gmail_client_id and s.gmail_client_secret:
                r = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": s.gmail_client_id,
                        "client_secret": s.gmail_client_secret,
                        "refresh_token": s.gmail_refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
                r.raise_for_status()
                token = r.json()["access_token"]
            if not token:
                raise ProviderDisconnected("Gmail OAuth is disconnected")
            message = EmailMessage()
            message["To"] = s.founder_email
            message["Subject"] = subject
            message.set_content(
                body
                + "\n\nAuthenticate to respond: "
                + s.app_origin
                + "/inbox\nEmail replies cannot authorize protected actions."
            )
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            response = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": "Bearer " + token},
                json={"raw": raw},
            )
            response.raise_for_status()
            return response.json()["id"]


async def deliver_pending(provider=None):
    provider = provider or GmailProvider()
    # Lock rows across bounded I/O; retries are capped. Gmail has no idempotency key:
    # ambiguous transport outcomes go to unknown and require owner review, never blind resend.
    with Session.begin() as db:
        rows = db.scalars(
            select(Delivery)
            .where(
                Delivery.state.in_(["pending", "retry", "disconnected"]), Delivery.next_attempt_at <= now()
            )
            .order_by(Delivery.created_at)
            .with_for_update(skip_locked=True)
            .limit(10)
        ).all()
        for row in rows:
            message = db.get(Message, row.message_id)
            try:
                row.attempts += 1
                row.provider_id = await provider.send(
                    "[AI Company OS] [Action Required] " + message.subject, message.body
                )
                row.state = "sent"
                row.error = None
            except ProviderDisconnected as e:
                row.state = "disconnected"
                row.attempts -= 1
                row.error = str(e)
                row.next_attempt_at = now() + timedelta(minutes=5)
            except httpx.HTTPStatusError as e:
                row.state = "retry" if e.response.status_code == 429 and row.attempts < 3 else "failed"
                row.error = f"Provider HTTP {e.response.status_code}"
                row.next_attempt_at = now() + timedelta(minutes=2**row.attempts)
            except (httpx.TransportError, KeyError):
                row.state = "unknown"
                row.error = "Delivery outcome unknown; inspect provider before retrying"
            emit(
                db,
                row.organization_id,
                "notification",
                row.id,
                "notification." + row.state,
                {"channel": "email", "provider_id": row.provider_id, "error": row.error},
            )
