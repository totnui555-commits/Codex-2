import asyncio

from temporalio.client import Client


async def main():
    for attempt in range(30):
        try:
            client = await Client.connect("localhost:7233")
            await client.service_client.check_health()
            return
        except (RuntimeError, OSError):
            if attempt == 29:
                raise
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
