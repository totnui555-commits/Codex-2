import asyncio
import json
from pathlib import Path

import httpx


async def main():
    credentials = json.loads(Path(".local/owner-credentials.json").read_text())
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=15) as client:
        login = await client.post(
            "/auth/login", json={"email": credentials["email"], "password": credentials["password"]}
        )
        login.raise_for_status()
        before = (await client.get("/snapshot")).json()
        project = await client.post(
            "/projects",
            json={
                "name": "Event reconnect verification",
                "description": "Actual integration check of persistent event replay after an authenticated reconnect.",
            },
        )
        project.raise_for_status()
        async with client.stream("GET", "/events", params={"after": before["cursor"]}) as stream:
            async for line in stream.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    assert event["event_type"] == "project.created"
                    assert event["aggregate_id"] == project.json()["id"]
                    cursor = event["cursor"]
                    break
        # Reconnect with the delivered cursor: no previously delivered event is returned by history.
        replay = await client.get("/events/history", params={"after": cursor})
        replay.raise_for_status()
        assert all(e["cursor"] > cursor for e in replay.json())
        integrity = (await client.get("/audit/verify")).json()
        assert integrity["valid"]
        Path("docs/evidence/events-reconnect.json").write_text(
            json.dumps(
                {
                    "sse_delivered_event_id": event["event_id"],
                    "cursor": cursor,
                    "replay_after_cursor_excludes_previous": True,
                    "audit_valid": True,
                },
                indent=2,
            )
            + "\n"
        )
        print("Authenticated live SSE, cursor replay and audit integrity verified.")


if __name__ == "__main__":
    asyncio.run(main())
