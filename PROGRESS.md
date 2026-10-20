# AI COMPANY OS — implementation progress

Updated 2026-10-20 (founder timezone Asia/Bangkok). Repository: `/workspace/Codex-2`, initially empty, branch `work`. This file distinguishes implemented code, executed evidence and unfinished acceptance criteria. **The full Master Prompt is not yet complete or production-certified.**

## Milestone status

| Milestone | Status | Implemented / verified | Remaining acceptance work |
|---|---|---|---|
| M0 Repository audit / architecture | Complete for this installation | Full specification read; no AGENTS.md initially; runtime/credential inventory; official SDK contracts/types checked; architecture ADR, plan, env template, locked dependencies | Recheck live provider permissions when configured |
| M1 Management foundation | Verified local vertical slice | FastAPI owner auth; PostgreSQL migrations (37 domain tables); tenant-scoped projects/tasks/DAG; 25 configured roles; transactional events/outbox; append-only hash-chained audit; real-time dashboard and 3D shell | Organization/member administration beyond initial owner, richer CRUD forms and pagination |
| M2 Autonomous software factory | Implemented adapters; live benchmark blocked | OpenAI Agents SDK typed Chief of Staff DAG delegation and specialist calls; Temporal workflow/activity; scoped model gateway; Daytona/Codex worker; immutable independent CRUD QA harness; GitHub draft PR adapter; private artifact checksum storage; Build Inspector | Real model/sandbox/storage/GitHub connections, current separate research/Codex prices and dated FX/sandbox pricing, explicit paid budget opt-in, hosted isolation proof, live benchmark PR and owner-visible staging preview. No actual coding model or hosted sandbox run has occurred |
| M3 Governance / durable operation | Core locally verified; external delivery incomplete | Atomic hierarchical budget reservations; concurrency limits; estimated telemetry reconciliation; 50/80/95% alerts; immutable-target single-use expiring approvals; STOP ALL and project pause; independent Watchtower with incidents/quarantine/heartbeat/remote cleanup logic; persistent Inbox; Gmail adapter and bounded delivery states; actual Temporal workflow dispatch blocks safely without providers | Application Gmail OAuth/authorized test delivery, real provider stop/reclaim proof, production Temporal TLS/auth, automatic GitHub App token renewal, authenticated durable approval waits tied to real protected release operations, scheduled digest/push |
| M4 Venture engine | Source-backed discovery and incubation backlog verified | Daily bounded public API collection; eight real discussion sources with URLs/observation/publication dates and uncertainty; preliminary weighted scoring; idempotent opportunity-to-project/task creation; fresh HMAC Stripe signatures, tenant match, live-only ledger, duplicate protection and refund debit tests | Market validation/willingness-to-pay research, experiment/product/funnel workflows and UI, prototypes, live billing onboarding/webhooks, subscriptions/fees/chargebacks/settlements; no verified revenue exists |
| M5 Production office | Interactive original office verified; full acceptance incomplete | Six procedural floors, yellow/glass/wood architecture, plants/desks/avatars; orbit/zoom/reset, floor selection and agent camera focus; authoritative run-derived state/working motion; inspector; accessible 2D view; responsive operational screens; real event updates; desktop/mobile screenshots; no browser page errors | Full state/animation choreography, moving-agent following, richer team/project filters and search, historical scene replay, measured GPU/frame-budget profiling, formal accessibility audit, premium asset/detail iteration |
| M6 Hardening / expansion | Local checks pass; production review pending | Restricted PostgreSQL roles/RLS; append-only history triggers; 24 backend integration tests including real Temporal execution; frontend tests/typecheck/build; CI; private local configuration; Dockerfiles/Compose; deployment/security/cost/operations/founder guides; backup/isolated-restore scripts | Hosted security/penetration tests, nonce CSP/distributed rate limiting, production role bindings/secret rotation, backup restore drill/PITR proof, load/recovery tests, full production observability and deployment acceptance |

## What is running locally

