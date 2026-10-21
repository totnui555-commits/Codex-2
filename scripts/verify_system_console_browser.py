"""Read-only browser acceptance against the real local API; no mutations or inference."""

import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
evidence = root / "docs/evidence"
creds = json.loads((root / ".local/owner-credentials.json").read_text())
errors = []
checks = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--enable-unsafe-swiftshader"])
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    response = context.request.post(
        "http://localhost:3000/api/auth/login", data={k: creds[k] for k in ("email", "password")}
    )
    assert response.ok
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://localhost:3000/overview", wait_until="domcontentloaded", timeout=120000)
    page.locator(".console-mode").wait_for(timeout=60000)
    for name in [
        "Overview",
        "Projects",
        "Tasks",
        "Agents",
        "Opportunities",
        "Watchtower",
        "Approvals",
        "Founder Inbox",
        "Finance",
        "Build Inspector",
        "Audit",
    ]:
        page.locator(".sidebar nav").get_by_role(
            "button", name=re.compile("^" + re.escape(name) + r"(?:\s|$)")
        ).click()
        page.wait_for_timeout(200)
        assert page.locator(".console-mode").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), name
        if name in ["Overview", "Projects", "Agents", "Finance"]:
            page.screenshot(path=str(evidence / ("system-console-" + name.lower() + ".png")), timeout=60000)
        checks.append("desktop_" + name)
    page.locator(".settings-link").click()
    page.get_by_role("heading", name=re.compile(r"^Settings"), level=1).wait_for()
    page.screenshot(path=str(evidence / "system-console-settings.png"))
    checks.append("settings_forms_preserved")
    page.get_by_role("button", name="New project", exact=True).click()
    page.get_by_role("dialog").wait_for()
    page.get_by_role("dialog").get_by_role("textbox").first.focus()
    assert page.evaluate("getComputedStyle(document.activeElement).outlineStyle") == "solid"
    page.screenshot(path=str(evidence / "system-console-dialog.png"))
    page.get_by_role("button", name="Close dialog", exact=True).click()
    checks.append("modal_keyboard_focus")
    page.locator(".sidebar nav").get_by_role("button", name="Office", exact=False).click()
    page.locator(".office-layout").wait_for()
    page.wait_for_timeout(3000)
    page.screenshot(path=str(evidence / "system-console-office.png"), timeout=60000)
    checks.append("office_scene_preserved")
    page.set_viewport_size({"width": 390, "height": 844})
    for route in [
        "overview",
        "projects",
        "agents",
        "tasks",
        "finance",
        "settings",
        "inbox",
        "opportunities",
        "watchtower",
        "approvals",
        "audit",
        "build-inspector",
        "office",
    ]:
        page.goto("http://localhost:3000/" + route, wait_until="domcontentloaded", timeout=120000)
        page.locator(".console-mode").wait_for(timeout=60000)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), route
        if route == "overview":
            page.screenshot(path=str(evidence / "system-console-mobile.png"))
        if route == "settings":
            page.screenshot(path=str(evidence / "system-console-mobile-settings.png"))
        checks.append("mobile_" + route)
    page.get_by_role("button", name="Open navigation", exact=True).click()
    assert page.locator(".sidebar").is_visible()
    page.locator(".sidebar nav").get_by_role("button", name="Projects", exact=True).click()
    assert not page.locator(".sidebar").is_visible()
    checks.append("mobile_navigation")
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto("http://localhost:3000", wait_until="domcontentloaded", timeout=120000)
    page.locator(".kingdom-mode").wait_for(timeout=60000)
    assert page.locator(".kingdom-mode .sidebar").is_visible()
    assert (
        page.evaluate('getComputedStyle(document.querySelector(".kingdom-mode .sidebar")).width') == "184px"
    )
    checks.append("kingdom_shell_scope_preserved")
    anonymous = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    login = anonymous.new_page()
    login.on("pageerror", lambda e: errors.append(str(e)))
    login.goto("http://localhost:3000/overview", wait_until="domcontentloaded", timeout=120000)
    login.locator(".system-login").wait_for()
    login.screenshot(path=str(evidence / "system-console-login.png"))
    login.get_by_role("button", name="First time here? Initialize installation", exact=True).click()
    login.get_by_label("Installation setup token", exact=True).wait_for()
    assert login.get_by_label("Installation setup token", exact=True).get_attribute("type") == "password"
    checks.append("login_and_private_setup_fields")
    login.set_viewport_size({"width": 390, "height": 844})
    assert login.evaluate("document.documentElement.scrollWidth <= innerWidth")
    login.screenshot(path=str(evidence / "system-console-mobile-setup.png"))
    checks.append("mobile_setup_no_overflow")
    assert not errors, errors
    (evidence / "system-console-browser.json").write_text(
        json.dumps(
            {
                "checks": checks,
                "page_errors": errors,
                "database_mutations": 0,
                "model_calls": 0,
                "viewports": [[1440, 1000], [390, 844]],
                "mode": "real authenticated local API and PostgreSQL",
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"checks_passed": len(checks), "page_errors": errors}), flush=True)
    browser.close()
