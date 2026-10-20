import pytest
from company_os.db import Session
from company_os.handoffs import dependency_evidence
from company_os.models import Artifact, Task
from company_os.providers import ArtifactStore, IntegrationBlocked
from company_os.settings import settings
from conftest import create_task
from cryptography.fernet import Fernet


@pytest.fixture
def store(tmp_path, monkeypatch):
    for key, value in {
        "artifact_backend": "filesystem",
        "artifact_directory": str(tmp_path),
        "artifact_encryption_key": Fernet.generate_key().decode(),
        "runtime": "development",
    }.items():
        monkeypatch.setattr(settings(), key, value)
    return ArtifactStore()


def pair(client, project, store, content=None):
    parent = create_task(client, project, agent_role="business_analyst")
    child = create_task(client, project, dependencies=[parent["id"]])
    uri, sha = store.put(
        project["organization_id"],
        parent["id"],
        "specialist_report",
        content or {"summary": "Observed source facts", "api_key": "private-value"},
    )
    with Session.begin() as db:
        artifact = Artifact(
            organization_id=project["organization_id"],
            task_id=parent["id"],
            kind="specialist_report",
            uri=uri,
            sha256=sha,
            verified=True,
        )
        db.add(artifact)
        db.flush()
        task = db.get(Task, parent["id"])
        task.status = "completed"
        task.checkpoint = {"accepted_artifact_id": artifact.id, "accepted_sha256": sha}
        return parent["id"], child["id"], artifact.id


def test_real_encrypted_handoff_preserves_provenance_and_redacts(owner_client, project, store):
    parent, child, artifact = pair(owner_client, project, store)
    with Session() as db:
        evidence = dependency_evidence(db, db.get(Task, child), store)
        assert evidence[0]["task_id"] == parent and evidence[0]["artifact_id"] == artifact
        assert evidence[0]["sha256"] == db.get(Artifact, artifact).sha256
        assert evidence[0]["content"] == {"summary": "Observed source facts", "api_key": "[REDACTED]"}
        assert "untrusted" in evidence[0]["trust"]


@pytest.mark.parametrize(
    "mutation",
    ["pending_review", "unverified", "missing_selection", "wrong_project", "changed_approval_hash"],
)
def test_handoff_fails_closed_on_invalid_provenance(owner_client, project, store, mutation):
    parent, child, artifact = pair(owner_client, project, store)
    with Session.begin() as db:
        task = db.get(Task, parent)
        if mutation == "pending_review":
            task.status = "waiting_for_approval"
        elif mutation == "unverified":
            db.get(Artifact, artifact).verified = False
        elif mutation == "missing_selection":
            task.checkpoint = {}
        elif mutation == "wrong_project":
            db.get(Task, child).project_id = owner_client.post(
                "/projects", json={"name": "Other project"}
            ).json()["id"]
        else:
            task.checkpoint = {**task.checkpoint, "accepted_sha256": "0" * 64}
    with Session() as db:
        with pytest.raises(IntegrationBlocked):
            dependency_evidence(db, db.get(Task, child), store)


def test_tampered_artifact_and_oversized_handoff_are_not_passed(owner_client, project, store):
    _, child, artifact = pair(owner_client, project, store, {"summary": "x" * 33000})
    with Session() as db:
        with pytest.raises(IntegrationBlocked, match="handoff budget"):
            dependency_evidence(db, db.get(Task, child), store)
    with Session.begin() as db:
        row = db.get(Artifact, artifact)
        row.sha256 = "f" * 64
        parent = db.get(Task, row.task_id)
        parent.checkpoint = {"artifact_id": row.id}
    with Session() as db:
        with pytest.raises(ValueError, match="integrity"):
            dependency_evidence(db, db.get(Task, child), store)


def test_owner_acceptance_records_exact_artifact_for_downstream(owner_client, project, store):
    parent, _, artifact = pair(owner_client, project, store)
    with Session.begin() as db:
        db.get(Task, parent).status = "waiting_for_approval"
    response = owner_client.post(f"/tasks/{parent}/accept-artifact/{artifact}")
    assert response.status_code == 200, response.text
    assert response.json()["checkpoint"]["accepted_artifact_id"] == artifact
    assert response.json()["checkpoint"]["accepted_sha256"]
    assert owner_client.get("/audit/verify").json()["valid"]
