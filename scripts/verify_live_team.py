"""Bounded real planner/delegation verification, not a customer or hosted coding test."""

import asyncio
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import httpx
from company_os.db import Session
from company_os.domain import emit, lock_org
from company_os.models import AgentRun, Artifact, Project, Reservation, Task, TaskDependency
from company_os.orchestration import TaskWorkflow, execute_task
from company_os.providers import ArtifactStore
from sqlalchemy import select
from temporalio.client import Client
from temporalio.worker import Worker


async def main():
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    credentials = json.loads(Path(".local/owner-credentials.json").read_text())
    scheduler_was_running = False
    # Pause local automatic dispatch during the explicitly bounded verification.
    processes = subprocess.check_output(["ps", "-eo", "pid,args"], text=True).splitlines()
    for line in processes[1:]:
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[1] in {
            ".venv/bin/python -m company_os.scheduler",
            str(root / ".venv/bin/python") + " -m company_os.scheduler",
        }:
            scheduler_was_running = True
            os.kill(int(parts[0]), signal.SIGTERM)
            for _ in range(50):
                try:
                    os.kill(int(parts[0]), 0)
                except ProcessLookupError:
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError("Scheduler did not stop; refusing concurrent verification")
    try:
        with httpx.Client(base_url="http://localhost:8000", timeout=15) as api:
            api.post(
                "/auth/login", json={"email": credentials["email"], "password": credentials["password"]}
            ).raise_for_status()
            snapshot = api.get("/snapshot").json()
            if snapshot["organization"]["stopped"] or snapshot["organization"]["paid_execution_authorized"]:
                raise RuntimeError("Expected a resumed company with paid execution disabled")
            policy = dict(
                mode="research_only",
                paid_execution_authorized=True,
                monthly_limit=100,
                max_paid_concurrency=1,
            )
            try:
                api.put("/company/policy", json=policy).raise_for_status()
                with Session.begin() as db:
                    org = lock_org(db, snapshot["organization"]["id"])
                    project = Project(
                        organization_id=org.id,
                        name="Internal multi-agent incubation review",
                        description="Real bounded planner and two specialist invocations; no market validation or hosted code execution.",
                        budget_limit=30,
                    )
                    db.add(project)
                    db.flush()
                    objective = (
                        "Create EXACTLY TWO independent tasks with no dependencies. Use exactly one business_analyst and one ux_researcher. "
                        "Each task must include all facts needed for a text-only advisory review: Product Incubator stores draft/running/paused/concluded experiments in PostgreSQL; "
                        "owner-reported observation batches require checksummed same-project artifacts; references deduplicate counts; "
                        "Wilson 95% intervals and predeclared thresholds yield continue/stop/inconclusive; starts do not authorize campaigns/spending. "
                        "35 actual backend tests and real browser persistence checks passed. Daytona and HTTPS gateway credentials are absent. "
                        "Ask business_analyst to identify measurement limitations and ux_researcher to identify consent/usability validation questions. "
                        "Both reviews are advisory, using only the provided facts. No customer interviews, new tests, source reads or demand validation occurred. "
                        "No coding, publishing, purchases, outreach or additional delegation."
                    )
                    parent = Task(
                        organization_id=org.id,
                        project_id=project.id,
                        title="Plan two independent incubation reviews",
                        objective=objective,
                        agent_role="chief_of_staff",
                        status="scheduled",
                        acceptance=["Two independent advisory reviews; no fabricated market evidence"],
                        expected_artifacts=["project_plan"],
                        budget_limit=10,
                    )
                    db.add(parent)
                    db.flush()
                    project_id, parent_id = project.id, parent.id
                    emit(
                        db,
                        org.id,
                        "task",
                        parent.id,
                        "task.created",
                        {
                            "title": parent.title,
                            "authorization": "Founder authorized continued implementation",
                            "scope": "one planner plus at most two specialist calls; THB100 organization cap; research only",
                        },
                    )
                client = await Client.connect("localhost:7233")
                queue = "company-os-team-verification"
                async with Worker(
                    client, task_queue=queue, workflows=[TaskWorkflow], activities=[execute_task]
                ):

                    async def execute(task_id):
                        workflow_id = "team-verification-" + task_id
                        with Session.begin() as db:
                            task = db.get(Task, task_id)
                            task.workflow_id = workflow_id
                        return await client.execute_workflow(
                            TaskWorkflow.run, task_id, id=workflow_id, task_queue=queue
                        )

                    parent_result = await execute(parent_id)
                    if parent_result["status"] != "completed":
                        raise RuntimeError("Planner did not complete; inspect Inbox")
                    with Session() as db:
                        children = db.scalars(
                            select(Task).where(Task.project_id == project_id, Task.id != parent_id)
                        ).all()
                        if len(children) != 2 or {c.agent_role for c in children} != {
                            "business_analyst",
                            "ux_researcher",
                        }:
                            raise RuntimeError(
                                "Planner exceeded bounded role/count scope; children will not execute"
                            )
                        child_ids = [c.id for c in children]
                        if db.scalar(select(TaskDependency).where(TaskDependency.task_id.in_(child_ids))):
                            raise RuntimeError(
                                "Expected independent reviewers; no owner reviews will be bypassed"
                            )
                    outcomes = [parent_result]
                    for task_id in child_ids:
                        outcomes.append(await execute(task_id))
                evidence = {
                    "scope": "real internal advisory delegation; not customer validation or hosted coding",
                    "project_id": project_id,
                    "parent_task_id": parent_id,
                    "specialist_task_ids": child_ids,
                    "results": outcomes,
                    "runs": [],
                }
                with Session() as db:
                    for task_id in [parent_id, *child_ids]:
                        task = db.get(Task, task_id)
                        run = db.scalar(select(AgentRun).where(AgentRun.task_id == task_id))
                        artifact = db.scalar(select(Artifact).where(Artifact.task_id == task_id))
                        reservation = db.scalar(select(Reservation).where(Reservation.task_id == task_id))
                        if not artifact or not artifact.verified:
                            raise RuntimeError("Missing verified report; inspect Inbox")
                        ArtifactStore().read(artifact.uri, artifact.sha256)
                        evidence["runs"].append(
                            {
                                "task_id": task.id,
                                "role": task.agent_role,
                                "workflow_id": task.workflow_id,
                                "status": task.status,
                                "run_id": run.id,
                                "provider": run.provider,
                                "usage": run.usage,
                                "cost_thb_estimated": str(reservation.actual),
                                "artifact_id": artifact.id,
                                "artifact_sha256": artifact.sha256,
                            }
                        )
                Path("docs/evidence/live-team-run.json").write_text(json.dumps(evidence, indent=2) + "\n")
                print(
                    json.dumps(
                        {
                            "project_id": project_id,
                            "roles": [r["role"] for r in evidence["runs"]],
                            "statuses": [r["status"] for r in evidence["runs"]],
                        }
                    )
                )
            finally:
                policy["paid_execution_authorized"] = False
                try:
                    api.put("/company/policy", json=policy).raise_for_status()
                finally:
                    # Local recovery is fail-closed even if the API became unavailable.
                    with Session.begin() as db:
                        org = lock_org(db, snapshot["organization"]["id"])
                        org.paid_execution_authorized = False
                        emit(
                            db,
                            org.id,
                            "organization",
                            org.id,
                            "verification.paid_execution_disabled",
                            {"scope": "bounded_team_verification_cleanup"},
                        )
                print("Paid execution restored to disabled.")
    finally:
        if scheduler_was_running:
            with Path("/tmp/company-os-scheduler.log").open("a") as log:
                subprocess.Popen(
                    [str(root / ".venv/bin/python"), "-m", "company_os.scheduler"],
                    cwd=root,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            print("Local scheduler restored.")


if __name__ == "__main__":
    asyncio.run(main())
