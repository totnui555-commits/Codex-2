import asyncio
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from fastapi import HTTPException

    from .db import Session
    from .domain import (
        TERMINAL,
        authorize,
        dependencies_complete,
        emit,
        inbox,
        lock_org,
        reconcile,
        reserve,
        transition,
    )
    from .models import (
        AgentRole,
        AgentRun,
        Artifact,
        Organization,
        Project,
        Reservation,
        Sandboxes,
        Task,
        TaskDependency,
        ToolCalls,
        now,
    )
    from .providers import (
        ArtifactStore,
        DaytonaFactory,
        GitHubProvider,
        IntegrationBlocked,
        artifact_storage_configured,
        coding_credentials_configured,
        plan_goal,
        price_configured,
        research_credentials_configured,
        specialist,
        token_cost,
    )
    from .security import redact
    from .settings import settings


@activity.defn
async def execute_task(task_id: str):
    activity.heartbeat("preflight")
    with Session.begin() as db:
        task = db.get(Task, task_id)
        if not task:
            raise ApplicationError("Unknown task", non_retryable=True)
        org = lock_org(db, task.organization_id)
        if task.status in TERMINAL:
            return {"status": task.status}
        if task.status == "waiting_for_approval":
            return {"status": task.status}
        if not dependencies_complete(db, task):
            return {"status": "dependency_wait"}
        if task.status == "running":
            # An activity restart cannot blindly repeat a paid/externally visible step.
            task.status = "blocked"
            task.error = "Interrupted execution requires usage reconciliation before retry"
            inbox(db, org.id, "Interrupted run needs review", task.error, dedupe="interrupted:" + task.id)
            return {"status": "blocked"}
        missing = []
        if not research_credentials_configured():
            missing.append("OpenAI model credentials")
        if not price_configured():
            missing.append("authorized model prices and dated FX snapshot")
        if not artifact_storage_configured():
            missing.append("private artifact storage")
        if not org.paid_execution_authorized:
            missing.append("founder paid-execution authorization")
        coding = task.agent_role in {"frontend_engineer", "backend_engineer"}
        if coding:
            if not coding_credentials_configured():
                missing.append("Configured coding provider connection")
            if not price_configured(coding=True):
                missing.append("verified Codex model price table")
            if settings().sandbox_thb_per_minute <= 0 or not settings().sandbox_price_observed_at:
                missing.append("dated sandbox minute pricing")
            if org.mode == "research_only":
                missing.append("build_autopilot owner policy")
            if not settings().daytona_api_key or not settings().daytona_snapshot:
                missing.append("hardened Daytona sandbox snapshot")
            if not settings().model_gateway_public_url:
                missing.append("HTTPS scoped model gateway")
            if not settings().github_token or not settings().github_repository:
                missing.append("scoped GitHub connection")
        if missing:
            task.status = "blocked"
            task.error = "Setup required: " + ", ".join(missing)
            emit(db, org.id, "task", task.id, "task.blocked", {"reason": task.error})
            inbox(
                db,
                org.id,
                "Provider setup blocks execution",
                task.error + " Configure secrets securely; never send them in chat.",
                dedupe="runtime-provider-setup",
            )
            return {"status": "blocked", "missing": missing}
        if org.stopped or db.get(Project, task.project_id).paused:
            return {"status": "paused"}
        if task.attempts >= task.max_attempts:
            return {"status": "retry_ceiling"}
        if task.status == "ready":
            transition(db, task, "scheduled")
        if task.status == "blocked":
            transition(db, task, "ready")
            transition(db, task, "scheduled")
        transition(db, task, "running")
        task.attempts += 1
        run = AgentRun(
            organization_id=org.id,
            task_id=task.id,
            agent_role=task.agent_role,
            status="running",
            provider="daytona/codex" if coding else settings().model_provider + "/agents",
        )
        db.add(run)
        db.flush()
        # Conservatively reserve the run cap. Provider gateway enforces each request ceiling.
        estimate = (
            (
                token_cost(4 * 65000, 4 * 2000, coding=True)
                + Decimal(str(settings().sandbox_thb_per_minute)) * 20
            )
            if coding
            else token_cost(64000, 2000)
        )
        try:
            reserve(db, task, run.id, estimate)
        except HTTPException as error:
            task.status = "blocked"
            task.error = str(error.detail)
            run.status = "failed"
            inbox(
                db,
                org.id,
                "Budget preflight blocked execution",
                task.error,
                dedupe="budget-preflight:" + task.id,
            )
            emit(db, org.id, "task", task.id, "task.blocked", {"reason": task.error})
            return {"status": "blocked", "reason": task.error}
        task.lease_owner = run.id
        task.lease_until = now() + timedelta(seconds=60)
        task.checkpoint = {**task.checkpoint, "stage": "running", "run_id": run.id}
        objective = task.objective
        role = task.agent_role
        org_id = org.id
        run_id = run.id
        accepted_roles = [
            r.key
            for r in db.scalars(select(AgentRole)).all()
            if r.key not in {"inspector_general", "financial_controller", "compliance_privacy"}
        ]
    stop_heartbeat = asyncio.Event()

    async def heartbeat():
        while not stop_heartbeat.is_set():
            activity.heartbeat(run_id)
            with Session.begin() as db:
                t = db.get(Task, task_id)
                o = db.get(Organization, org_id)
                if t.status != "running" or o.stopped or db.get(Project, t.project_id).paused:
                    raise ApplicationError("Execution revoked", non_retryable=True)
                t.lease_until = now() + timedelta(seconds=60)
            try:
                await asyncio.wait_for(stop_heartbeat.wait(), timeout=10)
            except TimeoutError:
                pass

    async def work():
        store = await asyncio.to_thread(ArtifactStore)
        if coding:
            github = GitHubProvider()
            checkout = await asyncio.to_thread(github.checkout)
            factory = DaytonaFactory()

            def register(sandbox_id):
                with Session.begin() as db:
                    db.add(
                        Sandboxes(
                            organization_id=org_id,
                            data={"run_id": run_id, "provider_id": sandbox_id, "state": "running"},
                        )
                    )
                    db.get(AgentRun, run_id).provider_run_id = sandbox_id

            exported = await asyncio.to_thread(
                factory.build,
                run_id,
                {"objective": objective, "model": settings().codex_model},
                checkout,
                register,
                organization_id=org_id,
            )
            report = await asyncio.to_thread(factory.qa, run_id, checkout, exported, register)
            # Re-check authoritative execution policy before creating any external PR.
            with Session.begin() as db:
                authorize(db, org_id, "sandbox_build", "", "")
                if (
                    db.get(Task, task_id).status != "running"
                    or db.get(Project, db.get(Task, task_id).project_id).paused
                ):
                    raise IntegrationBlocked("Execution revoked before PR creation")
            pr = await asyncio.to_thread(
                github.draft_pr,
                task_id,
                exported["base_sha"],
                exported["base_branch"],
                exported["files"],
                report,
            )
            result = {"export": exported, "qa": report, "pr": pr}
            kind = "verified_pull_request"
            with Session() as db:
                calls = db.scalars(select(ToolCalls).where(ToolCalls.organization_id == org_id)).all()
                own = [c for c in calls if c.data.get("run_id") == run_id]
                if not own or any(not c.data.get("usage") for c in own):
                    raise IntegrationBlocked("Model usage unknown; reservation retained for reconciliation")
                usage = {
                    "input_tokens": sum(c.data["usage"].get("input_tokens", 0) for c in own),
                    "output_tokens": sum(c.data["usage"].get("output_tokens", 0) for c in own),
                }
        elif role == "chief_of_staff":
            result, usage = await plan_goal(objective, accepted_roles)
            kind = "project_plan"
        else:
            result, usage = await specialist(role, objective)
            kind = "specialist_report"
        uri, checksum = await asyncio.to_thread(store.put, org_id, task_id, kind, result)
        with Session.begin() as db:
            task = db.get(Task, task_id)
            org = lock_org(db, org_id)
            if org.stopped or task.status != "running":
                raise IntegrationBlocked("Execution revoked; artifact retained for review")
            artifact = Artifact(
                organization_id=org_id,
                task_id=task_id,
                kind=kind,
                uri=uri,
                sha256=checksum,
                verified=True,
                details={
                    "verification": "store_checksum_and_schema" if not coding else "independent_hosted_QA",
                    "limitations": []
                    if coding
                    else ["Document schema verified; business claims require independent evidence review"],
                },
            )
            db.add(artifact)
            db.flush()
            if role == "chief_of_staff":
                children = []
                for item in result["tasks"]:
                    child = Task(
                        organization_id=org_id,
                        project_id=task.project_id,
                        title=item["title"],
                        objective=item["objective"],
                        agent_role=item["role"],
                        acceptance=item["acceptance"],
                        expected_artifacts=["specialist_report"],
                    )
                    db.add(child)
                    db.flush()
                    children.append(child)
                    for dependency in item["depends_on"]:
                        db.add(
                            TaskDependency(
                                organization_id=org_id,
                                task_id=child.id,
                                depends_on_id=children[dependency].id,
                            )
                        )
                    emit(
                        db,
                        org_id,
                        "task",
                        child.id,
                        "task.created",
                        {"title": child.title, "delegated_by": task.id, "agent_role": child.agent_role},
                    )
            run = db.get(AgentRun, run_id)
            run.status = "completed"
            run.usage = usage
            run.completed_at = now()
            reservation = db.scalar(select(Reservation).where(Reservation.run_id == run_id))
            attributed_model_cost = (
                Decimal(usage["provider_billed_usd"]) * Decimal(str(settings().thb_per_usd))
                if "provider_billed_usd" in usage
                else token_cost(usage["input_tokens"], usage["output_tokens"], coding=coding)
            )
            reconcile(
                db,
                reservation,
                attributed_model_cost
                + (Decimal(str(settings().sandbox_thb_per_minute)) * 20 if coding else 0),
                settings().codex_provider if coding else settings().model_provider,
                {
                    **usage,
                    "fx_thb_per_usd": settings().thb_per_usd,
                    "fx_observed_at": settings().fx_observed_at,
                    "sandbox_minutes_reserved_estimate": 20 if coding else 0,
                },
                estimated=True,
            )
            transition(db, task, "reviewing")
            if coding or role == "chief_of_staff":
                transition(db, task, "completed")
            else:
                # Never self-certify a specialist's factual output.
                task.status = "waiting_for_approval"
                inbox(
                    db,
                    org_id,
                    "Review specialist evidence",
                    f"Task {task.title} produced {uri}; checksum {checksum}. Schema and storage integrity verified. Factual claims await independent review.",
                    dedupe="review:" + task.id,
                )
                emit(db, org_id, "task", task.id, "task.review_required", {"artifact_id": artifact.id})
            task.lease_until = None
            task.checkpoint = {"stage": "delivered", "artifact_id": artifact.id}
            emit(
                db,
                org_id,
                "artifact",
                artifact.id,
                "artifact.verified",
                {"kind": kind, "sha256": checksum, "uri": uri},
            )
            return {"status": task.status, "artifact_id": artifact.id}

    h = asyncio.create_task(heartbeat())
    w = asyncio.create_task(work())
    try:
        done, _ = await asyncio.wait([h, w], return_when=asyncio.FIRST_COMPLETED)
        if h in done:
            await h
        return await w
    except Exception as error:
        w.cancel()
        with Session.begin() as db:
            task = db.get(Task, task_id)
            run = db.get(AgentRun, run_id)
            if task.status not in TERMINAL:
                task.status = "blocked"
            task.error = redact(type(error).__name__ + ": " + str(error))[:1000]
            run.status = "failed"
            run.completed_at = now()
            inbox(
                db,
                org_id,
                "Execution blocked — review required",
                task.error + " Budget reservation retained until usage is reconciled.",
                dedupe="execution:" + run_id,
            )
            emit(
                db, org_id, "task", task.id, "task.execution_blocked", {"error": task.error, "run_id": run_id}
            )
        raise ApplicationError("Run blocked; inspect Founder Inbox", non_retryable=True) from error
    finally:
        stop_heartbeat.set()
        h.cancel()
        await asyncio.gather(h, return_exceptions=True)


@workflow.defn
class TaskWorkflow:
    @workflow.run
    async def run(self, task_id: str):
        for _ in range(96):  # bounded 24-hour dependency/owner wait window
            result = await workflow.execute_activity(
                execute_task,
                task_id,
                start_to_close_timeout=timedelta(minutes=15),
                heartbeat_timeout=timedelta(seconds=45),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
            if result["status"] not in {"dependency_wait", "paused"}:
                return result
            await workflow.sleep(timedelta(minutes=15))
        return {"status": "wait_window_expired"}
