"""Check production Next.js nonce delivery in a local standalone browser session."""

import argparse
import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright


def inspect_request(browser, url):
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.add_init_script(
        "window.__cspViolations=[]; addEventListener('securitypolicyviolation', "
        "e=>window.__cspViolations.push({directive:e.violatedDirective,blocked:e.blockedURI}));"
    )
    static_responses = []
    page.on(
        "response",
        lambda response: (
            static_responses.append({"status": response.status, "url": response.url})
            if "/_next/static/" in response.url
            else None
        ),
    )
    response = page.goto(url, wait_until="networkidle", timeout=30000)
    assert response is not None and response.status == 200
    policy = response.headers.get("content-security-policy", "")
    nonce_match = re.search(r"'nonce-([^']+)'", policy)
    assert nonce_match, "response CSP has no nonce"
    nonce = nonce_match.group(1)
    script_policy = next(
        (directive for directive in policy.split(";") if directive.strip().startswith("script-src")),
        "",
    )
    assert script_policy, "response CSP has no script-src directive"
    assert "'unsafe-inline'" not in script_policy
    assert "'unsafe-eval'" not in script_policy
    scripts = page.locator("script").evaluate_all(
        "elements => elements.map(({src, nonce}) => ({src, nonce}))"
    )
    assert scripts and all(script["nonce"] == nonce for script in scripts)
    violations = page.evaluate("window.__cspViolations")
    assert not violations, violations
    assert static_responses and all(item["status"] == 200 for item in static_responses)
    result = {
        "http_status": response.status,
        "nonce_length": len(nonce),
        "script_count": len(scripts),
        "static_asset_count": len(static_responses),
        "all_scripts_nonce_authorized": True,
        "script_policy_has_unsafe_inline": False,
        "script_policy_has_unsafe_eval": False,
        "csp_violations": len(violations),
    }
    page.close()
    return nonce, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:3000/")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    launch = {"headless": True, "args": ["--no-sandbox"]}
    chromium_path = os.getenv("CHROMIUM_PATH")
    if chromium_path:
        launch["executable_path"] = chromium_path

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch)
        requests = [inspect_request(browser, args.url) for _ in range(2)]
        browser.close()
    assert requests[0][0] != requests[1][0], "nonce was reused across page requests"
    receipt = {
        "scope": "Local production standalone web response; read-only browser check",
        "requests": [result for _, result in requests],
        "fresh_nonce_per_request": True,
        "api_mutations": 0,
        "model_calls": 0,
    }
    (root / "docs/evidence/csp-browser.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
