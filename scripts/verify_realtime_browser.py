"""Verify unbuffered company events through Next's real proxy, with always-on cleanup."""

import json
import time
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import sync_playwright


def main():
    root = Path(__file__).resolve().parents[1]
    credentials = json.loads((root / ".local/owner-credentials.json").read_text())
    errors, streams = [], []
    receipt = {
        "checks": [],
        "model_calls": 0,
        "scope": "Real local PostgreSQL/API and Next proxy; internal paused project only",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1200, "height": 900})
        http = context.request
        origin = "http://localhost:3000"
        assert http.post(
            origin + "/api/auth/login", data={k: credentials[k] for k in ("email", "password")}
        ).ok
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))

        def response(r):
            if "/api/events?" in r.url:
                streams.append(
                    {key: r.headers.get(key) for key in ["cache-control", "content-encoding", "content-type"]}
                )

        page.on("response", response)
        page.goto(origin + "/tasks", wait_until="domcontentloaded")
        page.locator(".console-mode").wait_for()
        project = task = None
        try:
            page.evaluate("""async()=>{
              const s=await(await fetch('/api/snapshot')).json();
              window.eventEvidence=[];
              window.eventProbe=new EventSource('/api/events?after='+s.cursor);
              window.eventProbe.addEventListener('company',e=>{const d=JSON.parse(e.data);window.eventEvidence.push({type:d.event_type,id:d.aggregate_id});});
              await new Promise((resolve,reject)=>{window.eventProbe.onopen=resolve;window.eventProbe.onerror=()=>reject(Error('Event stream unavailable'));});
            }""")
            created = http.post(
                origin + "/api/projects",
                data={
                    "name": "Internal realtime verification " + uuid4().hex[:8],
                    "description": "Paused internal acceptance only; no model execution",
                },
            )
            assert created.ok
            project = created.json()
            assert http.patch(origin + "/api/projects/" + project["id"], data={"paused": True}).ok
            started = time.monotonic()
            created = http.post(
                origin + "/api/tasks",
                data={
                    "project_id": project["id"],
                    "title": "Verify live event delivery " + uuid4().hex[:8],
                    "objective": "Internal zero-cost stream verification",
                    "agent_role": "backend_engineer",
                    "acceptance": ["Real company event and visible task before polling fallback"],
                },
            )
            assert created.ok
            task = created.json()
            page.wait_for_function(
                'id=>window.eventEvidence.some(e=>e.type==="task.created"&&e.id===id)',
                arg=task["id"],
                timeout=12000,
            )
            page.get_by_text(task["title"], exact=True).wait_for(timeout=12000)
            elapsed = time.monotonic() - started
            assert elapsed < 12, "Cannot claim realtime visibility after polling fallback"
            assert streams and all(
                "no-transform" in (s["cache-control"] or "")
                and s["content-encoding"] not in ("gzip", "br", "deflate")
                for s in streams
            )
            page.reload(wait_until="domcontentloaded")
            page.get_by_text(task["title"], exact=True).wait_for()
            assert not errors, errors
            receipt.update(
                {
                    "checks": [
                        "real_task_created_event_received",
                        "ui_updates_before_30s_poll",
                        "sse_no_transform_through_proxy",
                        "sse_uncompressed",
                        "reload_persistence",
                    ],
                    "visibility_seconds": round(elapsed, 3),
                    "task_id": task["id"],
                    "stream_headers": streams,
                    "page_errors": errors,
                }
            )
        finally:
            if task:
                cancelled = http.post(origin + "/api/tasks/" + task["id"] + "/cancel")
                receipt["task_cancelled"] = cancelled.ok and cancelled.json()["status"] == "cancelled"
            if project:
                paused = http.patch(origin + "/api/projects/" + project["id"], data={"paused": True})
                receipt["project_paused"] = paused.ok and paused.json()["paused"] is True
            try:
                page.evaluate("window.eventProbe?.close()")
            finally:
                browser.close()
                (root / "docs/evidence/realtime-browser.json").write_text(
                    json.dumps(receipt, indent=2) + "\n"
                )
    print(
        json.dumps(
            {
                "checks_passed": len(receipt["checks"]),
                "visibility_seconds": receipt.get("visibility_seconds"),
                "cleanup": receipt.get("task_cancelled") and receipt.get("project_paused"),
            }
        )
    )


if __name__ == "__main__":
    main()
