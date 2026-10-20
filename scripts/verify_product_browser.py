"""Verify a real, explicitly unvalidated product draft against fresh source evidence."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    evidence = json.loads(Path("docs/evidence/fresh-discovery-portfolio.json").read_text())
    credentials = json.loads(Path(".local/owner-credentials.json").read_text())
    title = "Workflow pain research · unvalidated product hypothesis"
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
        section = page.get_by_role("region", name="Product Portfolio")
        section.get_by_text("Define a product hypothesis", exact=True).click()
        section.get_by_role("combobox", name="Product project", exact=True).select_option(
            evidence["project_id"]
        )
        section.get_by_label("Product name", exact=True).fill(title)
        section.get_by_label("Customer problem", exact=True).fill(
            "Investigate the workflow friction discussed at "
            + evidence["sources"][0]["url"]
            + ". No problem interviews or willingness-to-pay evidence have been collected."
        )
        section.get_by_label("Target customer", exact=True).fill(
            "Proposed: small teams managing repeated operational workflows; segment unvalidated"
        )
        section.get_by_label("MVP scope · one item per line", exact=True).fill(
            "Proposed: document one repeated workflow and its measurable friction\n"
            "Proposed: test a narrow automation only after customer evidence review"
        )
        section.get_by_role("button", name="Save product hypothesis", exact=True).click()
        card = section.locator("article").filter(has=page.get_by_role("heading", name=title, exact=True))
        card.get_by_role("heading", name=title, exact=True).wait_for()
        card.get_by_role("combobox", name="Validation experiment", exact=True).select_option(
            evidence["experiment_id"]
        )
        card.get_by_role("button", name="Link validation", exact=True).click()
        card.get_by_text("Validation experiment linked", exact=False).wait_for()
        page.reload(wait_until="networkidle")
        section = page.get_by_role("region", name="Product Portfolio")
        card = section.locator("article").filter(has=page.get_by_role("heading", name=title, exact=True))
        card.get_by_role("button", name="Check remaining release gates").click()
        card.get_by_text("No independently checked coding prototype attached", exact=True).wait_for()
        card.get_by_text("No concluded validation experiment", exact=True).wait_for()
        assert not card.get_by_role("button", name="Verify and attach prototype").count()
        section.screenshot(path="docs/evidence/product-portfolio-desktop.png")
        page.set_viewport_size({"width": 390, "height": 844})
        section.screenshot(path="docs/evidence/product-portfolio-mobile.png")
        assert page.locator("body").evaluate("(e) => e.scrollWidth") <= 390
        snapshot = page.evaluate("async () => (await fetch('/api/snapshot')).json()")
        product = next(r for r in snapshot["products"] if r["data"]["name"] == title)
        assert product["data"]["experiment_id"] == evidence["experiment_id"]
        assert product["data"]["proposed_price_minor"] is None
        assert product["data"]["economics"]["break_even_customers"] is None
        assert product["data"]["published"] is False
        assert product["data"]["prototype"] is None
        assert snapshot["organization"]["paid_execution_authorized"] is False
        assert page.evaluate("async () => (await fetch('/api/audit/verify')).json() ")["valid"]
        browser.close()
    Path("docs/evidence/product-portfolio-browser.json").write_text(
        json.dumps(
            {
                "scope": "actual UI persistence; draft hypothesis, no customer validation or prototype",
                "product_id": product["id"],
                "project_id": evidence["project_id"],
                "experiment_id": evidence["experiment_id"],
                "checks": [
                    "authenticated_create",
                    "same_project_experiment_link",
                    "reload_persistence",
                    "unknown_economics_preserved",
                    "prototype_and_release_gates_visible",
                    "mobile_no_horizontal_overflow",
                    "audit_chain_valid",
                    "paid_execution_disabled",
                ],
                "browser_errors": errors,
            },
            indent=2,
        )
        + "\n"
    )
    assert not errors, errors
    print("Product draft and experiment link persisted; release gates and mobile layout verified.")


if __name__ == "__main__":
    main()
