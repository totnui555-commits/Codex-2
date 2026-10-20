"""Real authenticated Kingdom acceptance; never fabricates a running agent or incident."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    credentials = json.loads(Path(".local/owner-credentials.json").read_text())
    evidence = Path("docs/evidence")
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--enable-unsafe-swiftshader"])
        context = browser.new_context(
            viewport={"width": 1700, "height": 1250},
        )
        response = context.request.post(
            "http://localhost:3000/api/auth/login", data={k: credentials[k] for k in ("email", "password")}
        )
        assert response.ok
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("http://localhost:3000", wait_until="domcontentloaded", timeout=120000)
        page.get_by_role("heading", name="Kingdom", exact=True).wait_for(timeout=60000)
        world = page.get_by_role("region", name="Kingdom Edition", exact=True)
        page.locator('[data-world-rendered="true"]').wait_for(timeout=60000)
        page.wait_for_function("window.__kingdomDiagnostics?.citizens > 0", timeout=60000)
        world.get_by_role("button", name="Display settings", exact=True).click()
        world.get_by_role("checkbox", name="Reduced motion").check()
        world.get_by_role("button", name="Display settings", exact=True).click()
        page.wait_for_timeout(1800)

        def screenshot(name, selector=".kingdom-layout"):
            element = page.locator(selector)
            element.scroll_into_view_if_needed(timeout=60000)
            box = element.bounding_box()
            assert box
            page.screenshot(path=str(evidence / name), clip=box, timeout=60000)

        assert world.locator(".kingdom-world canvas").is_visible(), (
            "3D context unavailable; cannot claim a rendered screenshot"
        )
        screenshot("kingdom-apple-desktop.png")
        canvas_box = world.locator(".kingdom-world canvas").bounding_box()
        assert canvas_box and canvas_box["width"] == 1700 and canvas_box["height"] == 1250
        search = world.get_by_role("searchbox", name="Search kingdom", exact=True)
        search.fill("Treasury")
        world.locator(".kingdom-search-results").get_by_role(
            "button", name="Royal Treasury", exact=False
        ).click()
        world.get_by_role("heading", name="Royal Treasury", exact=True).wait_for()
        search.fill("no-such-landmark-729")
        world.get_by_text("No landmarks or citizens found.", exact=True).wait_for()
        search.press("Escape")
        search.fill("Backend Engineer")
        search.press("Enter")
        world.get_by_role("heading", name="Backend Engineer", exact=True).wait_for()
        search.press("Escape")
        world.get_by_role("button", name="Focus on island", exact=True).click()
        assert not page.locator(".sidebar").is_visible()
        assert not world.get_by_role("complementary", name="Kingdom inspector").is_visible()
        screenshot("kingdom-apple-focus.png")
        page.keyboard.press("Escape")
        assert page.locator(".sidebar").is_visible()
        print("3D overview captured", flush=True)
        diagnostics = page.evaluate("window.__kingdomDiagnostics")
        print(json.dumps(diagnostics), flush=True)
        world.get_by_role("button", name="Display settings", exact=True).click()
        world.get_by_role("combobox", name="Kingdom render quality").select_option("low")
        world.get_by_role("button", name="Display settings", exact=True).click()
        directory = page.get_by_role("navigation", name="Kingdom landmarks")
        for title in [
            "Royal Keep",
            "Adventurers’ Guild",
            "Inventors’ Workshop",
            "Artisans’ Atelier",
            "Alchemists’ Laboratory",
            "Harbor Market",
            "Royal Treasury",
            "Watchtower Lighthouse",
            "Great Library",
            "Royal Post Office",
            "Harbor Shipyard",
            "Village Commons",
        ]:
            print("Inspecting " + title, flush=True)
            world.get_by_role("button", name="Toggle landmark directory", exact=True).click()
            directory.get_by_role("button", name=title, exact=False).click()
            page.get_by_role("complementary", name="Kingdom inspector").get_by_role(
                "heading", name=title, exact=True
            ).wait_for()
        world.get_by_role("button", name="Toggle landmark directory", exact=True).click()
        directory.get_by_role("button", name="Watchtower Lighthouse", exact=False).click()
        inspector = page.get_by_role("complementary", name="Kingdom inspector")
        snapshot = page.evaluate("async()=>(await fetch('/api/snapshot')).json()")
        open_incidents = [i for i in snapshot["incidents"] if i["state"] == "open"]
        assert str(len(open_incidents)) + " open incidents" in inspector.inner_text()
        screenshot("kingdom-apple-lighthouse.png")
        inspector.get_by_role("button", name="Open Watchtower", exact=False).click()
        page.get_by_role("heading", name="Watchtower", exact=True, level=1).wait_for()
        page.get_by_role("button", name="Kingdom", exact=True).click()
        world = page.get_by_role("region", name="Kingdom Edition", exact=True)
        page.locator('[data-world-rendered="true"]').wait_for(timeout=60000)
        world.locator('[data-citizen="backend_engineer"]').click()
        inspector = page.get_by_role("complementary", name="Kingdom inspector")
        inspector.get_by_role("heading", name="Backend Engineer", exact=True).wait_for()
        assert "Citizen identity" in inspector.inner_text()
        screenshot("kingdom-apple-citizen.png")
        inspector.get_by_role("button", name="Follow citizen", exact=True).click()
        page.get_by_role("combobox", name="Kingdom camera preset").select_option(label="Harbor Market")
        page.get_by_role("button", name="Reset kingdom camera", exact=True).click()
        world.get_by_role("button", name="Accessible view", exact=True).click()
        world.get_by_role("heading", name="Your kingdom, at a glance").wait_for()
        screenshot("kingdom-apple-accessible.png")
        # A genuine zero-cost internal acceptance task creates an event, never a synthetic run.
        receipt = page.evaluate(
            """async()=>{const project=await fetch('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Kingdom UI integration acceptance',description:'Internal zero-cost event/reconnect verification; no model job, customer evidence or product work.'})});if(!project.ok)throw Error('project');const p=await project.json();const task=await fetch('/api/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_id:p.id,title:'Verify Kingdom quest event visibility '+Date.now(),objective:'Verify persistent task creation, authenticated event updates and reconnect without executing a paid agent.',agent_role:'backend_engineer',acceptance:['Task appears in authenticated project dashboard']})});if(!task.ok)throw Error('task');return {project:p,task:await task.json()};}"""
        )
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Tasks", exact=True).click()
        page.get_by_text(receipt["task"]["title"], exact=True).wait_for(timeout=15000)
        page.reload(wait_until="domcontentloaded")
        page.get_by_text(receipt["task"]["title"], exact=True).wait_for()
        cancelled = page.evaluate(
            """async(id)=>{const r=await fetch('/api/tasks/'+id+'/cancel',{method:'POST',headers:{'Content-Type':'application/json'}});return r.ok;}""",
            receipt["task"]["id"],
        )
        assert cancelled
        assert page.evaluate(
            """async(id)=>(await fetch('/api/projects/'+id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({paused:true})})).ok""",
            receipt["project"]["id"],
        )
        page.get_by_role("button", name="Office", exact=True).click()
        page.get_by_role("heading", name="Mission Control", exact=True).wait_for()
        page.locator(".office-canvas canvas").wait_for(timeout=15000) if page.locator(
            ".office-canvas"
        ).count() else page.locator(".scene canvas").wait_for(timeout=15000)
        page.get_by_role("button", name="Kingdom", exact=True).click()
        page.get_by_role("region", name="Kingdom Edition", exact=True).wait_for()
        page.set_viewport_size({"width": 390, "height": 844})
        world = page.get_by_role("region", name="Kingdom Edition", exact=True)
        page.locator('[data-world-rendered="true"]').wait_for(timeout=60000)
        world.get_by_role("button", name="Display settings", exact=True).click()
        world.get_by_role("combobox", name="Kingdom render quality").select_option("low")
        world.get_by_role("checkbox", name="Reduced motion").check()
        world.get_by_role("button", name="Display settings", exact=True).click()
        page.wait_for_timeout(1500)
        assert page.locator("body").evaluate("(e)=>e.scrollWidth") <= 390
        screenshot("kingdom-apple-mobile.png", ".kingdom-stage")
        assert not world.get_by_role("complementary", name="Kingdom inspector").is_visible()
        search = world.get_by_role("searchbox", name="Search kingdom", exact=True)
        search.fill("Lighthouse")
        world.locator(".kingdom-search-results").get_by_role(
            "button", name="Watchtower Lighthouse", exact=False
        ).click()
        world.get_by_role("complementary", name="Kingdom inspector").get_by_role(
            "heading", name="Watchtower Lighthouse", exact=True
        ).wait_for()
        page.screenshot(path=str(evidence / "kingdom-apple-mobile-inspector.png"))
        world.get_by_role("button", name="Close kingdom panel", exact=True).click()
        assert not world.get_by_role("complementary", name="Kingdom inspector").is_visible()
        audit = page.evaluate("async()=>(await fetch('/api/audit/verify')).json()")
        assert audit["valid"]
        final = page.evaluate("async()=>(await fetch('/api/snapshot')).json()")
        assert final["organization"]["paid_execution_authorized"] is False
        context.close()
        browser.close()
    result = {
        "scope": "actual authenticated local company; no hosted coding or invented execution",
        "checks": [
            "full_viewport_island",
            "landmark_and_citizen_search",
            "search_empty_state_and_keyboard",
            "focus_mode_and_escape_restore",
            "mobile_inspector_sheet",
            "twelve_interactive_landmarks",
            "real_watchtower_dashboard",
            "incident_count_matches_server",
            "persistent_citizen_inspector",
            "camera_presets_follow_reset",
            "accessible_fallback",
            "real_task_event_and_reload_persistence",
            "legacy_office_preserved",
            "mobile_no_overflow",
            "audit_chain_valid",
            "paid_execution_stays_disabled",
        ],
        "task_id": receipt["task"]["id"],
        "verification_task_cancelled": True,
        "browser_errors": errors,
        "render_observation": diagnostics,
        "renderer": "headless Chromium SwiftShader software; not a hardware GPU certification",
        "monthly_spend": final["kpis"]["monthly_spend"],
        "model_calls_in_check": 0,
        "world_version": "kingdom-2.0.0",
    }
    (evidence / "kingdom-apple-browser.json").write_text(json.dumps(result, indent=2) + "\n")
    assert not errors, errors
    print(json.dumps(result))


if __name__ == "__main__":
    main()
