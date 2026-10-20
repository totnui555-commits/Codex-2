# Provider contract verification — 2026-10-20

Official docs inspected over verified HTTPS and installed API signatures/types checked before writing adapters:
- https://openai.github.io/openai-agents-python/running_agents/ — Agent, Runner.run, typed outputs and run limits.
- https://developers.openai.com/codex/sdk/ — TypeScript Codex, startThread, workingDirectory, sandboxMode, run and abort signal; installed @openai/codex-sdk/dist/index.d.ts read directly.
- https://www.daytona.io/docs/en/python-sdk/sync/daytona/ — Daytona create/delete/get; installed CreateSandboxFromSnapshotParams, process.exec, fs.upload_file/download_file signatures checked.
- https://docs.temporal.io/develop/python — installed Client.connect, Worker, workflow/activity decorators, bounded activities and retries validated by a real Temporal worker test.
- https://hn.algolia.com/api — bounded public source retrieval verified with HTTP 200 and eight actual discussion records, archived separately.
- https://docs.stripe.com/webhooks/signature — timestamp and HMAC verification; signed-event fixtures cover replay and tenant boundaries. No real billing connection configured.

Installed Python signatures: sdk-contracts.txt. Runtime versions are pinned in requirements.lock and package-lock.json. Provider functionality beyond local contract tests remains unverified until a live authorized run. API configuration status does not imply successful authentication or isolation proof.
