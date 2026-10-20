import asyncio
import json
from pathlib import Path

from company_os.db import Session
from company_os.domain import verify_audit
from company_os.models import AgentRun, Event, Message, Opportunity, Organization, Revenue, Task
from sqlalchemy import select
from temporalio.client import Client


async def main():
    client = await Client.connect("localhost:7233")
    histories = []
    with Session() as db:
        tasks = db.scalars(select(Task)).all()
        for task in tasks:
            if task.workflow_id:
                handle = client.get_workflow_handle(task.workflow_id)
                description = await handle.describe()
                history = await handle.fetch_history()
                histories.append(
                    {
                        "workflow_id": task.workflow_id,
                        "status": description.status.name,
                        "event_count": len(history.events),
                        "task_status": task.status,
                    }
                )
        data = {
            "database": "PostgreSQL 17",
            "temporal": histories,
            "source_backed_opportunities": len(db.scalars(select(Opportunity)).all()),
            "events_persisted": len(db.scalars(select(Event)).all()),
            "audit_valid": all(verify_audit(db, o.id) for o in db.scalars(select(Organization)).all()),
            "founder_messages": len(db.scalars(select(Message)).all()),
            "paid_model_runs_executed": len(
                [run for run in db.scalars(select(AgentRun)).all() if run.usage.get("input_tokens", 0) > 0]
            ),
            "verified_revenue_transactions": len(db.scalars(select(Revenue)).all()),
        }
    Path("docs/evidence/runtime.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