- PostgreSQL 17 and pinned Temporal CLI 1.4.1 (server 1.28) development service.
- FastAPI on port 8000; Next.js on port 3000; independent worker, scheduler and Watchtower processes. Browser closure does not stop these processes. Cloud workspace lifetime is not a production 24/7 uptime guarantee.
- Owner account initialized with generated private credentials in ignored `.local/owner-credentials.json` (0600). `.env` is private/ignored. No credentials are embedded in the UI or committed source.
- Installation remains `research_only`, paid execution disabled. Verified live revenue is zero. Agent activity is idle unless a persisted running run exists.
- Actual verification tasks have persisted blocked states and real Temporal histories (see `docs/evidence/runtime.json`); no fake successful coding logs or sales are shown.

## Founder setup request / email evidence

One consolidated provider setup request is persisted in Founder Inbox. The user-authorized connected **chat Gmail** account sent it to `traisorn.th@gmail.com`; Gmail confirmed message ID `1a1582754f083473` / SENT. Recipient reading is unknown. This connection is **not** deployed application OAuth. Application email truthfully remains disconnected; app delivery failures retain the Inbox request. Sensitive decisions require authenticated in-app action; email replies and silence grant no approval.

Required secure setup: scoped model connection; current research and Codex model price tables plus dated FX; authorized spend ceilings; hardened Daytona snapshot and per-minute pricing; publicly reachable HTTPS scoped model gateway; scoped GitHub App/token and allowed repository; private S3 storage; separately authorized Gmail OAuth. Add secrets through environment/secret-manager configuration, never chat or Inbox text.

## Verification commands and outcomes

- `RUN_TEMPORAL_TESTS=1 .venv/bin/pytest -q`: **24 passed**. Real PostgreSQL and real Temporal. Includes auth/origin rejection, tenant isolation, database RLS without application filters, worker/Watchtower inability to self-authorize, DAG cycles, persistence, STOP ALL, audit tampering/append-only triggers, concurrent budget collisions, reservation idempotency/overrun pause, exact-artifact single-use/expired approvals, stalled-worker quarantine, mail disconnected/sent/ambiguous states, hostile file exports, redaction, real-source scoring/incubation, signed live revenue/refunds/replay and gateway rejection.
- `npm run test`: **3 passed** (authoritative agent state and money formatting).
- `npm run typecheck`: web and Codex worker **passed**.
- `npm run build`: Next.js production and Codex worker **passed**. Web production Docker build also validates standalone Next output.
- `.venv/bin/ruff check apps/api/company_os scripts`: **passed**.
- `npm audit --omit=dev`: **0 known vulnerabilities** at check time; not a comprehensive security audit.
- `scripts/browser_check.py`: owner login, real office render, 2D floor selection, persistent Inbox, actual project/task creation, mobile no-overflow; **no page errors**.
- `scripts/browser_readonly_check.py`: agent selection/camera focus, truthful empty Build Inspector, authenticated `/inbox` deep link, mobile layout; **no page errors**.
- `scripts/live_events_check.py`: actual authenticated SSE event received, cursor replay excludes already-delivered event, audit chain valid.
- Public HN/Algolia API retrieval: **HTTP 200**, eight real discussion records; evidence archived. Preliminary heuristic scores are not confirmed demand.
- Alembic applied to separate local installation and test databases. Runtime role grants tested explicitly; local development administrator otherwise bypasses RLS.
- API and web images built with the managed proxy CA through transient BuildKit mounts. Web changed to standalone runtime output to reduce image size from ~1.35 GB to ~294 MB. Clean Compose startup and actual proxy auth/CRUD, migration/role seed, Temporal dispatch, live Watchtower and audit integrity **passed**; see `docs/evidence/containers.json`. The isolated smoke stack was shut down afterward (volumes retained) to reclaim disk; the primary native installation remains running. Initial full-stack and sandbox-image builds hit the 32 GB workspace disk limit; only implementation-created unused build caches/images were cleaned, preserving database state. The hosted sandbox image/isolation benchmark remains **unverified**, not a passing integration claim.

## Evidence / deliverables

