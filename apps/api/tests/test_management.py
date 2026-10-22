from datetime import timedelta
from sqlalchemy import text
from company_os.db import Session
from company_os.models import Organization, User, Membership, Project, Task, Audit, Artifact, now
from company_os.domain import transition, add_dependency, verify_audit
from company_os.security import passwords
from conftest import create_task


def test_authentication_and_origin(client):
    assert client.get("/snapshot").status_code == 401
    assert (
        client.post(
            "/auth/bootstrap",
            json={
                "email": "founder@example.com",
                "password": "long-test-password-123",
                "bootstrap_token": "wrong",
                "organization_name": "Test",
            },
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/projects", json={"name": "CSRF"}, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )


def test_persistent_crud_events_and_audit(owner_client, project):
    task = create_task(owner_client, project)
    snapshot = owner_client.get("/snapshot").json()
    assert snapshot["tasks"][0]["id"] == task["id"]
    assert snapshot["kpis"]["active_agents"] == 0
    assert snapshot["integrations"]["email"] == "disconnected"
    assert any(e["event_type"] == "task.created" for e in snapshot["events"])
    assert owner_client.get("/audit/verify").json()["valid"]
    assert owner_client.post("/tasks/" + task["id"] + "/cancel").status_code == 200
    with Session() as db:
        assert db.get(Task, task["id"]).status == "cancelled"
        assert verify_audit(db, project["organization_id"])


def test_tenant_isolation(owner_client, project):
    with Session.begin() as db:
        other = Organization(name="Other organization")
        db.add(other)
        db.flush()
        private = Project(organization_id=other.id, name="Hidden project")
        db.add(private)
        db.flush()
        other_id, private_id = other.id, private.id
    assert owner_client.get("/snapshot", headers={"X-Organization-ID": other_id}).status_code == 403
    assert owner_client.patch("/projects/" + private_id, json={"paused": True}).status_code == 404
    assert (
        owner_client.post(
            "/tasks",
            json={
                "project_id": private_id,
                "title": "Cross tenant",
                "objective": "Must be rejected",
                "acceptance": ["Denied"],
            },
        ).status_code
        == 404
    )


def test_dependency_cycle_and_execution_gate(owner_client, project):
    a = create_task(owner_client, project)
    b = create_task(owner_client, project, dependencies=[a["id"]])
    assert owner_client.post(f"/tasks/{a['id']}/dependencies/{b['id']}").status_code == 409
    from fastapi import HTTPException
    import pytest

    with Session.begin() as db:
        with pytest.raises(HTTPException, match="Dependencies are incomplete"):
            transition(db, db.get(Task, b["id"]), "scheduled")


def test_stop_and_revoke(owner_client, project):
    task = create_task(owner_client, project)
    assert owner_client.post("/company/stop").status_code == 200
    snap = owner_client.get("/snapshot").json()
    assert snap["organization"]["stopped"]
    assert snap["tasks"][0]["status"] == "quarantined"
    assert owner_client.post("/auth/logout").status_code == 200
    assert owner_client.get("/snapshot").status_code == 401


def test_audit_tampering_detected(owner_client, project):
    with Session.begin() as db:
        db.execute(text("ALTER TABLE audit_records DISABLE TRIGGER immutable_history"))
        audit = db.query(Audit).first()
        audit.payload = {"tampered": True}
        db.flush()
        db.execute(text("ALTER TABLE audit_records ENABLE TRIGGER immutable_history"))
    assert owner_client.get("/audit/verify").json()["valid"] is False


def test_inbox_answer_not_approval(owner_client):
    msg = owner_client.get("/snapshot").json()["messages"][0]
    r = owner_client.post("/inbox/" + msg["id"] + "/respond", json={"response": "Configure providers later"})
    assert r.status_code == 200 and r.json()["state"] == "answered"
    assert owner_client.get("/snapshot").json()["approvals"] == []
