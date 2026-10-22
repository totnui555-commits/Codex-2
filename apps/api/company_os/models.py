from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uid():
    return str(uuid4())


def now():
    return datetime.now(UTC)


class Identity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Scoped(Identity):
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)


class Organization(Identity, Base):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(120))
    mode: Mapped[str] = mapped_column(String(30), default="research_only")
    stopped: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_execution_authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    max_paid_concurrency: Mapped[int] = mapped_column(Integer, default=2)
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=2000)
    currency: Mapped[str] = mapped_column(String(3), default="THB")
    audit_head: Mapped[str] = mapped_column(String(64), default="0" * 64)


class User(Identity, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    session_version: Mapped[int] = mapped_column(Integer, default=1)


class Membership(Scoped, Base):
    __tablename__ = "memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(30), default="owner")
    __table_args__ = (UniqueConstraint("organization_id", "user_id"),)


class Project(Scoped, Base):
    __tablename__ = "projects"
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    budget_limit: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=500)


class Task(Scoped, Base):
    __tablename__ = "tasks"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    objective: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="ready", index=True)
    agent_role: Mapped[str] = mapped_column(String(64), default="chief_of_staff")
    acceptance: Mapped[list] = mapped_column(JSON, default=list)
    expected_artifacts: Mapped[list] = mapped_column(JSON, default=list)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    budget_limit: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=100)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(64))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checkpoint: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    workflow_id: Mapped[str | None] = mapped_column(String(120), unique=True)


class TaskDependency(Scoped, Base):
    __tablename__ = "task_dependencies"
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    depends_on_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    __table_args__ = (UniqueConstraint("task_id", "depends_on_id"),)


class AgentRole(Identity, Base):
    __tablename__ = "agent_roles"
    key: Mapped[str] = mapped_column(String(64), unique=True)
    config: Mapped[dict] = mapped_column(JSON)


class AgentRun(Scoped, Base):
    __tablename__ = "agent_runs"
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    agent_role: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="scheduled")
    provider: Mapped[str] = mapped_column(String(40))
    provider_run_id: Mapped[str | None] = mapped_column(String(200))
    usage: Mapped[dict] = mapped_column(JSON, default=dict)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Artifact(Scoped, Base):
    __tablename__ = "artifacts"
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    kind: Mapped[str] = mapped_column(String(50))
    uri: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class Approval(Scoped, Base):
    __tablename__ = "approvals"
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    action: Mapped[str] = mapped_column(String(60))
    artifact_sha256: Mapped[str] = mapped_column(String(64))
    target: Mapped[str] = mapped_column(Text)
    max_exposure: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(String(30), default="pending")
    decided_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Reservation(Scoped, Base):
    __tablename__ = "budget_reservations"
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    run_id: Mapped[str] = mapped_column(String(36), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    actual: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    state: Mapped[str] = mapped_column(String(20), default="reserved")
    period: Mapped[str] = mapped_column(String(7))
    telemetry: Mapped[dict] = mapped_column(JSON, default=dict)


class Usage(Scoped, Base):
    __tablename__ = "usage_ledger"
    reservation_id: Mapped[str] = mapped_column(ForeignKey("budget_reservations.id"), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    currency: Mapped[str] = mapped_column(String(3), default="THB")
    provider: Mapped[str] = mapped_column(String(50))
    estimated: Mapped[bool] = mapped_column(Boolean, default=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class Opportunity(Scoped, Base):
    __tablename__ = "revenue_opportunities"
    title: Mapped[str] = mapped_column(String(200))
    hypothesis: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)
    dimensions: Mapped[dict] = mapped_column(JSON)
    uncertainties: Mapped[list] = mapped_column(JSON)
    evidence: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="researched")
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"))


class Revenue(Scoped, Base):
    __tablename__ = "revenue_transactions"
    provider: Mapped[str] = mapped_column(String(40))
    external_id: Mapped[str] = mapped_column(String(200), unique=True)
    kind: Mapped[str] = mapped_column(String(30))
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    verified: Mapped[bool] = mapped_column(Boolean, default=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class Message(Scoped, Base):
    __tablename__ = "messages"
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(30), default="action_required")
    state: Mapped[str] = mapped_column(String(30), default="open")
    options: Mapped[list] = mapped_column(JSON, default=list)
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    response: Mapped[str | None] = mapped_column(Text)
    responded_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    dedupe_key: Mapped[str | None] = mapped_column(String(200), unique=True)


class Delivery(Scoped, Base):
    __tablename__ = "notification_deliveries"
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"))
    channel: Mapped[str] = mapped_column(String(30), default="email")
    state: Mapped[str] = mapped_column(String(30), default="pending")
    provider_id: Mapped[str | None] = mapped_column(String(200))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    error: Mapped[str | None] = mapped_column(Text)


class Event(Scoped, Base):
    __tablename__ = "events"
    cursor: Mapped[int] = mapped_column(Integer, unique=True, autoincrement=True, nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(50))
    aggregate_id: Mapped[str] = mapped_column(String(36))
    aggregate_sequence: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(100))
    actor_type: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[str] = mapped_column(String(100))
    correlation_id: Mapped[str] = mapped_column(String(100))
    causation_id: Mapped[str | None] = mapped_column(String(36))
    payload: Mapped[dict] = mapped_column(JSON)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (
        UniqueConstraint("organization_id", "aggregate_type", "aggregate_id", "aggregate_sequence"),
    )


class Outbox(Scoped, Base):
    __tablename__ = "outbox"
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), unique=True)
    state: Mapped[str] = mapped_column(String(20), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Audit(Scoped, Base):
    __tablename__ = "audit_records"
    sequence: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON)
    previous_hash: Mapped[str] = mapped_column(String(64))
    record_hash: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint("organization_id", "sequence"),)


class Incident(Scoped, Base):
    __tablename__ = "incidents"
    severity: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(60))
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    details: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(20), default="open")
    dedupe_key: Mapped[str] = mapped_column(String(200), unique=True)


# Versioned, tenant-scoped document contracts for supporting entities.
# Core transactional entities above use dedicated typed columns.
for _name in [
    "project_specs",
    "agent_instances",
    "workflow_runs",
    "tool_calls",
    "sandboxes",
    "artifact_versions",
    "approval_decisions",
    "policy_rules",
    "budget_limits",
    "research_evidence",
    "experiments",
    "products",
    "go_to_market_plans",
    "customer_metrics",
    "decisions",
    "price_tables",
    "fx_snapshots",
]:
    _class_name = "".join(x.title() for x in _name.split("_"))
    globals()[_class_name] = type(
        _class_name,
        (Scoped, Base),
        {
            "__tablename__": _name,
            "__annotations__": {"data": Mapped[dict], "version": Mapped[int]},
            "data": mapped_column(JSON, default=dict),
            "version": mapped_column(Integer, default=1),
        },
    )
