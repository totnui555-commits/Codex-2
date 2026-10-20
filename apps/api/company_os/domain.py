import hashlib
import json
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select

from .models import (
    Approval,
    Audit,
    Delivery,
    Event,
    Message,
    Organization,
    Outbox,
    Project,
    Reservation,
    Task,
    TaskDependency,
    Usage,
    now,
)
from .security import redact

TERMINAL = {"completed", "failed", "cancelled", "quarantined"}
TRANSITIONS = {
    "proposed": {"ready", "cancelled"},
    "ready": {"scheduled", "blocked", "cancelled", "quarantined"},
    "scheduled": {"running", "blocked", "cancelled", "quarantined"},
    "running": {"reviewing", "blocked", "waiting_for_approval", "failed", "cancelled", "quarantined"},
    "blocked": {"ready", "cancelled", "quarantined"},
    "reviewing": {"completed", "failed", "quarantined", "waiting_for_approval", "cancelled"},
    "waiting_for_approval": {"ready", "completed", "cancelled", "quarantined"},
    "failed": {"ready", "cancelled"},
    "completed": set(),
    "cancelled": set(),
    "quarantined": set(),
}


def scoped(db, model, id, org):
    obj = db.scalar(select(model).where(model.id == id, model.organization_id == org))
    if not obj:
        raise HTTPException(404, "Resource not found")
    return obj


def lock_org(db, id):
    return db.scalar(select(Organization).where(Organization.id == id).with_for_update())


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def emit(db, org, aggregate_type, aggregate_id, event_type, payload, actor="system", correlation=None):
    organization = lock_org(db, org)
    db.flush()
    payload = redact(payload)
    seq = (
        db.scalar(
            select(func.max(Event.aggregate_sequence)).where(
                Event.organization_id == org,
                Event.aggregate_type == aggregate_type,
                Event.aggregate_id == aggregate_id,
            )
        )
        or 0
    ) + 1
    cursor = db.scalar(select(func.nextval("event_cursor_seq")))
    event = Event(
        organization_id=org,
        cursor=cursor,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        aggregate_sequence=seq,
        event_type=event_type,
        actor_type="user" if actor != "system" else "service",
        actor_id=actor,
        correlation_id=correlation or aggregate_id,
        payload=payload,
    )
    db.add(event)
    db.flush()
    db.add(Outbox(organization_id=org, event_id=event.id))
    audit_seq = (db.scalar(select(func.max(Audit.sequence)).where(Audit.organization_id == org)) or 0) + 1
    content = {
        "organization_id": org,
        "sequence": audit_seq,
        "actor_id": actor,
        "action": event_type,
        "payload": payload,
        "previous_hash": organization.audit_head,
    }
    digest = hashlib.sha256(canonical(content).encode()).hexdigest()
    db.add(Audit(**content, record_hash=digest))
    organization.audit_head = digest
    return event


def verify_audit(db, org):
    previous = "0" * 64
    rows = db.scalars(select(Audit).where(Audit.organization_id == org).order_by(Audit.sequence)).all()
    for sequence, row in enumerate(rows, 1):
        content = {
            k: getattr(row, k)
            for k in ["organization_id", "sequence", "actor_id", "action", "payload", "previous_hash"]
        }
        if (
            row.sequence != sequence
            or row.previous_hash != previous
            or hashlib.sha256(canonical(content).encode()).hexdigest() != row.record_hash
        ):
            return False
        previous = row.record_hash
    return previous == db.get(Organization, org).audit_head


def add_dependency(db, task, dependency_id):
    lock_org(db, task.organization_id)
    dep = scoped(db, Task, dependency_id, task.organization_id)
    if task.project_id != dep.project_id:
        raise HTTPException(422, "Dependencies must be in the same project")
    edges = db.scalars(
        select(TaskDependency).where(TaskDependency.organization_id == task.organization_id)
    ).all()
    graph = {}
    for e in edges:
        graph.setdefault(e.task_id, []).append(e.depends_on_id)
    graph.setdefault(task.id, []).append(dep.id)
    seen = set()

    def visit(node):
        if node == task.id:
            raise HTTPException(409, "Dependency cycle")
        if node in seen:
            return
        seen.add(node)
        for n in graph.get(node, []):
            visit(n)

    visit(dep.id)
    db.add(TaskDependency(organization_id=task.organization_id, task_id=task.id, depends_on_id=dep.id))
    emit(db, task.organization_id, "task", task.id, "task.dependency_added", {"depends_on": dep.id})


def dependencies_complete(db, task):
    deps = db.scalars(select(TaskDependency.depends_on_id).where(TaskDependency.task_id == task.id)).all()
    return not deps or not db.scalar(
        select(func.count()).select_from(Task).where(Task.id.in_(deps), Task.status != "completed")
    )


def transition(db, task, status, actor="system"):
    lock_org(db, task.organization_id)
    if status not in TRANSITIONS.get(task.status, set()):
        raise HTTPException(409, f"Invalid transition: {task.status} -> {status}")
    if status in {"scheduled", "running"}:
        org = db.get(Organization, task.organization_id)
        project = db.get(Project, task.project_id)
        if org.stopped or project.paused:
            raise HTTPException(409, "Company or project is paused")
        if not dependencies_complete(db, task):
            raise HTTPException(409, "Dependencies are incomplete")
    old = task.status
    task.status = status
    emit(
        db,
        task.organization_id,
        "task",
        task.id,
        "task.status_changed",
        {"before": old, "status": status},
        actor,
    )


