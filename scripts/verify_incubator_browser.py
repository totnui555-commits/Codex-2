"""Exercise real UI persistence with an explicitly internal, zero-observation experiment."""

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

credentials = json.loads(Path(".local/owner-credentials.json").read_text())
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1512, "height": 1100})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=120000)
    page.get_by_label("Email", exact=True).fill(credentials["email"])
    page.get_by_label("Password", exact=True).fill(credentials["password"])
    page.get_by_role("button", name="Enter mission control").click()
    page.get_by_role("heading", name="Kingdom", exact=True).wait_for(timeout=120000)
    page.get_by_role("button", name="Opportunities", exact=True).click()
    section = page.get_by_role("region", name="Product Incubator")
    section.get_by_text("Define an experiment", exact=True).click()
    title = "Internal UI persistence verification " + str(int(time.time()))
    section.get_by_label("Experiment title", exact=True).fill(title)
    section.get_by_label("Hypothesis", exact=True).fill(
        "The owner can record a draft and retrieve the same criteria after reloading. Internal platform verification, not customer research."
    )
    section.get_by_label("Success metric", exact=True).fill("Owner completes evidence review flow")
    section.get_by_role("button", name="Save draft experiment").click()
    section.get_by_role("heading", name=title, exact=True).wait_for()
    page.reload(wait_until="networkidle")
    section = page.get_by_role("region", name="Product Incubator")
    card = section.locator("article").filter(has=page.get_by_role("heading", name=title, exact=True))
    card.get_by_text("draft", exact=True).wait_for()
    card.get_by_role("button", name="Open evidence collection").click()
    card.get_by_text("running", exact=True).wait_for()
    card.get_by_role("button", name="Pause", exact=True).click()
    card.get_by_text("paused", exact=True).wait_for()
    card.get_by_role("button", name="Conclude and freeze", exact=True).click()
    card.get_by_text("concluded", exact=True).wait_for()
    assert card.get_by_text("inconclusive", exact=True).is_visible()
    card.get_by_role("button", name="View evidence receipts").click()
    assert not card.get_by_role("button", name="Open evidence collection").count()
    page.screenshot(path="docs/evidence/incubator-desktop.png", full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path="docs/evidence/incubator-mobile.png", full_page=True)
    assert page.locator("body").evaluate("(e) => e.scrollWidth") <= 390
    snapshot = page.evaluate("async () => (await fetch('/api/snapshot')).json()")
    experiment = next(e for e in snapshot["experiments"] if e["data"]["title"] == title)
    assert experiment["data"]["statistics"]["samples"] == 0
    assert snapshot["organization"]["paid_execution_authorized"] is False
    audit = page.evaluate("async () => (await fetch('/api/audit/verify')).json()")
    assert audit["valid"] is True
    browser.close()
    Path("docs/evidence/incubator-browser-check.json").write_text(
        json.dumps(
            {
                "checks": [
                    "authenticated_ui_create",
                    "reload_persistence",
                    "start_pause_conclude",
                    "zero_observations_inconclusive",
                    "concluded_experiment_frozen",
                    "audit_chain_valid",
                    "paid_execution_stays_disabled",
                    "mobile_no_overflow",
                ],
                "experiment_id": experiment["id"],
                "experiment_title": title,
                "evidence_class": "internal_platform_verification_not_customer_research",
                "customer_observations": 0,
                "browser_errors": errors,
            },
            indent=2,
        )
        + "\n"
    )
    assert not errors, errors
    print("Incubator browser persistence and lifecycle verified; zero customer observations.")
