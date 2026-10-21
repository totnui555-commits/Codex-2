import asyncio
import hmac
import json
import time
from collections import defaultdict, deque
from datetime import timedelta
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from sqlalchemy import func, select, text

from .contracts import (
    ApprovalCreate,
    ApprovalDecision,
    Bootstrap,
    CompanyPolicy,
    Credentials,
    InboxResponse,
    ProjectCreate,
    ProjectUpdate,
    TaskCreate,
)
from .db import Session, get_db
from .domain import PROTECTED, add_dependency, emit, inbox, lock_org, scoped, transition, verify_audit
from .experiments import router as experiments_router
from .gateway import router as gateway_router
from .models import (
    AgentRole,
    AgentRun,
    Approval,
    Artifact,
    Audit,
    Decisions,
    Delivery,
    Event,
    Experiments,
    Incident,
    Membership,
    Message,
    Opportunity,
    Organization,
    Products,
    Project,
    Reservation,
    Revenue,
    Task,
    TaskDependency,
    Usage,
    User,
    now,
)
from .products import router as products_router
from .security import current_user, dummy_password_hash, owner, passwords, redact, session_token, tenant
from .settings import settings

app = FastAPI(title="AI COMPANY OS", version="0.1.0")
REQUESTS = Counter("company_api_requests_total", "API request counts", ["method", "status"])
login_attempts = defaultdict(deque)


def record(row):
    value = jsonable_encoder({c.name: getattr(row, c.name) for c in row.__table__.columns})
    if isinstance(row, Event):
        value.update(event_id=row.id, occurred_at=row.created_at.isoformat())
    return value


def records(rows):
    return [record(row) for row in rows]


