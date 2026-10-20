import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

creds = json.loads(Path(".local/owner-credentials.json").read_text())
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1512, "height": 1100}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=120000)
    page.get_by_label("Email", exact=True).fill(creds["email"])
    page.get_by_label("Password", exact=True).fill(creds["password"])
    page.get_by_role("button", name="Enter mission control").click()
    page.get_by_role("heading", name="Mission Control").wait_for(timeout=120000)
    page.wait_for_timeout(8000)
    page.screenshot(path="docs/evidence/office-desktop.png", full_page=True)
    page.get_by_role("button", name="2D view", exact=True).click()
    page.get_by_role("button", name="02 Quality & Watchtower").click()
    assert page.get_by_role("heading", name="Quality & Watchtower").is_visible()
    page.get_by_role("button", name="3D Office view").count()
    page.get_by_role("button", name=re.compile(r"^Founder Inbox")).click()
    page.get_by_role("heading", name="Connect providers to activate the workforce").wait_for()
    page.screenshot(path="docs/evidence/founder-inbox.png", full_page=True)
    project_name = "Platform verification " + str(int(time.time()))
    page.get_by_role("button", name="New project", exact=True).click()
    page.get_by_label("Project name", exact=True).fill(project_name)
    page.get_by_label("Goal & context", exact=True).fill(
        "Verify persistent management, authenticated events, durable blocked-provider handling and live office synchronization."
    )
    page.get_by_role("button", name="Create project", exact=True).click()
    page.get_by_role("dialog").wait_for(state="hidden")
    page.get_by_role("button", name="Projects", exact=True).click()
    page.get_by_role("heading", name=project_name, exact=True).wait_for()
    page.get_by_role("button", name="Tasks", exact=True).click()
    page.get_by_role("button", name="Create task", exact=True).click()
    page.locator("select[name=project]").select_option(label=project_name)
    page.get_by_label("Task title", exact=True).fill("Verify real hosted coding readiness")
    page.get_by_label("Objective", exact=True).fill(
        "Check secure provider readiness before running the documented CRUD benchmark in a hosted sandbox."
    )
    page.get_by_label("Acceptance criteria · one per line").fill(
        "Execute real Codex worker in isolated sandbox\nIndependent CRUD tests pass\nPublish a draft PR with checksummed evidence"
    )
    page.locator("select[name=role]").select_option("backend_engineer")
    page.get_by_role("button", name="Create task", exact=True).last.click()
    page.get_by_role("dialog").wait_for(state="hidden")
    page.get_by_role("heading", name="Verify real hosted coding readiness", exact=True).last.wait_for()
    page.screenshot(path="docs/evidence/task-backlog.png", full_page=True)
    page.locator("nav").get_by_role("button", name=re.compile(r"^Office")).click()
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(2000)
    page.screenshot(path="docs/evidence/office-mobile.png", full_page=True)
    assert page.locator("body").evaluate("(e)=>e.scrollWidth") <= 390
    Path("docs/evidence/browser-check.json").write_text(
        json.dumps(
            {
                "checks": [
                    "owner_login",
                    "real_office_render",
                    "2d_floor_selection",
                    "persistent_inbox",
                    "project_create",
                    "task_create",
                    "mobile_no_overflow",
                ],
                "browser_errors": errors,
            },
            indent=2,
        )
    )
    browser.close()
    assert not errors, errors