- `docs/evidence/office-desktop.png`, `office-mobile.png`, `agent-inspector.png`, `founder-inbox.png`, `task-backlog.png`.
- `browser-check.json`, `browser-readonly-check.json`, `events-reconnect.json`, `runtime.json`, `public-source-retrieval.json`, `SDK_SOURCES.md`, `sdk-contracts.txt`.
- Backend/domain: `apps/api/company_os/`; frozen schema and RLS/history migrations: `apps/api/migrations/versions/`.
- Frontend and reusable UI: `apps/web/src/`; sandbox Codex SDK: `packages/codex-worker/`; original fixed QA/export tools: `sandbox/`.
- Roles: `config/roles.json`; runtime role grants: `scripts/database_roles.sql`; local/production instructions: README and `docs/`.
- `.github/workflows/ci.yml`, `docker-compose.yml`, `infrastructure/`, `.env.example`, npm/Python locks.

## Engineering decisions / issues resolved

- Use a modular monolith plus separate workers, not a simulated browser-driven workforce. PostgreSQL is authoritative; no production SQLite fallback.
- Use the actual installed Agents/Codex/Daytona APIs; adapters fail closed. Model keys stay in trusted services; sandbox gets only an expiring run-scoped gateway capability. Research and coding models have separate explicit prices.
- Do not automatically retry ambiguous paid/externally visible operations. Preserve reservations and escalate for reconciliation. GitHub token renewal, hosted preview and general repo test manifests are not silently invented.
- Fixed a Temporal import-sandbox regression and verified the correction with a real worker test.
- Fixed oversized 3D labels/React root cleanup by projecting labels through the regular React tree. Removed dependence on nested HTML roots inside the 3D renderer. Screenshot and interaction checks passed afterward.
- Temporal's latest image failed locally due internal loopback/proxy behavior; pinned stable CLI and explicit local NO_PROXY entries resolved startup without bypassing any external destination policy.

## Next execution steps

1. Complete the secure provider setup request and explicit owner budgets; verify each actual provider handshake.
2. Build/register/audit the hardened snapshot; execute `docs/BENCHMARK.md` through a real hosted Codex run, independent QA, private artifacts and a draft PR. Save actual costs and failed outcomes. Add owner-visible preview before claiming M2 done.
3. Configure application Gmail OAuth and an owner-opted-in test message; verify real sandbox kill/reclamation and production Temporal recovery.
4. Implement experiment/product/funnel workflows, remaining office interactions and financial/observability integrations, then execute the documented production release gate. No public launch, ads, third-party marketing, contracts or binding purchases have been approved or performed.

## Final infrastructure checkpoint

Both API and standalone web images built successfully. A clean isolated Compose stack passed actual frontend-proxy owner authentication, PostgreSQL initialization/migrations, 25 role definitions, project/task persistence, real Temporal dispatch into a blocked task without credentials, live Watchtower reporting and hash-chain verification. Fixed non-root config readability and initialized the Temporal volume using a capability-limited one-shot CHOWN container. Optional `docker-compose.cloud.yml` handles managed build/runtime CA trust. The unsuccessful sandbox-image build remains unverified and is not used as a hosted execution claim.

## OpenRouter connection update — 2026-10-20
Founder explicitly supplied an OpenRouter credential for configuration. Stored only in the ignored private .env file (0600), never in source/evidence. Authenticated GET /api/v1/key returned 200, limit/remaining USD 100, usage 0. No paid inference request was sent. Retrieved official model catalog pricing for openai/gpt-4.1-mini and saved non-secret evidence in docs/evidence/openrouter-connection.json. Added an Agents SDK OpenAIChatCompletionsModel adapter for OpenRouter research/planning, with deterministic provider-selection tests; 26 backend tests passed. The direct OpenAI Responses/Codex gateway remains separate and does not receive the OpenRouter key. Paid authorization remains disabled; FX, storage, sandbox and GitHub setup remain outstanding. Existing deployment images need rebuilding to include this change.

## Delegated setup activation — 2026-10-20
Founder asked to handle all remaining setup after the THB 100 initial-test recommendation. Configured that conservative ceiling and concurrency one for bounded research verification; restored paid_execution_authorized=false after each run. No recurring paid loop was enabled.

