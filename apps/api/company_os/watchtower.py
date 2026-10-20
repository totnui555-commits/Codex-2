import asyncio

from sqlalchemy import select

from .db import Session
from .domain import emit, inbox, verify_audit
from .health import service_heartbeat
from .models import AgentRun, Artifact, Incident, Organization, Sandboxes, Task, now
from .security import redact


# Stop-only enforcement. This service cannot approve, spend, publish, or release.
def inspect_organization(db, org_id):
    org = db.scalar(select(Organization).where(Organization.id == org_id).with_for_update())
    findings = []
    if not verify_audit(db, org_id):
        findings.append(("audit_integrity", "critical", None, {"reason": "Hash chain verification failed"}))
    tasks = db.scalars(select(Task).where(Task.organization_id == org_id)).all()
    for task in tasks:
        if task.status == "running" and task.lease_until and task.lease_until < now():
            findings.append(("stalled_worker", "high", task, {"reason": "Worker lease expired"}))
        if task.attempts > task.max_attempts:
            findings.append(("retry_limit", "high", task, {"attempts": task.attempts}))
        if task.status == "completed":
            artifacts = db.scalars(
                select(Artifact).where(Artifact.task_id == task.id, Artifact.verified.is_(True))
            ).all()
            if not artifacts:
                findings.append(("false_completion", "high", task, {"reason": "No verified artifact"}))
        if task.error and redact(task.error) != task.error:
            task.error = redact(task.error)
            findings.append(
                ("secret_exposure", "critical", task, {"reason": "Secret-like value detected and redacted"})
            )
    for kind, severity, task, details in findings:
        key = f"{org_id}:{kind}:{task.id if task else 'company'}"
        if db.scalar(select(Incident).where(Incident.dedupe_key == key)):
            continue
        incident = Incident(
            organization_id=org_id,
            severity=severity,
            kind=kind,
            task_id=task.id if task else None,
            details=details,
            dedupe_key=key,
        )
        db.add(incident)
        db.flush()
        if task:
            if task.status not in {"cancelled", "quarantined"}:
                task.status = "quarantined"
            for run in db.scalars(
                select(AgentRun).where(AgentRun.task_id == task.id, AgentRun.status == "running")
            ).all():
                run.status = "quarantined"
        if severity == "critical":
            org.stopped = True
        emit(
            db,
            org_id,
            "incident",
            incident.id,
            "watchtower.incident",
            {"kind": kind, "severity": severity, "task_id": task.id if task else None},
        )
        inbox(
            db,
            org_id,
            f"Watchtower: {kind}",
            details.get("reason", str(details)),
            "critical" if severity == "critical" else "action_required",
            dedupe=key,
        )
    return findings


async def reclaim_revoked_sandboxes():
    from daytona import Daytona, DaytonaConfig, DaytonaError, DaytonaNotFoundError

    from .settings import settings

    if not settings().daytona_api_key:
        return
    client = Daytona(DaytonaConfig(api_key=settings().daytona_api_key, api_url=settings().daytona_api_url))
    with Session.begin() as db:
        rows = db.scalars(select(Sandboxes).with_for_update(skip_locked=True)).all()
        for row in rows:
            if (
                row.data.get("state") not in {"running", "stop_failed"}
                or row.data.get("stop_attempts", 0) >= 3
            ):
                continue
            run = db.get(AgentRun, row.data["run_id"])
            task = db.get(Task, run.task_id) if run else None
            org = db.get(Organization, row.organization_id)
            if run and run.status == "running" and task and task.status == "running" and not org.stopped:
                continue
            attempts = row.data.get("stop_attempts", 0) + 1
            try:
                sandbox = await asyncio.to_thread(client.get, row.data["provider_id"])
                await asyncio.to_thread(client.delete, sandbox, wait=True)
                state = "deleted"
            except DaytonaNotFoundError:
                state = "deleted"
            except DaytonaError:
                state = "stop_failed"
            row.data = {
                **row.data,
                "state": state,
                "stop_attempts": attempts,
                "observed_at": now().isoformat(),
            }
            emit(
                db,
                row.organization_id,
                "sandbox",
                row.id,
                "sandbox." + state,
                {"provider_id": row.data["provider_id"], "attempts": attempts},
            )
            if state == "stop_failed" and attempts >= 3:
                inbox(
                    db,
                    row.organization_id,
                    "Remote sandbox cleanup failed",
                    "Inspect the provider session and revoke access. Remote termination has not been confirmed.",
                    "critical",
                    dedupe="sandbox-cleanup:" + row.id,
                )


async def main():
    while True:
        service_heartbeat("watchtower")
        with Session.begin() as db:
            for org_id in db.scalars(select(Organization.id)).all():
                inspect_organization(db, org_id)
        await reclaim_revoked_sandboxes()
        await asyncio.sleep(15)


if __name__ == "__main__":
    asyncio.run(main())
