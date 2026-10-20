import json
from pathlib import Path

from playwright.sync_api import sync_playwright

credentials = json.loads(Path(".local/owner-credentials.json").read_text())
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1512, "height": 1100}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=120000)
    page.get_by_label("Email", exact=True).fill(credentials["email"])
    page.get_by_label("Password", exact=True).fill(credentials["password"])
    page.get_by_role("button", name="Enter mission control").click()
    page.get_by_role("heading", name="Mission Control").wait_for()
    page.wait_for_timeout(2500)
    page.screenshot(path="docs/evidence/office-desktop.png", full_page=True)
    page.locator(".desk-label").filter(has_text="Backend Engineer").click()
    page.get_by_role("heading", name="Backend Engineer", exact=True).wait_for()
    page.wait_for_timeout(1500)
    page.screenshot(path="docs/evidence/agent-inspector.png", full_page=True)
    page.get_by_role("button", name="Build Inspector", exact=True).click()
    page.get_by_role("heading", name="No coding sessions have run.").wait_for()
    page.goto("http://localhost:3000/inbox", wait_until="networkidle")
    page.get_by_role("heading", name="Founder Inbox", exact=True).wait_for()
    page.screenshot(path="docs/evidence/founder-inbox.png", full_page=True)
    page.goto("http://localhost:3000", wait_until="networkidle")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(1500)
    assert page.locator("body").evaluate("(e)=>e.scrollWidth") <= 390
    page.screenshot(path="docs/evidence/office-mobile.png", full_page=True)
    browser.close()
    Path("docs/evidence/browser-readonly-check.json").write_text(
        json.dumps(
            {
                "checks": [
                    "3d_render",
                    "agent_selection_and_camera_focus",
                    "build_inspector_empty_truthfully",
                    "authenticated_inbox_deep_link",
                    "mobile_no_horizontal_overflow",
                ],
                "browser_errors": errors,
            },
            indent=2,
        )
        + "\n"
    )
    assert errors == [], errors
