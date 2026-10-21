"""Capture a reproducible local software-renderer sample without invoking company work.

This is ordinary browser telemetry, not a sealed game-dev run or hardware certification.
Owner credentials are read only from the ignored local development credential file.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--name", required=True, help="Unique evidence name; existing files are never overwritten"
    )
    parser.add_argument("--seconds", type=int, default=12, choices=range(5, 61), metavar="5..60")
    parser.add_argument("--warmup", type=int, default=6, choices=range(2, 31), metavar="2..30")
    parser.add_argument("--quality", choices=["balanced", "low", "high"], default="balanced")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", args.name):
        parser.error("Use a short lowercase name containing letters, numbers and hyphens")
    root = Path(__file__).resolve().parents[1]
    evidence = root / "docs/evidence"
    report = evidence / f"kingdom-profile-{args.name}.json"
    screenshot = evidence / f"kingdom-profile-{args.name}.png"
    if report.exists() or screenshot.exists():
        parser.error("Evidence already exists; choose a new name")
    credentials = json.loads((root / ".local/owner-credentials.json").read_text())
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--enable-unsafe-swiftshader"])
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000}, device_scale_factor=1, reduced_motion="no-preference"
        )
        response = context.request.post(
            "http://localhost:3000/api/auth/login", data={k: credentials[k] for k in ("email", "password")}
        )
        if not response.ok:
            raise RuntimeError("Local owner login failed; no credential values were logged")
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("http://localhost:3000", wait_until="domcontentloaded", timeout=120000)
        page.locator('[data-world-rendered="true"]').wait_for(timeout=90000)
        page.get_by_role("button", name="Display settings", exact=True).click()
        page.get_by_role("combobox", name="Kingdom render quality", exact=True).select_option(args.quality)
        page.get_by_role("checkbox", name="Reduced motion", exact=True).uncheck()
        page.get_by_role("button", name="Display settings", exact=True).click()
        page.wait_for_function("window.__kingdomDiagnostics?.citizens > 0", timeout=90000)
        page.wait_for_timeout(args.warmup * 1000)
        result = page.evaluate(
            """async (duration) => {
          const canvas = document.querySelector('.kingdom-world canvas');
          const gl = canvas.getContext('webgl2');
          const ext = gl.getExtension('WEBGL_debug_renderer_info');
          let previous = performance.now();
          const started = previous;
          const intervals = [];
          await new Promise(resolve => {
            function sample(t) {
              intervals.push(t - previous); previous = t;
              if (t - started >= duration) resolve();
              else requestAnimationFrame(sample);
            }
            requestAnimationFrame(sample);
          });
          const sorted = intervals.slice(1).sort((a,b) => a-b);
          return {
            renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'unknown',
            frames: intervals.length, duration_ms: previous-started,
            raf_fps: intervals.length / ((previous-started)/1000),
            median_frame_ms: sorted[Math.floor(sorted.length/2)] ?? null,
            p95_frame_ms: sorted[Math.min(sorted.length-1, Math.floor(sorted.length*.95))] ?? null,
            three: window.__kingdomDiagnostics,
            canvas: [canvas.width, canvas.height]
          };
        }""",
            args.seconds * 1000,
        )
        page.get_by_role("button", name="Display settings", exact=True).click()
        page.get_by_role("checkbox", name="Reduced motion", exact=True).check()
        page.get_by_role("button", name="Display settings", exact=True).click()
        page.wait_for_timeout(1000)
        page.screenshot(path=str(screenshot), timeout=60000)
        result.update(
            {
                "scope": "Local Next dev browser telemetry; not a sealed game-dev bundle or hardware evidence",
                "quality": args.quality,
                "build_mode": "next_dev",
                "browser_version": browser.version,
                "units": {"median_frame_ms": "ms", "p95_frame_ms": "ms", "raf_fps": "frames/second"},
                "power_state": "unverified",
                "asset_sha256": {
                    name: hashlib.sha256((root / "apps/web/public/kingdom" / name).read_bytes()).hexdigest()
                    for name in (
                        "island.glb" if args.quality == "high" else f"island-{args.quality}.glb",
                        "citizen.glb",
                    )
                },
                "viewport": [1440, 1000],
                "errors": errors,
                "warmup_seconds": args.warmup,
                "database_mutations": 0,
                "model_calls": 0,
                "source_sha256": hashlib.sha256(
                    (root / "apps/web/src/components/kingdom.tsx").read_bytes()
                ).hexdigest(),
            }
        )
        report.write_text(json.dumps(result, indent=2) + "\n")
        browser.close()
    print(
        json.dumps(
            {"report": str(report.relative_to(root)), "frames": result["frames"], "page_errors": errors}
        )
    )
    if errors:
        raise RuntimeError("Browser errors were recorded; do not admit this sample as successful")


if __name__ == "__main__":
    main()