- Verified the existing GitHub identity can read/push the private repository. Added runtime support for inherited GH_TOKEN without copying it into dotenv or sandbox credentials. Initialized the empty private main branch as a review base.
- Added a real encrypted persistent development artifact store with authenticated decryption and SHA-256 validation. It is explicitly local, not a cloud S3 connection, and is denied in production. MinIO registry pulls were denied, so no MinIO service is claimed.
- Retrieved dated USD/THB FX (33.555, 2026-10-19) from Frankfurter and actual research/Codex pricing from the OpenRouter model catalog.
- Executed TWO real OpenRouter Agents SDK specialist jobs through real Temporal workers. Both produced encrypted verified artifacts and wait for owner review. First run: 266 input / 217 output tokens, estimated THB 0.0152. Second: 266 input / 223 output, provider response gen-1792485461-ReRo9XMSfFEZTLS333vg reported USD 0.0004632, converted to estimated THB 0.0155 using the dated FX snapshot.
- Fixed provider attribution and captured per-response model IDs/cost metadata, because aggregate key usage cannot be treated as one job's cost. Prior aggregate key usage observation USD 0.0098862 was not attributed wholesale to this application. First-run per-request cost remains estimated; the second has provider-reported USD cost.
- Official OpenRouter Codex documentation confirms a supported provider route. Prepared the Codex gateway for openrouter or openai, selected catalog-listed openai/gpt-5.1-codex-mini, and configured its real prices. This route has NOT been executed through a hosted Codex sandbox; separate OpenAI signup is not required merely to prepare it.
- Backend tests: 30 passed, including encrypted storage, production denial, billing metadata capture and coding endpoint selection. TypeScript checks rerun. Source/evidence are being preserved in a private draft PR; no production merge/release is authorized by that PR.

Remaining owner-only setup is consolidated in docs/FOUNDER_SETUP_TH.md and Founder Inbox: Daytona login/account-specific API credentials and an authorized reachable HTTPS gateway deployment. The environment has no Daytona connection, and the connected browser-control tool is unavailable. Application Gmail OAuth and cloud S3 still require their own production credentials/consent; chat connectors are not exported as application OAuth tokens. No account registration, new service contract, purchase, public tunnel or public app launch was performed.

## Review handoff — 2026-10-20

Private draft PR: https://github.com/totnui555-commits/Codex-2/pull/1 . Source pushed on codex/company-os-implementation; no merge or production launch. Sent the consolidated missing-account/gateway setup request to the authorized founder address using the connected Gmail chat connector; connector reported action completed but returned no message ID, so no application delivery receipt is claimed. Paid execution remains disabled.

## Authorized continuation: Product Incubator — 2026-10-20

Founder authorized continuing all setup/implementation. This supplies authorization to proceed; it does not supply missing external account credentials. Rechecked the managed environment: no Daytona or cloud outbound identity/secret binding exists. Plugin discovery found Render and Railway hosting integrations but no callable Daytona connection; Render was suggested as the smallest useful hosting connection and is not installed/connected. No deployment or account onboarding is claimed.

Implemented the Product Incubator vertical slice, rather than stopping at the hosted-sandbox blocker:

- Strict authenticated experiment contracts, tenant/project scope, predeclared thresholds and minimum sample sizes, version checks, serialized writes and draft/running/paused/concluded transitions.
- Persistent owner-reported evidence receipts with same-project checksummed artifact provenance; duplicate batches cannot inflate counts. No measurement is represented as independently verified demand or provider-confirmed revenue.
- Wilson 95% interval recommendations with an explicit inconclusive state; STOP ALL/project pause gates new evidence. Concluded results are frozen. No experiment action grants external execution permission.
- Interactive forms, evidence receipt inspector, actual statistics, lifecycle controls and responsive styling in Opportunities. Real event snapshots refresh the view.
- Linked an actual existing public-source opportunity to a paused validation project/backlog and draft experiment, with proposed criteria and zero customer observations. Preserved the dated source and identifiers in docs/evidence/source-to-incubator.json.
- Real browser persistence/lifecycle verification passed with zero browser errors and mobile horizontal overflow absent. The internal check recorded zero customer observations and an inconclusive result; it is not customer research.
- Full backend verification including the actual Temporal service: **35 passed**. Frontend: **3 passed**. Both TypeScript workspaces passed and web/Codex production builds succeeded. Ruff passed. No additional paid inference was used; the existing THB 100 ceiling remains and paid execution is disabled.

