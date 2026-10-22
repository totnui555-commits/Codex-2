"""One bounded, founder-delegated research smoke run. Restores paid execution to off."""

import asyncio
import json
from pathlib import Path

import httpx
from company_os.db import Session
from company_os.domain import emit
from company_os.models import AgentRun, Artifact, Organization, Project, Reservation, Task
from company_os.orchestration import TaskWorkflow, execute_task
from company_os.providers import ArtifactStore
from sqlalchemy import select
from temporalio.client import Client
from temporalio.worker import Worker


async def main():
    owner = json.loads(Path(".local/owner-credentials.json").read_text())
    with httpx.Client(base_url="http://localhost:8000", timeout=15) as api:
        api.post(
            "/auth/login", json={"email": owner["email"], "password": owner["password"]}
        ).raise_for_status()
        initial = api.get("/snapshot").json()
        api.put(
            "/company/policy",
            json={
                "mode": "research_only",
                "paid_execution_authorized": True,
                "monthly_limit": 100,
                "max_paid_concurrency": 1,
            },
        ).raise_for_status()
        try:
            with Session.begin() as db:
                org = db.get(Organization, initial["organization"]["id"])
                project = Project(
                    organization_id=org.id,
                    name="Provider activation verification",
                    description="A single real research run authorized by the founder request to handle setup. No sandbox or outreach.",
                    budget_limit=30,
                )
                db.add(project)
                db.flush()
                task = Task(
                    organization_id=org.id,
                    project_id=project.id,
                    title="Review verified setup readiness",
                    objective="Summarize only these verified setup facts: OpenRouter authenticated; GitHub private repository totnui555-commits/Codex-2 is accessible with push permission; PostgreSQL and Temporal are real; local artifacts are encrypted and checksummed. Daytona, hosted gateway and application Gmail OAuth are not configured. List what remains before a hosted coding benchmark. Do not invent sources, revenue, completed code, or test results. This is a readiness report, not external market research.",
                    agent_role="business_analyst",
                    status="scheduled",
                    acceptance=[
                        "Separate verified facts from missing prerequisites",
                        "No claims of a hosted coding run",
                    ],
                    expected_artifacts=["specialist_report"],
                    budget_limit=30,
                )
                db.add(task)
                db.flush()
                task_id = task.id
                emit(
                    db,
                    org.id,
                    "task",
                    task.id,
                    "task.created",
                    {
                        "title": task.title,
                        "authorization": "Founder delegated all setup after THB 100 initial-test recommendation",
                        "scope": "single paid research call; no publication or outreach",
                    },
                )
            client = await Client.connect("localhost:7233")
            async with Worker(
                client,
                task_queue="company-os-setup-verification",
                workflows=[TaskWorkflow],
                activities=[execute_task],
            ):
                await client.execute_workflow(
                    TaskWorkflow.run,
                    task_id,
                    id="setup-research-" + task_id,
                    task_queue="company-os-setup-verification",
                )
            with Session() as db:
                task = db.get(Task, task_id)
                artifact = db.scalar(select(Artifact).where(Artifact.task_id == task_id))
                run = db.scalar(select(AgentRun).where(AgentRun.task_id == task_id))
                reservation = db.scalar(select(Reservation).where(Reservation.task_id == task_id))
                require_artifact = artifact is not None and artifact.verified
                if not require_artifact:
                    raise RuntimeError("No verified stored report; inspect Founder Inbox")
                report = json.loads(ArtifactStore().read(artifact.uri, artifact.sha256))
                evidence = {
                    "task_id": task_id,
                    "workflow_id": "setup-research-" + task_id,
                    "status": task.status,
                    "provider": run.provider,
                    "usage": run.usage,
                    "cost_thb_estimated": str(reservation.actual),
                    "artifact_id": artifact.id,
                    "artifact_sha256": artifact.sha256,
                    "storage": "encrypted persistent local filesystem",
                    "owner_review_required": True,
                    "report": report,
                }
                Path("docs/evidence/live-research-run.json").write_text(json.dumps(evidence, indent=2) + "\n")
                print(json.dumps({k: v for k, v in evidence.items() if k != "report"}, indent=2))
        finally:
            response = api.put(
                "/company/policy",
                json={
                    "mode": "research_only",
                    "paid_execution_authorized": False,
                    "monthly_limit": 100,
                    "max_paid_concurrency": 1,
                },
            )
            response.raise_for_status()
            print("Paid execution restored to disabled; THB 100 ceiling retained.")


if __name__ == "__main__":
    asyncio.run(main())
