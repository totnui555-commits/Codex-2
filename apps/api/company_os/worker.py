import asyncio

from temporalio.worker import Worker

from .health import service_heartbeat
from .orchestration import TaskWorkflow, execute_task
from .temporal_connection import connect_temporal


async def main():
    client = await connect_temporal()
    worker = Worker(
        client,
        task_queue="company-os",
        workflows=[TaskWorkflow],
        activities=[execute_task],
        max_concurrent_activities=2,
    )

    async def heartbeat():
        while True:
            service_heartbeat("worker")
            await asyncio.sleep(15)

    await asyncio.gather(worker.run(), heartbeat())


if __name__ == "__main__":
    asyncio.run(main())
