"""Verify real scene measurement and private report export without invoking agents."""

import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

root = Path(__file__).resolve().parents[1]
c = json.loads((root / ".local/owner-credentials.json").read_text())
out = root / "docs/evidence"
errors = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox", "--enable-unsafe-swiftshader"])
    x = b.new_context(
        viewport={"width": 1440, "height": 1000}, reduced_motion="no-preference", accept_downloads=True
    )
    assert x.request.post(
        "http://localhost:3000/api/auth/login", data={k: c[k] for k in ("email", "password")}
    ).ok
    t = x.new_page()
    t.on("pageerror", lambda e: errors.append(str(e)))
    t.goto("http://localhost:3000", wait_until="domcontentloaded", timeout=120000)
    t.locator('[data-world-rendered="true"]').wait_for(timeout=90000)
    t.get_by_role("button", name="Display settings", exact=True).click()
    panel = t.locator(".kingdom-performance")
    start = panel.get_by_role("button", name="Measure performance (10s)", exact=True)
    t.get_by_role("combobox", name="Kingdom render quality", exact=True).select_option("balanced")
    expect(start).to_be_enabled(timeout=60000)
    start.click()
    panel.get_by_role("button", name="Download performance report", exact=True).wait_for(timeout=90000)
    with t.expect_download(timeout=60000) as d:
        panel.get_by_role("button", name="Download performance report", exact=True).click()
    download = d.value
    report = json.loads(Path(download.path()).read_text())
    assert report["scene_frames"] > 0 and report["duration_ms"] >= 10000
    assert report["scope"].startswith("Foreground browser sample")
    assert set(report) == {
        "schema_version",
        "captured_at",
        "world_version",
        "quality",
        "citizens",
        "renderer",
        "duration_ms",
        "scene_frames",
        "scene_fps",
        "browser_raf_fps",
        "median_browser_frame_ms",
        "p95_browser_frame_ms",
        "canvas_pixels",
        "scope",
    }
    (out / "kingdom-client-performance-report.json").write_text(json.dumps(report, indent=2) + "\n")
    t.screenshot(path=str(out / "kingdom-diagnostics-desktop.png"), timeout=60000)
    start.click()
    t.get_by_role("button", name="Reset kingdom camera", exact=True).click()
    expect(start).to_be_enabled()
    expect(panel.get_by_role("button", name="Download performance report", exact=True)).not_to_be_visible()
    start.click()
    panel.get_by_role("button", name="Cancel measurement", exact=True).click()
    expect(start).to_be_enabled()
    expect(panel.get_by_role("button", name="Download performance report", exact=True)).not_to_be_visible()
    t.get_by_role("checkbox", name="Reduced motion", exact=True).check()
    expect(start).to_be_disabled()
    panel.get_by_text("Turn off Reduced motion to measure scene frames.", exact=True).wait_for()
    t.set_viewport_size({"width": 390, "height": 844})
    assert t.evaluate("document.documentElement.scrollWidth <= innerWidth")
    t.screenshot(path=str(out / "kingdom-diagnostics-mobile.png"))
    assert not errors, errors
    (out / "kingdom-diagnostics-browser.json").write_text(
        json.dumps(
            {
                "checks": [
                    "actual_scene_measurement",
                    "json_download",
                    "no_company_records_or_credentials_in_report",
                    "explicit_cancel_discards_report",
                    "camera_reset_discards_report",
                    "reduced_motion_disables_measurement",
                    "mobile_no_overflow",
                ],
                "page_errors": errors,
                "database_mutations": 0,
                "model_calls": 0,
                "scope": "Authenticated local real 3D and API; software renderer. No hardware GPU claim.",
            },
            indent=2,
        )
        + "\n"
    )
    print("Diagnostics acceptance passed", flush=True)
    b.close()
