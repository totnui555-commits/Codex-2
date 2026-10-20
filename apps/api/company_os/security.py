import hashlib
import re
from datetime import timedelta

import jwt
from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy import select, text

from .db import get_db
from .models import Membership, User, now
from .settings import settings

passwords = PasswordHash.recommended()
dummy_password_hash = passwords.hash("unmatchable-account-dummy-passphrase")
SENSITIVE = re.compile(
    r"(api[_-]?key|password|secret|authorization|refresh[_-]?token|access[_-]?token)", re.IGNORECASE
)
TOKEN = re.compile(r"(sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|Bearer\s+\S+)")


def redact(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if SENSITIVE.search(k) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return TOKEN.sub("[REDACTED]", value)
    return value


def session_token(user):
    if len(settings().session_secret) < 32:
        raise HTTPException(503, "Configure SESSION_SECRET with at least 32 random characters")
    return jwt.encode(
        {
            "sub": user.id,
            "v": user.session_version,
            "exp": now() + timedelta(hours=8),
            "aud": "company-os",
            "iss": "company-os",
        },
        settings().session_secret,
        algorithm="HS256",
    )


def current_user(request: Request, db=Depends(get_db)):
    token = request.cookies.get("company_session")
    if not token:
        raise HTTPException(401, "Authentication required")
    try:
        claims = jwt.decode(
            token, settings().session_secret, algorithms=["HS256"], audience="company-os", issuer="company-os"
        )
        user = db.get(User, claims["sub"])
        if not user or user.session_version != claims["v"]:
            raise ValueError()
        db.execute(text("SELECT set_config('app.user_id', :id, true)"), {"id": user.id})
        return user
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Session expired or revoked")


def tenant(request: Request, user=Depends(current_user), db=Depends(get_db)):
    organization_id = request.headers.get("X-Organization-ID") or request.query_params.get("organization_id")
    memberships = db.scalars(select(Membership).where(Membership.user_id == user.id)).all()
    membership = (
        next((m for m in memberships if m.organization_id == organization_id), None)
        if organization_id
        else next(iter(memberships), None)
    )
    if not membership:
        raise HTTPException(403, "Organization access denied")
    db.execute(
        text("SELECT set_config('app.organization_id', :id, true)"), {"id": membership.organization_id}
    )
    return membership


def owner(membership=Depends(tenant)):
    if membership.role != "owner":
        raise HTTPException(403, "Owner action required")
    return membership


def fingerprint(text):
    return hashlib.sha256(text.encode()).hexdigest()
