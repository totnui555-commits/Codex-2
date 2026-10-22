import asyncio

from temporalio.client import Client


async def main():
    for attempt in range(30):
        try:
            # Avoid creating native SDK clients while the server port is still closed.
            _, writer = await asyncio.wait_for(asyncio.open_connection("localhost", 7233), timeout=1)
            writer.close()
            await writer.wait_closed()
            client = await Client.connect("localhost:7233")
            await client.service_client.check_health()
            return
        except (RuntimeError, OSError, TimeoutError):
            if attempt == 29:
                raise
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
