"""Tenant-owned product hypotheses and traceable prototype evidence; no implied publication."""

import json
import math
import re
from typing import Annotated
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy import select, text

from .contracts import Strict
from .db import get_db
from .domain import emit, lock_org, scoped
from .experiments import Revision, revision, serialize
from .models import AgentRun, Artifact, Experiments, Products, Project, Task
from .providers import ArtifactStore, GitHubProvider, IntegrationBlocked
from .security import current_user, owner
from .settings import settings

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(Strict):
    project_id: str
    name: str = Field(min_length=3, max_length=160)
    problem: str = Field(min_length=10, max_length=5000)
    target_customer: str = Field(min_length=3, max_length=500)
    mvp_scope: list[Annotated[str, Field(min_length=3, max_length=1000)]] = Field(min_length=1, max_length=20)
    currency: str = Field(default="THB", pattern=r"^(THB|USD)$")
    proposed_price_minor: int | None = Field(default=None, ge=0, le=100000000, strict=True)
    estimated_variable_cost_minor: int | None = Field(default=None, ge=0, le=100000000, strict=True)
    estimated_monthly_fixed_cost_minor: int | None = Field(default=None, ge=0, le=100000000, strict=True)


class ExperimentLink(Revision):
    experiment_id: str


class PrototypeLink(Revision):
    artifact_id: str


def economics(data):
    price = data.get("proposed_price_minor")
    variable = data.get("estimated_variable_cost_minor")
    fixed = data.get("estimated_monthly_fixed_cost_minor")
    contribution = price - variable if price is not None and variable is not None else None
    return {
        "classification": "owner_supplied_estimate_not_revenue_or_profit",
        "unit_contribution_minor": contribution,
        "break_even_customers": math.ceil(fixed / contribution)
        if fixed is not None and contribution is not None and contribution > 0
        else None,
        "costs_complete": False,
        "currency": data["currency"],
    }


@router.post("", status_code=201)
def create(data: ProductCreate, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    lock_org(db, m.organization_id)
    scoped(db, Project, data.project_id, m.organization_id)
    payload = data.model_dump()
    payload.update(
        state="draft", published=False, prototype=None, experiment_id=None, economics=economics(payload)
    )
    row = Products(organization_id=m.organization_id, data=payload)
    db.add(row)
    db.flush()
    emit(db, m.organization_id, "product", row.id, "product.created", payload, user.id)
    return serialize(row)


def editable(db, id, m, expected):
    lock_org(db, m.organization_id)
    row = scoped(db, Products, id, m.organization_id)
    revision(row, expected)
    if row.data["state"] == "archived":
        raise HTTPException(409, "Archived products are frozen")
    return row


@router.post("/{id}/experiment")
def link_experiment(
    id: str, data: ExperimentLink, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)
):
    row = editable(db, id, m, data.expected_version)
    experiment = scoped(db, Experiments, data.experiment_id, m.organization_id)
    if experiment.data["project_id"] != row.data["project_id"]:
        raise HTTPException(422, "Experiment must belong to this product project")
    row.data = {**row.data, "experiment_id": experiment.id}
    row.version += 1
    emit(
        db,
        m.organization_id,
        "product",
        id,
        "product.experiment_linked",
        {"experiment_id": experiment.id},
        user.id,
    )
    return serialize(row)