def reserve(db, task, run_id, amount):
    amount = Decimal(str(amount))
    org = lock_org(db, task.organization_id)
    existing = db.scalar(select(Reservation).where(Reservation.run_id == run_id))
    if existing:
        if existing.task_id != task.id or existing.amount != amount:
            raise HTTPException(409, "Idempotency key mismatch")
        return existing
    if org.stopped or db.get(Project, task.project_id).paused:
        raise HTTPException(409, "Execution paused")
    if not org.paid_execution_authorized:
        raise HTTPException(403, "Paid execution has not been authorized")
    if amount <= 0 or amount > 30 or amount > task.budget_limit:
        raise HTTPException(422, "Run/task budget exceeded")
    period = now().strftime("%Y-%m")
    reservations = db.scalars(select(Reservation).where(Reservation.organization_id == org.id)).all()

    def committed(r):
        return r.amount if r.state == "reserved" else (r.actual or Decimal(0))

    monthly = sum((committed(r) for r in reservations if r.period == period), Decimal(0))
    if monthly + amount > org.monthly_limit:
        raise HTTPException(409, "Monthly budget exhausted")
    project_task_ids = set(db.scalars(select(Task.id).where(Task.project_id == task.project_id)).all())
    if (
        sum((committed(r) for r in reservations if r.task_id in project_task_ids), Decimal(0)) + amount
        > db.get(Project, task.project_id).budget_limit
    ):
        raise HTTPException(409, "Project budget exhausted")
    if (
        sum((committed(r) for r in reservations if r.task_id == task.id), Decimal(0)) + amount
        > task.budget_limit
    ):
        raise HTTPException(409, "Task budget exhausted")
    if sum(r.state == "reserved" for r in reservations) >= org.max_paid_concurrency:
        raise HTTPException(409, "Paid concurrency limit reached")
    row = Reservation(organization_id=org.id, task_id=task.id, run_id=run_id, amount=amount, period=period)
    db.add(row)
    db.flush()
    for threshold in [50, 80, 95]:
        if org.monthly_limit and (monthly + amount) / org.monthly_limit * 100 >= threshold:
            inbox(
                db,
                org.id,
                f"Budget alert: {threshold}% committed",
                "Monthly spend plus reservations reached the configured threshold.",
                dedupe=f"budget:{period}:{threshold}",
            )
    emit(db, org.id, "budget", row.id, "budget.reserved", {"amount": str(amount), "task_id": task.id})
    return row


def reconcile(db, reservation, actual, provider, telemetry, estimated=True):
    lock_org(db, reservation.organization_id)
    actual = Decimal(str(actual))
    if reservation.state != "reserved":
        return reservation
    if actual < 0:
        raise HTTPException(422, "Invalid usage")
    reservation.actual, reservation.state, reservation.telemetry = actual, "settled", redact(telemetry)
    db.add(
        Usage(
            organization_id=reservation.organization_id,
            reservation_id=reservation.id,
            amount=actual,
            provider=provider,
            estimated=estimated,
            details=redact(telemetry),
        )
    )
    if actual > reservation.amount:
        db.get(Organization, reservation.organization_id).stopped = True
        inbox(
            db,
            reservation.organization_id,
            "Budget overrun — company paused",
            "Provider usage exceeded its reservation. Review the usage ledger before resuming.",
            "critical",
            f"overrun:{reservation.id}",
        )
    emit(
        db,
        reservation.organization_id,
        "budget",
        reservation.id,
        "budget.reconciled",
        {"actual": str(actual), "estimated": estimated},
    )
    return reservation


PROTECTED = {
    "production_release",
    "public_launch",
    "external_outreach",
    "payment_setup",
    "vendor_purchase",
    "paid_advertising",
    "delete_data",
    "policy_change",
}


def authorize(db, org_id, action, artifact_sha, target, approval_id=None, exposure=0):
    org = lock_org(db, org_id)
    if org.stopped:
        raise HTTPException(409, "STOP ALL is active")
    if action == "sandbox_build" and org.mode == "research_only":
        raise HTTPException(403, "Build autopilot is disabled")
    if action in PROTECTED:
        if not approval_id:
            raise HTTPException(403, "Authenticated owner approval required")
        a = scoped(db, Approval, approval_id, org_id)
        if (
            a.state != "approved"
            or a.expires_at <= now()
            or a.consumed_at
            or a.action != action
            or a.artifact_sha256 != artifact_sha
            or a.target != target
            or a.max_exposure < Decimal(str(exposure))
        ):
            raise HTTPException(403, "Approval expired, consumed, changed or out of scope")
        a.consumed_at = now()
        emit(
            db,
            org_id,
            "approval",
            a.id,
            "approval.consumed",
            {"action": action, "artifact_sha256": artifact_sha},
        )
    return True


def inbox(db, org, subject, body, priority="action_required", dedupe=None, options=None):
    if dedupe:
        existing = db.scalar(select(Message).where(Message.dedupe_key == f"{org}:{dedupe}"))
        if existing:
            return existing
    row = Message(
        organization_id=org,
        subject=subject,
        body=body,
        priority=priority,
        dedupe_key=f"{org}:{dedupe}" if dedupe else None,
        options=options or [],
    )
    db.add(row)
    db.flush()
    db.add(Delivery(organization_id=org, message_id=row.id))
    emit(db, org, "message", row.id, "inbox.created", {"subject": subject, "priority": priority})
    return row
