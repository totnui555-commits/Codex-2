import os
import pytest
from temporalio.client import Client
from temporalio.worker import Worker
from company_os.orchestration import TaskWorkflow, execute_task
from company_os.db import Session
from company_os.models import Task
from conftest import create_task


@pytest.mark.skipif(
    os.getenv("RUN_TEMPORAL_TESTS") != "1",
    reason="Set RUN_TEMPORAL_TESTS=1 with the real Temporal service running",
)
async def test_real_temporal_worker_fails_closed_without_providers(owner_client, project):
    task = create_task(owner_client, project, agent_role="backend_engineer")
    client = await Client.connect("localhost:7233")
    async with Worker(
        client, task_queue="company-os-tests", workflows=[TaskWorkflow], activities=[execute_task]
    ):
        result = await client.execute_workflow(
            TaskWorkflow.run, task["id"], id="test-" + task["id"], task_queue="company-os-tests"
        )
    assert result["status"] == "blocked"
    assert "OpenAI model credentials" in result["missing"]
    with Session() as db:
        assert db.get(Task, task["id"]).status == "blocked"
        assert db.get(Task, task["id"]).attempts == 0
