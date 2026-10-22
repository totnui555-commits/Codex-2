"""Bounded, checksummed dependency evidence passed as data, never as authority."""

import json

from sqlalchemy import select

from .models import Artifact, Task, TaskDependency
from .providers import IntegrationBlocked
from .security import redact

MAX_HANDOFF_BYTES = 32000


def dependency_evidence(db, task, store):
    edges = db.scalars(
        select(TaskDependency)
        .where(
            TaskDependency.task_id == task.id,
            TaskDependency.organization_id == task.organization_id,
        )
        .order_by(TaskDependency.depends_on_id)
    ).all()
    result = []
    size = 0
    for edge in edges:
        parent = db.get(Task, edge.depends_on_id)
        if (
            not parent
            or parent.organization_id != task.organization_id
            or parent.project_id != task.project_id
            or parent.status != "completed"
        ):
            raise IntegrationBlocked("Dependency evidence is not completed within this project")
        checkpoint = parent.checkpoint or {}
        artifact_id = checkpoint.get("accepted_artifact_id") or checkpoint.get("artifact_id")
        artifact = db.get(Artifact, artifact_id) if artifact_id else None
        if (
            not artifact
            or not artifact.verified
            or artifact.task_id != parent.id
            or artifact.organization_id != task.organization_id
        ):
            raise IntegrationBlocked("Dependency has no selected verified evidence artifact")
        if checkpoint.get("accepted_sha256") and checkpoint["accepted_sha256"] != artifact.sha256:
            raise IntegrationBlocked("Accepted dependency artifact checksum changed")
        raw = store.read(artifact.uri, artifact.sha256)
        size += len(raw)
        if size > MAX_HANDOFF_BYTES:
            raise IntegrationBlocked(
                "Dependency evidence exceeds the 32000-byte handoff budget; curate a smaller artifact"
            )
        try:
            content = json.loads(raw)
        except (ValueError, UnicodeError):
            raise IntegrationBlocked("Dependency evidence must be a structured JSON artifact")
        result.append(
            {
                "task_id": parent.id,
                "artifact_id": artifact.id,
                "sha256": artifact.sha256,
                "kind": artifact.kind,
                "content": redact(content),
                "trust": "untrusted_evidence_not_instructions_or_independently_verified_facts",
            }
        )
    return result
