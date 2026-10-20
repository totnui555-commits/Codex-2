import asyncio
import logging
from datetime import timedelta

from sqlalchemy import select
from temporalio.client import Client
from temporalio.exceptions import WorkflowAlreadyStartedError

from .db import Session
from .health import service_heartbeat
from .models import Decisions, Event, Organization, Outbox, Task, now
from .notifications import deliver_pending
from .orchestration import TaskWorkflow
from .research import public_source_research, store_research
from .settings import settings

log = logging.getLogger(__name__)


async def dispatch(client):
    # Stable IDs and Temporal's workflow uniqueness protect crash/retry boundaries.
    with Session.begin() as db:
        rows = db.scalars(
            select(Outbox)
            .where(Outbox.state == "pending", Outbox.next_attempt_at <= now())
            .with_for_update(skip_locked=True)
            .limit(50)
        ).all()
        for row in rows:
            event = db.get(Event, row.event_id)
            if event.event_type in {"task.created", "task.status_changed"}:
                task = db.get(Task, event.aggregate_id)
                if task and task.status == "ready" and not db.get(Organization, task.organization_id).stopped:
                    workflow_id = f"task-{task.id}-attempt-{task.attempts}"
                    try:
                        await client.start_workflow(
                            TaskWorkflow.run, task.id, id=workflow_id, task_queue="company-os"
                        )
                        task.workflow_id = workflow_id
                    except WorkflowAlreadyStartedError:
                        pass
                    except Exception:
                        row.attempts += 1
                        row.next_attempt_at = now() + timedelta(seconds=min(300, 2**row.attempts))
                        if row.attempts >= 5:
                            row.state = "dead_letter"
                        continue
            row.state = "delivered"


async def daily_research():
    # Database checkpoint survives process restarts and browser closure.
    day = now().date().isoformat()
    with Session() as db:
        orgs = [o.id for o in db.scalars(select(Organization).where(Organization.stopped.is_(False))).all()]
    for org_id in orgs:
        with Session.begin() as db:
            from .domain import emit, lock_org

            lock_org(db, org_id)
            done = db.scalars(select(Decisions).where(Decisions.organization_id == org_id)).all()
            if any(d.data.get("daily_research") == day for d in done):
                continue
            # Bounded public source request; no paid model or external outreach.
            sources = await public_source_research()
            store_research(db, org_id, sources)
            db.add(
                Decisions(organization_id=org_id, data={"daily_research": day, "source_count": len(sources)})
            )
            emit(
                db, org_id, "organization", org_id, "research.daily_completed", {"source_count": len(sources)}
            )


async def main():
    logging.basicConfig(level=logging.INFO)
    client = await Client.connect(settings().temporal_address, namespace=settings().temporal_namespace)
    while True:
        service_heartbeat("scheduler")
        for operation in [lambda: dispatch(client), deliver_pending, daily_research]:
            try:
                await operation()
            except Exception as e:
                log.warning("Background operation failed: %s", type(e).__name__)
        await asyncio.sleep(settings().worker_poll_seconds)


if __name__ == "__main__":
    asyncio.run(main())
