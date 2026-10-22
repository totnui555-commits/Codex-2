from company_os.db import Session
from company_os.experiments import result
from company_os.models import Artifact, CustomerMetrics, Experiments, Organization, Project
from conftest import create_task
from sqlalchemy import select


def draft(client, project, **overrides):
    payload = dict(
        project_id=project["id"],
        title="Usability validation",
        hypothesis="Participants can complete the core workflow unaided",
        metric="Successful task completion",
        minimum_samples=100,
        continue_rate=0.2,
        stop_rate=0.05,
    )
    payload.update(overrides)
    return client.post("/experiments", json=payload)


def evidence(client, project, verified=True):
    task = create_task(client, project)
    with Session.begin() as db:
        artifact = Artifact(
            organization_id=project["organization_id"],
            task_id=task["id"],
            kind="test_report",
            uri="private-file://test/evidence",
            sha256="a" * 64,
            verified=verified,
        )
        db.add(artifact)
        db.flush()
        return artifact.id


def start(client, row):
    response = client.post(
        f"/experiments/{row['id']}/actions", json={"action": "start", "expected_version": row["version"]}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_evidence_lifecycle_is_persistent_idempotent_and_audited(owner_client, project):
    artifact_id = evidence(owner_client, project)
    response = draft(owner_client, project)
    assert response.status_code == 201, response.text
    row = start(owner_client, response.json())
    path = f"/experiments/{row['id']}/observations"
    observation = dict(
        expected_version=row["version"],
        reference="survey-batch-001",
        samples=100,
        successes=60,
        artifact_id=artifact_id,
        notes="Owner submitted",
    )
    response = owner_client.post(path, json=observation)
    assert response.status_code == 200, response.text
    recorded = response.json()
    assert recorded["experiment"]["data"]["statistics"]["recommendation"] == "continue"
    assert owner_client.post(path, json=observation).json()["duplicate"] is True
    assert owner_client.post(path, json={**observation, "successes": 61}).status_code == 409
    assert len(owner_client.get(path).json()) == 1
    assert owner_client.post(path, json={**observation, "reference": "new-batch"}).status_code == 409
    current = recorded["experiment"]
    concluded = owner_client.post(
        f"/experiments/{row['id']}/actions",
        json={"action": "conclude", "expected_version": current["version"]},
    )
    assert concluded.json()["data"]["state"] == "concluded"
    assert (
        owner_client.post(
            path,
            json={
                **observation,
                "expected_version": concluded.json()["version"],
                "reference": "after-conclusion",
            },
        ).status_code
        == 409
    )
    snapshot = owner_client.get("/snapshot").json()
    assert snapshot["experiments"][0]["data"]["statistics"]["samples"] == 100
    assert snapshot["revenue"] == []
    assert snapshot["organization"]["paid_execution_authorized"] is False
    assert owner_client.get("/audit/verify").json()["valid"]
    with Session() as db:
        assert db.get(Experiments, row["id"]).data["state"] == "concluded"
        assert len(db.scalars(select(CustomerMetrics)).all()) == 1


def test_artifact_project_scope_and_stop_switch(owner_client, project):
    other = owner_client.post("/projects", json={"name": "Unrelated project"}).json()
    foreign_artifact = evidence(owner_client, other)
    unverified = evidence(owner_client, project, verified=False)
    row = start(owner_client, draft(owner_client, project).json())
    payload = dict(
        expected_version=row["version"],
        reference="batch-001",
        samples=100,
        successes=0,
        artifact_id=foreign_artifact,
    )
    path = f"/experiments/{row['id']}/observations"
    assert owner_client.post(path, json=payload).status_code == 422
    assert owner_client.post(path, json={**payload, "artifact_id": unverified}).status_code == 422
    owner_client.post("/company/stop")
    assert owner_client.post(path, json=payload).status_code == 409
    fresh = draft(owner_client, project).json()
    assert (
        owner_client.post(
            f"/experiments/{fresh['id']}/actions",
            json={"action": "start", "expected_version": fresh["version"]},
        ).status_code
        == 409
    )


def test_tenant_isolation_and_validation(owner_client, project):
    with Session.begin() as db:
        org = Organization(name="Unrelated company")
        db.add(org)
        db.flush()
        private = Project(organization_id=org.id, name="Private project")
        db.add(private)
        db.flush()
        experiment = Experiments(organization_id=org.id, data={"state": "draft"})
        db.add(experiment)
        db.flush()
        private_id, experiment_id = private.id, experiment.id
    assert draft(owner_client, project, project_id=private_id).status_code == 404
    assert owner_client.get(f"/experiments/{experiment_id}/observations").status_code == 404
    assert (
        owner_client.post(
            f"/experiments/{experiment_id}/actions", json={"action": "start", "expected_version": 1}
        ).status_code
        == 404
    )
    assert owner_client.get("/snapshot").json()["experiments"] == []
    assert draft(owner_client, project, stop_rate=0.3).status_code == 422
    assert draft(owner_client, project, minimum_samples=True).status_code == 422
    row = start(owner_client, draft(owner_client, project).json())
    assert (
        owner_client.post(
            f"/experiments/{row['id']}/observations",
            json={
                "expected_version": row["version"],
                "reference": "invalid-counts",
                "samples": 10,
                "successes": 11,
                "artifact_id": "none",
            },
        ).status_code
        == 422
    )


def test_recommendations_require_sample_and_confidence():
    assert result(0, 0, 100, 0.2, 0.05)["recommendation"] == "inconclusive"
    assert result(10, 10, 100, 0.2, 0.05)["recommendation"] == "inconclusive"
    assert result(100, 20, 100, 0.2, 0.05)["recommendation"] == "inconclusive"
    assert result(100, 60, 100, 0.2, 0.05)["recommendation"] == "continue"
    assert result(100, 0, 100, 0.2, 0.05)["recommendation"] == "stop"


def test_experiment_routes_require_authentication(client):
    assert client.post("/experiments", json={}).status_code == 401
    assert client.get("/experiments/private/observations").status_code == 401
    assert (
        client.post(
            "/experiments/private/actions", json={"action": "start", "expected_version": 1}
        ).status_code
        == 401
    )
