# Real coding benchmark

Status: **not executed through Codex/Daytona**; external credentials and owner budget authorization are missing. Local pytest/Playwright checks prove the platform, not this build loop.

Assign a backend_engineer task in build_autopilot mode in the configured benchmark repository with this exact objective:

> Implement app.py exposing a FastAPI app named app. GET /health returns 200. POST /items accepts a nonempty name and returns 201 with an id/name object. GET /items returns an array; GET /items/{id}, PATCH /items/{id} and DELETE /items/{id} implement CRUD with 404 for missing records. Persist using the DATABASE_PATH environment variable across process restarts. Reject empty names with 422. Do not change dependencies, CI, infrastructure or policy. Dependencies are preinstalled in the hardened snapshot.

The factory exports code, provisions a second hosted sandbox, runs the immutable sandbox/benchmark.py acceptance suite, checks report exit status, commits permitted files via the scoped GitHub adapter, opens a draft PR and stores the entire evidence bundle privately with SHA-256 verification. No production release or externally public app deployment occurs.

A live result must include Temporal workflow/run, provider sandbox IDs, model gateway usage, checksummed code and QA report, actual GitHub PR/commit, and owner-visible preview. Preview hosting is not yet implemented; it remains a separate acceptance blocker. Independent sandbox execution is not proven by adapter unit tests or a screenshot.