@app.middleware("http")
async def security_headers(request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and origin != settings().app_origin:
            return Response("Origin denied", status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return Response("Cross-site request denied", status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    # Compressing an SSE response can buffer small events until the proxy closes
    # the stream, leaving a connected client displaying stale operational state.
    event_stream = response.headers.get("content-type", "").startswith("text/event-stream")
    response.headers["Cache-Control"] = "no-store, no-transform" if event_stream else "no-store"
    REQUESTS.labels(request.method, str(response.status_code)).inc()
    return response


@app.get("/health")
def health(db=Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgresql", "version": "0.1.0"}


@app.get("/metrics")
def metrics(_=Depends(owner)):
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def throttle(request):
    key = request.client.host if request.client else "unknown"
    q = login_attempts[key]
    while q and q[0] < time.monotonic() - 60:
        q.popleft()
    if len(q) >= 10:
        raise HTTPException(429, "Too many authentication attempts")
    q.append(time.monotonic())


def set_session(response, user):
    response.set_cookie(
        "company_session",
        session_token(user),
        httponly=True,
        secure=settings().secure_cookies,
        samesite="strict",
        max_age=8 * 3600,
        path="/",
    )


@app.post("/auth/bootstrap", status_code=201)
def bootstrap(data: Bootstrap, request: Request, response: Response, db=Depends(get_db)):
    throttle(request)
    if not settings().bootstrap_token or not hmac.compare_digest(
        data.bootstrap_token, settings().bootstrap_token
    ):
        raise HTTPException(403, "Invalid setup token")
    db.execute(text("SELECT pg_advisory_xact_lock(930210)"))
    if db.scalar(select(func.count()).select_from(User)):
        raise HTTPException(409, "Installation already initialized")
    from .models import uid

    org = Organization(id=uid(), name=data.organization_name)
    db.execute(text("SELECT set_config('app.organization_id', :id, true)"), {"id": org.id})
    user = User(id=uid(), email=data.email.lower(), password_hash=passwords.hash(data.password))
    db.execute(text("SELECT set_config('app.user_id', :id, true)"), {"id": user.id})
    db.add_all([org, user])
    db.flush()
    db.add(Membership(organization_id=org.id, user_id=user.id, role="owner"))
    emit(db, org.id, "organization", org.id, "organization.created", {"name": org.name}, user.id)
    inbox(
        db,
        org.id,
        "Connect providers to activate the workforce",
        "Add model credentials and an authorized budget, a Daytona hardened snapshot, GitHub App credentials, private S3 storage and Gmail OAuth through secure deployment configuration. Research and coding remain blocked until configured. The chat Gmail connection does not provision application OAuth.",
        dedupe="provider-setup-v1",
        options=[
            "Configure secure provider settings",
            "Continue with management and public source research",
            "Review deployment guide",
        ],
    )
    set_session(response, user)
    return {"user": {"id": user.id, "email": user.email}, "organization": record(org)}


@app.post("/auth/login")
def login(data: Credentials, request: Request, response: Response, db=Depends(get_db)):
    throttle(request)
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    # Perform Argon2 even for unknown accounts to limit timing-based enumeration.
    target = user.password_hash if user else dummy_password_hash
    valid = passwords.verify(data.password, target)
    if not user or not valid:
        raise HTTPException(401, "Invalid email or password")
    set_session(response, user)
    return {"id": user.id, "email": user.email}


@app.post("/auth/logout")
def logout(response: Response, user=Depends(current_user), db=Depends(get_db)):
    user.session_version += 1
    response.delete_cookie("company_session", path="/")
    return {"logged_out": True}


@app.get("/auth/me")
def me(user=Depends(current_user), db=Depends(get_db)):
    return {
        "id": user.id,
        "email": user.email,
        "memberships": records(db.scalars(select(Membership).where(Membership.user_id == user.id)).all()),
    }


@app.get("/snapshot")
def snapshot(m=Depends(tenant), db=Depends(get_db)):
    org = lock_org(db, m.organization_id)

    def rows(model, limit=200):
        return records(
            db.scalars(
                select(model)
                .where(model.organization_id == org.id)
                .order_by(model.created_at.desc())
                .limit(limit)
            ).all()
        )

    tasks, runs, usage = rows(Task), rows(AgentRun), rows(Usage, 1000)
    period = now().strftime("%Y-%m")
    all_reservations = db.scalars(
        select(Reservation).where(Reservation.organization_id == org.id, Reservation.period == period)
    ).all()
    spend = sum((r.actual or Decimal(0) for r in all_reservations if r.state == "settled"), Decimal(0))
    reserved = sum((r.amount for r in all_reservations if r.state == "reserved"), Decimal(0))
    from datetime import datetime

    heartbeats = db.scalars(select(Decisions).where(Decisions.organization_id == org.id)).all()
    services = {
        h.data["service"]: {
            "last_seen_at": h.data["last_seen_at"],
            "state": "live"
            if (now() - datetime.fromisoformat(h.data["last_seen_at"])).total_seconds() < 60
            else "stale",
        }
        for h in heartbeats
        if "service" in h.data
    }
    return {
        "services": services,
        "deployment": {"runtime": settings().runtime},
        "organization": record(org),
        "projects": rows(Project),
        "tasks": tasks,
        "dependencies": rows(TaskDependency),
        "roles": records(db.scalars(select(AgentRole)).all()),
        "runs": runs,
        "artifacts": rows(Artifact),
        "approvals": rows(Approval),
        "messages": rows(Message),
        "deliveries": rows(Delivery),
        "opportunities": rows(Opportunity),
        "experiments": rows(Experiments),
        "products": rows(Products),
        "revenue": rows(Revenue),
        "usage": usage,
        "incidents": rows(Incident),
        "events": rows(Event, 40),
        "cursor": db.scalar(select(func.max(Event.cursor)).where(Event.organization_id == org.id)) or 0,
        "kpis": {
            "active_agents": len({r["agent_role"] for r in runs if r["status"] == "running"}),
            "jobs_running": sum(t["status"] == "running" for t in tasks),
            "jobs_waiting": sum(t["status"] in ["blocked", "waiting_for_approval", "ready"] for t in tasks),
            "approvals_needed": sum(a["state"] == "pending" for a in rows(Approval)),
            "monthly_spend": str(spend),
            "reserved": str(reserved),
            "available_budget": str(org.monthly_limit - spend - reserved),
            "currency": org.currency,
        },
        "integrations": provider_status(),
    }


@app.get("/integrations")
def integrations(_=Depends(owner)):
    return provider_status()


def provider_status():
    from .providers import artifact_storage_configured

    s = settings()
    return {
        "model": "configured"
        if (
            s.openrouter_api_key
            if s.model_provider == "openrouter"
            else s.openai_api_key
            if s.model_provider == "openai"
            else ""
        )
        else "disconnected",
        "sandbox": "configured" if s.daytona_api_key and s.daytona_snapshot else "disconnected",
        "github": "configured" if s.github_token and s.github_repository else "disconnected",
        "artifacts": "configured" if artifact_storage_configured() else "disconnected",
        "email": "configured"
        if s.email_send_authorized and (s.gmail_access_token or s.gmail_refresh_token)
        else "disconnected",
        "billing": "configured" if s.stripe_webhook_secret else "disconnected",
    }


@app.post("/projects", status_code=201)
def create_project(data: ProjectCreate, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    row = Project(organization_id=m.organization_id, **data.model_dump())
    db.add(row)
    db.flush()
    emit(db, m.organization_id, "project", row.id, "project.created", {"name": row.name}, user.id)
    return record(row)


@app.patch("/projects/{id}")
def update_project(
    id: str, data: ProjectUpdate, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)
):
    lock_org(db, m.organization_id)
    row = scoped(db, Project, id, m.organization_id)
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(row, k, v)
    emit(db, m.organization_id, "project", id, "project.updated", data.model_dump(exclude_none=True), user.id)
    return record(row)


@app.post("/tasks", status_code=201)
def create_task(data: TaskCreate, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    scoped(db, Project, data.project_id, m.organization_id)
    if not db.scalar(select(AgentRole).where(AgentRole.key == data.agent_role)):
        raise HTTPException(422, "Unknown agent role")
    row = Task(organization_id=m.organization_id, **data.model_dump(exclude={"dependencies"}))
    db.add(row)
    db.flush()
    for dependency in data.dependencies:
        add_dependency(db, row, dependency)
    emit(
        db,
        m.organization_id,
        "task",
        row.id,
        "task.created",
        {"title": row.title, "agent_role": row.agent_role},
        user.id,
    )
    return record(row)


@app.post("/tasks/{id}/dependencies/{dependency_id}")
def dependency(id: str, dependency_id: str, m=Depends(owner), db=Depends(get_db)):
    task = scoped(db, Task, id, m.organization_id)
    if task.status not in {"proposed", "ready", "blocked"}:
        raise HTTPException(409, "Cannot change an executing task DAG")
    add_dependency(db, task, dependency_id)
    return {"added": True}


@app.post("/tasks/{id}/cancel")
def cancel(id: str, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    task = scoped(db, Task, id, m.organization_id)
    transition(db, task, "cancelled", user.id)
    return record(task)


@app.post("/tasks/{id}/retry")
def retry(id: str, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    task = scoped(db, Task, id, m.organization_id)
    if task.attempts >= task.max_attempts:
        raise HTTPException(409, "Retry ceiling reached")
    transition(db, task, "ready", user.id)
    task.error = None
    return record(task)


@app.post("/company/stop")
def stop(m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    org = lock_org(db, m.organization_id)
    org.stopped = True
    for task in db.scalars(
        select(Task).where(
            Task.organization_id == org.id, Task.status.in_(["ready", "scheduled", "running", "reviewing"])
        )
    ).all():
        transition(db, task, "quarantined", user.id)
    emit(db, org.id, "organization", org.id, "company.stopped", {"reason": "Founder STOP ALL"}, user.id)
    return {
        "stopped": True,
        "note": "Execution gates closed; Watchtower will reclaim active sandboxes. Remote stop outcomes are recorded separately.",
    }


@app.post("/company/resume")
def resume(m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    org = lock_org(db, m.organization_id)
    org.stopped = False
    emit(db, org.id, "organization", org.id, "company.resumed", {}, user.id)
    return {"stopped": False}


@app.put("/company/policy")
def policy(data: CompanyPolicy, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    org = lock_org(db, m.organization_id)
    for k, v in data.model_dump().items():
        setattr(org, k, v)
    emit(db, org.id, "organization", org.id, "company.policy_changed", data.model_dump(), user.id)
    return record(org)


@app.post("/approvals", status_code=201)
def request_approval(data: ApprovalCreate, m=Depends(owner), db=Depends(get_db)):
    if data.action not in PROTECTED:
        raise HTTPException(422, "Unknown protected action")
    if data.task_id:
        scoped(db, Task, data.task_id, m.organization_id)
    row = Approval(
        organization_id=m.organization_id,
        expires_at=now() + timedelta(hours=data.expires_hours),
        **data.model_dump(exclude={"expires_hours"}),
    )
    db.add(row)
    db.flush()
    emit(
        db,
        m.organization_id,
        "approval",
        row.id,
        "approval.requested",
        {"action": row.action, "artifact_sha256": row.artifact_sha256, "target": row.target},
    )
    inbox(
        db,
        m.organization_id,
        f"Approve {row.action}",
        f"Target: {row.target}. Artifact: {row.artifact_sha256}. Maximum exposure: {row.max_exposure}. Authenticate in the approval center to decide.",
        dedupe=f"approval:{row.id}",
    )
    return record(row)


@app.post("/approvals/{id}/decide")
def decide(id: str, data: ApprovalDecision, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    lock_org(db, m.organization_id)
    row = scoped(db, Approval, id, m.organization_id)
    if row.state != "pending" or row.expires_at <= now():
        raise HTTPException(409, "Approval no longer pending")
    if row.artifact_sha256 != data.artifact_sha256:
        raise HTTPException(409, "Artifact changed")
    row.state = data.decision
    row.decided_by = user.id
    row.decided_at = now()
    emit(
        db,
        m.organization_id,
        "approval",
        id,
        "approval.decided",
        {"decision": data.decision, "artifact_sha256": row.artifact_sha256},
        user.id,
    )
    return record(row)


@app.post("/inbox/{id}/respond")
def respond(id: str, data: InboxResponse, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    row = scoped(db, Message, id, m.organization_id)
    row.response = data.response
    row.state = "answered"
    row.responded_by = user.id
    emit(db, m.organization_id, "message", id, "inbox.responded", {"response": data.response}, user.id)
    return record(row)


@app.post("/opportunities/{id}/incubate")
def incubate(id: str, m=Depends(owner), db=Depends(get_db)):
    lock_org(db, m.organization_id)
    row = scoped(db, Opportunity, id, m.organization_id)
    if row.project_id:
        return record(db.get(Project, row.project_id))
    project = Project(organization_id=m.organization_id, name=row.title, description=row.hypothesis)
    db.add(project)
    db.flush()
    task = Task(
        organization_id=m.organization_id,
        project_id=project.id,
        title="Validate customer pain and MVP scope",
        objective=row.hypothesis,
        agent_role="business_analyst",
        acceptance=["Cite primary sources", "Define a measurable experiment"],
        expected_artifacts=["opportunity_memo"],
    )
    db.add(task)
    db.flush()
    row.project_id = project.id
    row.status = "incubating"
    emit(
        db,
        m.organization_id,
        "opportunity",
        id,
        "opportunity.incubated",
        {"project_id": project.id, "task_id": task.id},
    )
    return record(project)


@app.get("/audit/verify")
def audit_verify(m=Depends(owner), db=Depends(get_db)):
    lock_org(db, m.organization_id)
    return {
        "valid": verify_audit(db, m.organization_id),
        "records": db.scalar(
            select(func.count()).select_from(Audit).where(Audit.organization_id == m.organization_id)
        ),
    }


@app.get("/audit")
def audit(m=Depends(owner), db=Depends(get_db)):
    return records(
        db.scalars(
            select(Audit)
            .where(Audit.organization_id == m.organization_id)
            .order_by(Audit.sequence.desc())
            .limit(200)
        ).all()
    )


@app.get("/events")
async def stream(
    request: Request, after: int = 0, m=Depends(tenant), user=Depends(current_user), db=Depends(get_db)
):
    try:
        cursor = max(after, int(request.headers.get("last-event-id", "0")))
    except ValueError:
        raise HTTPException(422, "Invalid event cursor")
    org = m.organization_id
    session_user_id, session_version = user.id, user.session_version
    db.commit()
    db.close()
    connection_started = time.monotonic()

    async def events():
        nonlocal cursor
        while not await request.is_disconnected() and time.monotonic() - connection_started < 300:
            with Session() as db:
                db.execute(text("SELECT set_config('app.organization_id', :id, true)"), {"id": org})
                check_user = db.get(User, session_user_id)
                if not check_user or check_user.session_version != session_version:
                    return
                rows = db.scalars(
                    select(Event)
                    .where(Event.organization_id == org, Event.cursor > cursor)
                    .order_by(Event.cursor)
                    .limit(100)
                ).all()
                for event in rows:
                    cursor = event.cursor
                    yield f"id: {cursor}\nevent: company\ndata: {json.dumps(record(event))}\n\n"
            if not rows:
                yield ": heartbeat\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})


@app.post("/webhooks/stripe/{organization_id}")
async def stripe(organization_id: str, request: Request, db=Depends(get_db)):
    from .revenue import ingest_stripe

    return ingest_stripe(
        db, organization_id, await request.body(), request.headers.get("stripe-signature", "")
    )


if settings().telemetry_enabled:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)


app.include_router(gateway_router)
app.include_router(experiments_router)
app.include_router(products_router)


@app.get("/events/history")
def event_history(after: int = 0, limit: int = 100, m=Depends(tenant), db=Depends(get_db)):
    return records(
        db.scalars(
            select(Event)
            .where(Event.organization_id == m.organization_id, Event.cursor > after)
            .order_by(Event.cursor)
            .limit(max(1, min(200, limit)))
        ).all()
    )


@app.get("/artifacts/{id}/content")
def artifact_content(id: str, m=Depends(owner), db=Depends(get_db)):

    from .providers import ArtifactStore

    artifact = scoped(db, Artifact, id, m.organization_id)
    body = ArtifactStore().read(artifact.uri, artifact.sha256)
    return {"artifact": record(artifact), "content": redact(json.loads(body))}


@app.post("/tasks/{id}/accept-artifact/{artifact_id}")
def accept_artifact(
    id: str, artifact_id: str, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)
):
    lock_org(db, m.organization_id)
    task = scoped(db, Task, id, m.organization_id)
    artifact = scoped(db, Artifact, artifact_id, m.organization_id)
    if task.status != "waiting_for_approval" or artifact.task_id != task.id or not artifact.verified:
        raise HTTPException(409, "No verified artifact awaiting review")
    task.checkpoint = {
        **task.checkpoint,
        "accepted_artifact_id": artifact.id,
        "accepted_sha256": artifact.sha256,
    }
    emit(
        db,
        m.organization_id,
        "task",
        task.id,
        "task.artifact_accepted",
        {"artifact_id": artifact.id, "sha256": artifact.sha256},
        user.id,
    )
    transition(db, task, "completed", user.id)
    return record(task)
