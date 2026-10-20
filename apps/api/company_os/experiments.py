"""Owner-reported incubation evidence; never a verified revenue source."""

import hashlib
import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import Field, model_validator
from sqlalchemy import select

from .contracts import Strict
from .db import get_db
from .domain import emit, lock_org, scoped
from .models import Artifact, CustomerMetrics, Experiments, Project, now
from .security import current_user, owner

router = APIRouter(prefix="/experiments", tags=["incubation"])


class ExperimentCreate(Strict):
    project_id: str
    title: str = Field(min_length=3, max_length=200)
    hypothesis: str = Field(min_length=10, max_length=5000)
    metric: str = Field(min_length=3, max_length=120)
    minimum_samples: int = Field(ge=10, le=1000000, strict=True)
    continue_rate: float = Field(gt=0, lt=1)
    stop_rate: float = Field(ge=0, lt=1)

    @model_validator(mode="after")
    def ordered_thresholds(self):
        if self.stop_rate >= self.continue_rate:
            raise ValueError("Stop rate must be below continue rate")
        return self


class Revision(Strict):
    expected_version: int = Field(ge=1, strict=True)


class ExperimentAction(Revision):
    action: Literal["start", "pause", "conclude"]


class Observation(Revision):
    reference: str = Field(min_length=3, max_length=200, pattern=r".*\S.*")
    samples: int = Field(ge=1, le=1000000, strict=True)
    successes: int = Field(ge=0, le=1000000, strict=True)
    artifact_id: str
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def valid_counts(self):
        if self.successes > self.samples:
            raise ValueError("Successes cannot exceed samples")
        return self


def result(samples, successes, minimum, continue_rate, stop_rate):
    """Wilson 95% interval; uncertainty prevents premature recommendations."""
    if samples == 0:
        return {
            "samples": 0,
            "successes": 0,
            "rate": None,
            "interval_95": None,
            "recommendation": "inconclusive",
        }
    rate = successes / samples
    z2 = 1.959963984540054**2
    center = (rate + z2 / (2 * samples)) / (1 + z2 / samples)
    margin = math.sqrt(rate * (1 - rate) / samples + z2 / (4 * samples**2))
    margin *= math.sqrt(z2) / (1 + z2 / samples)
    low, high = max(0, center - margin), min(1, center + margin)
    verdict = "inconclusive"
    if samples >= minimum:
        if low >= continue_rate:
            verdict = "continue"
        elif high <= stop_rate:
            verdict = "stop"
    return {
        "samples": samples,
        "successes": successes,
        "rate": rate,
        "interval_95": [low, high],
        "recommendation": verdict,
    }


def serialize(row):
    return jsonable_encoder(
        {
            "id": row.id,
            "organization_id": row.organization_id,
            "created_at": row.created_at,
            "version": row.version,
            "data": row.data,
        }
    )


def revision(row, expected):
    if row.version != expected:
        raise HTTPException(409, "Experiment changed; refresh before retrying")


