from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Credentials(Strict):
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=12, max_length=128)


class Bootstrap(Credentials):
    bootstrap_token: str
    organization_name: str = Field(min_length=2, max_length=120)


class ProjectCreate(Strict):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=10000)


class ProjectUpdate(Strict):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=10000)
    paused: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=100)


class TaskCreate(Strict):
    project_id: str
    title: str = Field(min_length=3, max_length=200)
    objective: str = Field(min_length=5, max_length=20000)
    acceptance: list[str] = Field(min_length=1, max_length=30)
    agent_role: str = "chief_of_staff"
    dependencies: list[str] = Field(default_factory=list, max_length=50)
    expected_artifacts: list[str] = Field(default_factory=list, max_length=20)


class ApprovalCreate(Strict):
    action: str
    artifact_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    target: str = Field(min_length=1, max_length=2000)
    task_id: str | None = None
    max_exposure: float = Field(default=0, ge=0, le=1000000)
    context: dict = Field(default_factory=dict)
    expires_hours: int = Field(default=24, ge=1, le=72)


class ApprovalDecision(Strict):
    decision: Literal["approved", "rejected", "changes_requested"]
    artifact_sha256: str = Field(pattern="^[a-f0-9]{64}$")


class CompanyPolicy(Strict):
    mode: Literal["research_only", "build_autopilot", "approved_growth"]
    paid_execution_authorized: bool
    monthly_limit: float = Field(ge=0, le=1000000)
    max_paid_concurrency: int = Field(ge=1, le=2)


class InboxResponse(Strict):
    response: str = Field(min_length=1, max_length=10000)


class GoalPlan(Strict):
    summary: str
    tasks: list[dict] = Field(max_length=12)


class ResearchMemo(Strict):
    title: str
    hypothesis: str
    dimensions: dict[str, int]
    uncertainties: list[str]
    evidence: list[dict]
    mvp_scope: list[str]
    experiment: str
