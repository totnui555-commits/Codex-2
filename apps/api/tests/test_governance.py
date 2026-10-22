import concurrent.futures
from datetime import timedelta
from decimal import Decimal
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from company_os.db import Session
from company_os.models import Task, Organization, Reservation, Usage, Approval, Incident, now
from company_os.domain import reserve, reconcile, authorize
from company_os.watchtower import inspect_organization
from conftest import create_task


def enable(org_id, limit=2000):
    with Session.begin() as db:
        org = db.get(Organization, org_id)
        org.paid_execution_authorized = True
        org.monthly_limit = limit


def test_paid_default_denied_and_concurrent_reservations(owner_client, project):
    task = create_task(owner_client, project)
    with Session.begin() as db:
        with pytest.raises(HTTPException):
            reserve(db, db.get(Task, task["id"]), "denied", 20)
    enable(project["organization_id"], 30)

    def attempt(i):
        try:
            with Session.begin() as db:
                reserve(db, db.get(Task, task["id"]), f"run-{i}", 20)
            return True
        except HTTPException:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, range(2)))
    assert sum(results) == 1
    with Session() as db:
        assert len(db.scalars(select(Reservation)).all()) == 1


def test_reservation_idempotency_and_overrun_stops_company(owner_client, project):
    task = create_task(owner_client, project)
    enable(project["organization_id"])
    with Session.begin() as db:
        t = db.get(Task, task["id"])
        a = reserve(db, t, "same-run", 20)
        b = reserve(db, t, "same-run", 20)
        assert a.id == b.id
        reconcile(db, a, 25, "test-provider", {"input_tokens": 10})
        reconcile(db, a, 25, "test-provider", {"input_tokens": 10})
    with Session() as db:
        assert db.get(Organization, project["organization_id"]).stopped
        assert len(db.scalars(select(Usage)).all()) == 1


def test_approval_bound_to_exact_target_artifact_and_one_use(owner_client, project):
    sha = "a" * 64
    a = owner_client.post(
        "/approvals",
        json={
            "action": "production_release",
            "artifact_sha256": sha,
            "target": "staging-commit-test",
            "max_exposure": 30,
        },
    ).json()
    assert (
        owner_client.post(
            f"/approvals/{a['id']}/decide", json={"decision": "approved", "artifact_sha256": "b" * 64}
        ).status_code
        == 409
    )
    assert (
        owner_client.post(
            f"/approvals/{a['id']}/decide", json={"decision": "approved", "artifact_sha256": sha}
        ).status_code
        == 200
    )
    with Session.begin() as db:
        with pytest.raises(HTTPException):
            authorize(
                db, project["organization_id"], "production_release", "b" * 64, "staging-commit-test", a["id"]
            )
    with Session.begin() as db:
        assert authorize(
            db, project["organization_id"], "production_release", sha, "staging-commit-test", a["id"]
        )
    with Session.begin() as db:
        with pytest.raises(HTTPException):
            authorize(
                db, project["organization_id"], "production_release", sha, "staging-commit-test", a["id"]
            )


def test_expired_approval_denied(owner_client, project):
    a = owner_client.post(
        "/approvals", json={"action": "public_launch", "artifact_sha256": "a" * 64, "target": "example.com"}
    ).json()
    with Session.begin() as db:
        db.get(Approval, a["id"]).expires_at = now() - timedelta(seconds=1)
    assert (
        owner_client.post(
            f"/approvals/{a['id']}/decide", json={"decision": "approved", "artifact_sha256": "a" * 64}
        ).status_code
        == 409
    )


def test_watchtower_quarantines_stalled_and_false_completion(owner_client, project):
    task = create_task(owner_client, project)
    with Session.begin() as db:
        t = db.get(Task, task["id"])
        t.status = "running"
        t.lease_until = now() - timedelta(seconds=10)
    with Session.begin() as db:
        assert inspect_organization(db, project["organization_id"])
    with Session.begin() as db:
        inspect_organization(db, project["organization_id"])
    with Session() as db:
        assert db.get(Task, task["id"]).status == "quarantined"
        assert len(db.scalars(select(Incident)).all()) == 1