Remaining blockers: Daytona account credentials/snapshot setup and a connected HTTPS gateway host for the real hosted coding benchmark; application-owned email OAuth and cloud object storage for production; remaining product/funnel/office and production release acceptance work. Founder Inbox now explicitly distinguishes missing account connections from permission, which the founder has already granted. See docs/INCUBATOR.md for concrete behavior and limitations.

## Real planner-to-specialist delegation and independent CI — 2026-10-20

Executed one real Chief of Staff invocation through Temporal/OpenRouter. Its structured plan created exactly two independent advisory tasks, then actual Business Analyst and UX Researcher invocations produced encrypted checksummed reports. Planner task completed; both specialist tasks remain waiting_for_approval. This is real internal planning/delegation, not customer research, code execution or independent validation of model claims. docs/evidence/live-team-run.json records actual workflow/task/run IDs, provider response metadata, artifact hashes and cost receipts.

The three calls reported USD 0.0006900, 0.0005024 and 0.0004028; converted/rounded application cost was THB 0.0536 using the dated FX snapshot. Combined with the earlier two specialist jobs, recorded spend is approximately THB 0.0843. Automatic dispatch was briefly paused to restrict this verification to the selected project, then restored; paid execution was restored to false. The reusable script now also includes a local fail-closed database cleanup if the API becomes unavailable during policy restoration. No external account credentials were invented or acquired.

Both GitHub workflow runs for commit 602c8a8 succeeded on independent GitHub runners, including migrations, restricted database roles, actual Temporal, 35 backend tests, frontend tests/typechecks/builds and Ruff. Added branch filtering and concurrency to avoid duplicate push/PR verification and cancel superseded runs. The subsequent evidence/script/CI commit receives its own check; its outcome must be verified separately.

## Final continuation checkpoint — 2026-10-20

Latest code/script/CI commit **9fd5531** passed independent GitHub CI: https://github.com/totnui555-commits/Codex-2/actions/runs/39397093487 . This final documentation/evidence update does not change executable code. API snapshot verifies worker/scheduler/Watchtower live, audit chain valid, paid execution disabled, THB 100 limit and THB 0.0843 recorded spend. Two experiments contain zero customer observations. Model/GitHub/development artifacts are configured; sandbox, application email and billing remain disconnected.

Inspected the official Daytona sign-in flow in a fresh private headless browser using the connected account identity. It requires password authentication or Google/GitHub OAuth; an authenticated browser session is not available. No password reset, account creation, API-key acquisition, service purchase or sandbox provisioning occurred. This is a verified authentication blocker, not missing user permission. Render remains unconnected. Updated Founder Inbox accordingly; existing founder setup email remains the notification record, with no repeated email sent in this continuation.

## Render connected and staging preparation — 2026-10-20

Founder confirmed Render workspace My Workspace / totnui555@gmail.com, tea-dbbj2qbbc2fs73bcelb0. Clarified USD 100 is for OpenRouter API, not recurring hosting. No paid hosting or worker resource was purchased. Existing local execution remains research_only with paid execution disabled; the general THB 100 initial-test ceiling was not silently reallocated into a hosting allowance.

Created actual Render PostgreSQL company-os-staging-db (free, Singapore, PostgreSQL 17), dpg-dbbj5h0u01pc73dvnm5g-a. Status available; expires 2026-11-19. No web services or other databases existed in this workspace when checked. The existing free DB is referenced from render.yaml rather than redeclared, to avoid duplicate free-instance creation.

Implemented cloud transport/deployment code:

- Normalize postgres:// and postgresql:// DSNs to the installed psycopg driver without losing escaped credentials or SSL parameters.
- Shared Temporal connection helper with namespace/API-key/TLS settings; reject API-key transport without TLS. Actual Temporal integration verification now uses that helper.
- Normalize Render private hostport to a proper HTTP API origin; reject credential-bearing origins, unsupported schemes and path/query ambiguity.
- Preserve up to four decimal places for sub-baht costs, instead of showing a real nonzero spend as zero.
- Management-only free staging Docker topology and supervisor (API + Next standalone), migrations/role seeding, signal forwarding and fail-together process management. Staging requires persistent PostgreSQL and private setup/session secrets; it does not run autonomous workers. UI explicitly labels staging limitations.
- Local native staging runtime smoke verified real PostgreSQL migration, Next server, proxy, authenticated login/snapshot, 25 roles, audit chain and graceful shutdown. No mock database or invented activity. The Docker image/Render deployment itself remains unverified.

Validation: 37 backend tests including actual Temporal passed; six frontend tests passed; TypeScript and production builds passed; Ruff passed. render.yaml passed the current official JSON Schema. Installed official Render CLI v2.30.0 with release SHA-256 verification; CLI platform validation is blocked by separate CLI authentication, not schema acceptance. Render MCP OAuth is not exported to CLI or copied into files.

Blocking platform action: current connector cannot create/apply a Blueprint or set a fromDatabase reference when creating a web service. Dashboard flow must connect the private Git source, choose codex/company-os-implementation and apply render.yaml. No web deployment/live URL, external gateway or hosted coding run is claimed. docs/RENDER_STAGING_TH.md gives the concrete remaining action and verified free-plan limitations. Daytona password/OAuth authentication, production storage/email/hosting and the remaining release gate remain outstanding.

### Render checkpoint verification and founder handoff

Implementation commit **2c1c6c4** passed independent GitHub CI: https://github.com/totnui555-commits/Codex-2/actions/runs/39401039003 (37 backend tests with real Temporal, six frontend tests, TypeScript/build and Ruff). Native development API restored and checked: audit chain valid, paid execution false, recorded model spend still THB 0.0843. No new inference was charged in this continuation.

Sent the concrete Blueprint Dashboard action to traisorn.th@gmail.com through the explicitly authorized Gmail chat connector. Actual receipt ID **1a158a6072fb21f7** was recorded as channel chat_gmail / state sent in Founder Inbox delivery history; the pending application delivery was reconciled to prevent treating it as an application OAuth send. Application email integration remains disconnected. Queued the Render Blueprint Dashboard URL in the Codex panel; queuing a page is not completion of authentication, Blueprint apply or deployment. Latest non-secret resource/validation evidence is docs/evidence/render-staging-readiness.json.

## Continued implementation: coding gateway revocation and real RLS — 2026-10-20

Rechecked the founder-confirmed Render workspace: still no web service/deploy exists. The Dashboard Blueprint action remains an external platform/authentication blocker; no new hosting or model spend was made.

Advanced the secure coding-worker milestone in source:

- Gateway capabilities now require expiration and an organization claim, supplied by trusted orchestration when the Daytona worker capability is minted.
- Set the verified tenant context for every gateway DB transaction. Added positive verification under the actual restricted company_api PostgreSQL role, rather than relying on a migration-owner connection that bypasses RLS.
- Reject paid-authorization revocation, research-only mode, STOP ALL, paused projects, expired/wrong task leases and missing reservations before provider I/O. Recheck policy while streaming and before returning non-streamed output.
- Stop forwarding after in-flight revocation; preserve known usage and budget reservations rather than claim free cancellation or known zero cost. Audit call outcomes and distinguish completed/revoked/provider_rejected/usage_unknown.
- Validate request structure and tool definitions before consuming an allowance; disable provider-hosted tools/background execution and bound request receipt memory. Keep server-selected model and output limits.

Full backend suite with real PostgreSQL and Temporal: **51 passed**. The new security cases use controlled HTTP transports for boundary testing, not simulated production integrations. Ruff passed. No hosted Codex execution, Render web deployment or additional paid inference is claimed. See docs/GATEWAY_SECURITY.md.

### Native service continuity and CI observation