@router.post("", status_code=201)
def create(data: ExperimentCreate, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    lock_org(db, m.organization_id)
    scoped(db, Project, data.project_id, m.organization_id)
    payload = data.model_dump()
    payload.update(
        state="draft",
        evidence_class="owner_reported_not_independently_verified",
        statistics=result(0, 0, data.minimum_samples, data.continue_rate, data.stop_rate),
    )
    row = Experiments(organization_id=m.organization_id, data=payload)
    db.add(row)
    db.flush()
    emit(db, m.organization_id, "experiment", row.id, "experiment.created", payload, user.id)
    return serialize(row)


@router.get("/{id}/observations")
def observations(id: str, m=Depends(owner), db=Depends(get_db)):
    scoped(db, Experiments, id, m.organization_id)
    rows = db.scalars(
        select(CustomerMetrics)
        .where(
            CustomerMetrics.organization_id == m.organization_id,
            CustomerMetrics.data["experiment_id"].as_string() == id,
        )
        .order_by(CustomerMetrics.created_at)
    ).all()
    return [serialize(row) for row in rows]


@router.post("/{id}/actions")
def action(id: str, data: ExperimentAction, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    org = lock_org(db, m.organization_id)
    row = scoped(db, Experiments, id, m.organization_id)
    revision(row, data.expected_version)
    state = row.data["state"]
    allowed = {"start": {"draft", "paused"}, "pause": {"running"}, "conclude": {"running", "paused"}}
    if state not in allowed[data.action]:
        raise HTTPException(409, "Invalid experiment transition")
    if data.action == "start":
        project = scoped(db, Project, row.data["project_id"], m.organization_id)
        if org.stopped or project.paused:
            raise HTTPException(409, "Company stopped or project paused")
    next_state = {"start": "running", "pause": "paused", "conclude": "concluded"}[data.action]
    row.data = {
        **row.data,
        "state": next_state,
        "updated_at": now().isoformat(),
        "execution_scope": "record_evidence_only",
    }
    row.version += 1
    emit(
        db,
        m.organization_id,
        "experiment",
        id,
        "experiment." + next_state,
        {
            "version": row.version,
            "statistics": row.data["statistics"],
            "external_execution_authorized": False,
        },
        user.id,
    )
    return serialize(row)


@router.post("/{id}/observations")
def observe(id: str, data: Observation, m=Depends(owner), user=Depends(current_user), db=Depends(get_db)):
    org = lock_org(db, m.organization_id)
    row = scoped(db, Experiments, id, m.organization_id)
    # Retries return the original receipt, even if the aggregate revision advanced.
    reference = data.reference.strip()
    key = hashlib.sha256(reference.encode()).hexdigest()
    existing = db.scalar(
        select(CustomerMetrics).where(
            CustomerMetrics.organization_id == m.organization_id,
            CustomerMetrics.data["experiment_id"].as_string() == id,
            CustomerMetrics.data["reference_hash"].as_string() == key,
        )
    )
    content = {
        "reference": reference,
        "samples": data.samples,
        "successes": data.successes,
        "artifact_id": data.artifact_id,
        "notes": data.notes,
    }
    if existing:
        if any(existing.data[k] != v for k, v in content.items()):
            raise HTTPException(409, "Reference already records different evidence")
        return {"duplicate": True, "observation": serialize(existing), "experiment": serialize(row)}
    revision(row, data.expected_version)
    if row.data["state"] != "running" or org.stopped:
        raise HTTPException(409, "Experiment is not running or company stopped")
    project = scoped(db, Project, row.data["project_id"], m.organization_id)
    if project.paused:
        raise HTTPException(409, "Project paused")
    artifact = scoped(db, Artifact, data.artifact_id, m.organization_id)
    from .models import Task

    task = scoped(db, Task, artifact.task_id, m.organization_id)
    if not artifact.verified or task.project_id != project.id:
        raise HTTPException(422, "A checksummed evidence artifact from this project is required")
    metric = CustomerMetrics(
        organization_id=m.organization_id,
        data={
            **content,
            "experiment_id": id,
            "reference_hash": key,
            "artifact_sha256": artifact.sha256,
            "submitted_by": user.id,
            "evidence_class": "owner_reported_not_independently_verified",
        },
    )
    db.add(metric)
    db.flush()
    previous = row.data["statistics"]
    stats = result(
        previous["samples"] + data.samples,
        previous["successes"] + data.successes,
        row.data["minimum_samples"],
        row.data["continue_rate"],
        row.data["stop_rate"],
    )
    row.data = {**row.data, "statistics": stats, "updated_at": now().isoformat()}
    row.version += 1
    emit(
        db,
        m.organization_id,
        "experiment",
        id,
        "experiment.observed",
        {
            "observation_id": metric.id,
            "artifact_sha256": artifact.sha256,
            "statistics": stats,
            "version": row.version,
        },
        user.id,
    )
    return {"duplicate": False, "observation": serialize(metric), "experiment": serialize(row)}
