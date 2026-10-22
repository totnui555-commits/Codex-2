from datetime import timedelta

import pytest
from company_os.db import Session
from company_os.models import AgentRun, Incident, Organization, Project, Sandboxes, Task, now
from company_os.settings import settings
from company_os.watchtower import inspect_organization, monitor_once, reclaim_revoked_sandboxes
from conftest import create_task
from sqlalchemy import func, select, text


def test_existing_critical_incident_still_stops_resumed_company(owner_client, project):
    org_id = project["organization_id"]
    with Session.begin() as db:
        org = db.get(Organization, org_id)
        org.audit_head = "f" * 64
        org.stopped = False
        db.add(
            Incident(
                organization_id=org_id,
                kind="audit_integrity",
                severity="critical",
                details={"reason": "Previous detection"},
                dedupe_key=f"{org_id}:audit_integrity:company",
            )
        )
    with Session.begin() as db:
        inspect_organization(db, org_id)
    with Session() as db:
        assert db.get(Organization, org_id).stopped
        assert db.scalar(select(func.count()).select_from(Incident)) == 1


@pytest.mark.parametrize(
    "condition", ["missing_lease", "paid_revoked", "project_paused", "coding_in_research"]
)
def test_watchtower_enforces_live_execution_policy(owner_client, project, condition):
    task = create_task(owner_client, project, agent_role="backend_engineer")
    with Session.begin() as db:
        org = db.get(Organization, project["organization_id"])
        org.paid_execution_authorized = True
        org.mode = "build_autopilot"
        row = db.get(Task, task["id"])
        row.status = "running"
        row.lease_until = now() + timedelta(minutes=5)
        if condition == "missing_lease":
            row.lease_until = None
        elif condition == "paid_revoked":
            org.paid_execution_authorized = False
        elif condition == "project_paused":
            db.get(Project, project["id"]).paused = True
        else:
            org.mode = "research_only"
        run = AgentRun(
            organization_id=org.id,
            task_id=row.id,
            status="running",
            agent_role=row.agent_role,
            provider="boundary_test",
        )
        db.add(run)
        db.flush()
        run_id = run.id
    with Session.begin() as db:
        db.execute(text("SET LOCAL ROLE company_watchtower"))
        assert inspect_organization(db, project["organization_id"])
    with Session() as db:
        assert db.get(Task, task["id"]).status == "quarantined"
        assert db.get(AgentRun, run_id).status == "quarantined"
        assert db.scalar(select(func.count()).select_from(Incident)) == 1


async def test_provider_failure_does_not_disable_monitor_cycle(owner_client, project, monkeypatch, caplog):
    async def unavailable():
        raise RuntimeError("private-value-must-not-be-logged")

    monkeypatch.setattr("company_os.watchtower.reclaim_revoked_sandboxes", unavailable)
    await monitor_once()
    await monitor_once()
    assert "Sandbox reclamation failed" in caplog.text
    assert "private-value-must-not-be-logged" not in caplog.text


async def test_one_organization_failure_does_not_skip_others(owner_client, project, monkeypatch):
    with Session.begin() as db:
        other = Organization(name="Independent organization")
        db.add(other)
        db.flush()
        other_id = other.id
    checked = []

    def inspect(db, org_id):
        checked.append(org_id)
        if org_id == project["organization_id"]:
            raise RuntimeError("broken tenant boundary test")

    async def no_sandboxes():
        pass

    monkeypatch.setattr("company_os.watchtower.inspect_organization", inspect)
    monkeypatch.setattr("company_os.watchtower.reclaim_revoked_sandboxes", no_sandboxes)
    await monitor_once()
    assert set(checked) == {project["organization_id"], other_id}


@pytest.mark.parametrize("condition", ["project_paused", "paid_revoked", "active", "lookup_failure"])
async def test_remote_cleanup_policy_boundary(owner_client, project, monkeypatch, condition):
    """Controlled provider boundary only; not evidence of live Daytona termination."""
    task = create_task(owner_client, project, agent_role="backend_engineer")
    with Session.begin() as db:
        org = db.get(Organization, project["organization_id"])
        org.paid_execution_authorized = condition != "paid_revoked"
        org.mode = "build_autopilot"
        db.get(Project, project["id"]).paused = condition in {"project_paused", "lookup_failure"}
        row = db.get(Task, task["id"])
        row.status = "running"
        row.lease_until = now() + timedelta(minutes=5)
        run = AgentRun(
            organization_id=org.id,
            task_id=row.id,
            status="running",
            agent_role=row.agent_role,
            provider="daytona/codex",
        )
        db.add(run)
        db.flush()
        sandbox = Sandboxes(
            organization_id=org.id,
            data={"run_id": run.id, "provider_id": "controlled-provider-boundary", "state": "running"},
        )
        db.add(sandbox)
        db.flush()
        sandbox_id = sandbox.id
    calls = []

    class Provider:
        def get(self, provider_id):
            calls.append(("get", provider_id))
            if condition == "lookup_failure":
                raise TimeoutError()
            return provider_id

        def delete(self, sandbox, wait):
            assert wait is True
            calls.append(("delete", sandbox))

    monkeypatch.setattr(settings(), "daytona_api_key", "boundary-test-only")
    monkeypatch.setattr("daytona.Daytona", lambda config: Provider())
    await reclaim_revoked_sandboxes()
    with Session() as db:
        data = db.get(Sandboxes, sandbox_id).data
        if condition == "active":
            assert not calls and data["state"] == "running"
        elif condition == "lookup_failure":
            assert [c[0] for c in calls] == ["get"]
            assert data["state"] == "stop_failed" and data["stop_attempts"] == 1
        else:
            assert [c[0] for c in calls] == ["get", "delete"]
            assert data["state"] == "deleted" and data["stop_attempts"] == 1