Found that native API/worker processes tied to earlier command sessions were no longer running, while the detached scheduler survived. Added scripts/start_local_services.py to start the four development services detached with private logs and a startup lock, without enabling paid execution. Executed it twice: the second invocation reused every process without creating duplicates. Real API snapshots confirm worker/scheduler/Watchtower live, audit chain valid, paid execution false and spend unchanged at THB 0.0843. This improves local session continuity; it is not production hosting or survival of a stopped cloud environment.

The first GitHub CI attempt for 711157d exited 139 (Python segmentation fault) in scripts/wait_temporal.py before the test suite. No test assertion failed in that attempt; the native crash's underlying cause is not established. Requested a fresh runner attempt, and the subsequent continuity-script commit receives its own complete verification. Local full backend verification remains 51 passed. Do not report the failed attempt as a CI pass.

### CI native transport diagnostic follow-up

A second fresh CI attempt also exited 139 at Temporal readiness, before pytest. The runner reported Python 3.12.15; the local environment where the actual Temporal suite passes uses Python 3.12.14. Pinned CI to that verified patch and enabled faulthandler diagnostics. Added a bounded TCP readiness check before constructing the native Temporal client, to avoid native client creation while the service port is closed. The actual SDK health check and Temporal integration tests remain required; nothing is skipped or replaced with a mock. The readiness script passes locally. This is a controlled mitigation/diagnostic change; the native crash root cause is not established from the available trace.

### Verified gateway checkpoint

Commit **f4752ae** passed the complete independent GitHub workflow: https://github.com/totnui555-commits/Codex-2/actions/runs/39423677511 . Actual Temporal readiness, all **51 backend tests**, Ruff, six frontend tests, TypeScript and production builds passed. The verified configuration combines Python 3.12.14 and TCP readiness before SDK connection; this successful mitigation does not establish which underlying native issue caused the earlier 3.12.15 crashes. No test was skipped to obtain the result.

Development service startup remains detached and idempotent, with live worker/scheduler/Watchtower heartbeats and valid audit chain. No additional model spending or paid hosting occurred. Render Blueprint apply and Daytona account authentication remain unfulfilled external steps; the hosted coding benchmark and production deployment are still unverified. The final evidence/documentation-only commit skips redundant CI.

## Continued implementation: verified inter-agent evidence handoffs — 2026-10-20

Implemented a real evidence path across the task DAG. Planner, specialist and coding briefs now receive bounded dependency artifacts, rather than just task objectives. Enforce completed same-tenant/same-project sources, selected artifact IDs, verified checksums and a 32,000-byte budget; redact sensitive content and label all supplied evidence as untrusted data. Pending review, changed approvals, missing selection, corrupt bytes and oversized evidence fail closed. Owner artifact acceptance now records the exact ID/hash in task checkpoints and audit history. Handoff provenance is audited without logging source bodies.

Local full backend suite with PostgreSQL and actual Temporal: **59 passed**. Eight new cases cover real encrypted artifact transfer, scope/state/selection/approval integrity, size/tamper rejection and exact owner acceptance. Ruff passed.

Executed ONE real OpenRouter/Temporal Technical Architect call consuming the previous completed Chief of Staff plan artifact. The output cited the actual source task ID, artifact ID and full SHA-256; the advisory report remains waiting_for_approval. Provider receipt gen-1792501029-3g0h0mtKXe0nVq4TkAq8 reported USD **0.0011864**, converted/rounded THB **0.0398** with the dated FX snapshot. Total recorded application model spend is approximately THB **0.1241**. Paid execution was restored to false and the scheduler resumed. This verifies model evidence handoff, not customer demand or a hosted Codex build. Saved actual workflow/run/source/artifact/cost receipts in docs/evidence/live-handoff-run.json.

The reusable verification script restores scheduler dispatch using graceful process shutdown/restart rather than leaving a process suspended while it may own DB locks. No repeated paid run was needed for that operational cleanup refinement. The existing USD100 OpenRouter-only authorization remains separate from hosting. Render Blueprint apply and Daytona authentication remain external blockers; no deployment or new hosting spend is claimed.