@router.post("/{id}/prototype")
def link_prototype(
    id: str, data: PrototypeLink, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)
):
    row = editable(db, id, m, data.expected_version)
    artifact = scoped(db, Artifact, data.artifact_id, m.organization_id)
    task = scoped(db, Task, artifact.task_id, m.organization_id)
    run = db.scalar(
        select(AgentRun).where(
            AgentRun.task_id == task.id,
            AgentRun.organization_id == m.organization_id,
            AgentRun.status == "completed",
            AgentRun.provider == "daytona/codex",
        )
    )
    if (
        not artifact.verified
        or artifact.kind != "verified_pull_request"
        or task.status != "completed"
        or task.project_id != row.data["project_id"]
        or not run
        or artifact.details.get("verification") != "independent_hosted_QA"
    ):
        raise HTTPException(
            422, "A completed same-project coding run with independently checked PR evidence is required"
        )
    try:
        proof = json.loads(ArtifactStore().read(artifact.uri, artifact.sha256))
        qa, export, pr = proof["qa"], proof["export"], proof["pr"]
        if (
            type(qa.get("exit_code")) is not int
            or qa["exit_code"] != 0
            or not qa.get("trusted_test_suite")
            or not qa.get("sandbox_id")
            or not export.get("sandbox_id")
            or qa["sandbox_id"] == export.get("sandbox_id")
            or not re.fullmatch(r"[a-f0-9]{40}", pr.get("commit", ""))
        ):
            raise ValueError()
        parsed = urlsplit(pr["url"])
        expected = "/" + settings().github_repository + "/pull/"
        if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment:
            raise ValueError()
        if not parsed.path.startswith(expected) or not re.fullmatch(r"[0-9]+", parsed.path[len(expected) :]):
            raise ValueError()
    except Exception:
        raise HTTPException(422, "Prototype evidence is missing, corrupt or has invalid provenance")
    # Release the organization lock during external provider I/O, then recheck revision.
    org_id, user_id = m.organization_id, user.id
    db.commit()
    try:
        actual = GitHubProvider().request("GET", "/pulls/" + parsed.path[len(expected) :])
    except (httpx.HTTPError, IntegrationBlocked):
        raise HTTPException(503, "GitHub verification is unavailable; prototype not attached")
    db.expire_all()
    db.execute(text("SELECT set_config('app.organization_id', :id, true)"), {"id": org_id})
    db.execute(text("SELECT set_config('app.user_id', :id, true)"), {"id": user_id})
    row = editable(db, id, m, data.expected_version)
    if (
        actual.get("head", {}).get("sha") != pr["commit"]
        or actual.get("base", {}).get("repo", {}).get("full_name") != settings().github_repository
    ):
        raise HTTPException(409, "Current GitHub PR does not match the checked commit/repository")
    row.data = {
        **row.data,
        "state": "prototype_evidence_attached",
        "prototype": {
            "artifact_id": artifact.id,
            "sha256": artifact.sha256,
            "pr_url": pr["url"],
            "commit": pr["commit"],
            "run_id": run.id,
            "qa_sandbox_id": qa["sandbox_id"],
            "build_sandbox_id": export["sandbox_id"],
        },
    }
    row.version += 1
    emit(db, m.organization_id, "product", id, "product.prototype_attached", row.data["prototype"], user.id)
    return serialize(row)


@router.post("/{id}/archive")
def archive(id: str, data: Revision, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    row = editable(db, id, m, data.expected_version)
    row.data = {**row.data, "state": "archived"}
    row.version += 1
    emit(db, m.organization_id, "product", id, "product.archived", {"version": row.version}, user.id)
    return serialize(row)


@router.get("/{id}/readiness")
def readiness(id: str, m=Depends(owner), db=Depends(get_db)):
    row = scoped(db, Products, id, m.organization_id)
    blockers = []
    prototype = row.data.get("prototype")
    if not prototype:
        blockers.append("No independently checked coding prototype attached")
    else:
        artifact = scoped(db, Artifact, prototype["artifact_id"], m.organization_id)
        if not artifact.verified or artifact.sha256 != prototype["sha256"]:
            blockers.append("Prototype integrity needs re-verification")
    experiment = None
    if row.data.get("experiment_id"):
        experiment = scoped(db, Experiments, row.data["experiment_id"], m.organization_id)
    if not experiment or experiment.data["state"] != "concluded":
        blockers.append("No concluded validation experiment")
    elif experiment.data["statistics"]["recommendation"] != "continue":
        blockers.append("Validation result does not recommend continuing")
    if row.data["state"] == "archived":
        blockers.append("Product archived")
    blockers.append("Independent release review, approved target and verified deployment are still required")
    return {
        "product_id": id,
        "published": False,
        "release_authorized": False,
        "blockers": blockers,
        "experiment": serialize(experiment) if experiment else None,
        "measurement_class": "owner_reported_not_verified_demand_or_revenue",
    }
