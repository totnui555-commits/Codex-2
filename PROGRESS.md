# AI COMPANY OS — implementation progress

Updated 2026-10-22 (founder timezone Asia/Bangkok). Repository: `/workspace/Codex-2`, initially empty, implementation branch `codex/company-os-implementation`. This file distinguishes implemented code, executed evidence and unfinished acceptance criteria. **The full Master Prompt is not yet complete or production-certified.**

## Milestone status

| Milestone | Status | Implemented / verified | Remaining acceptance work |
|---|---|---|---|
| M0 Repository audit / architecture | Complete for this installation | Full specification read; no AGENTS.md initially; runtime/credential inventory; official SDK contracts/types checked; architecture ADR, plan, env template, locked dependencies | Recheck live provider permissions when configured |
| M1 Management foundation | Verified local vertical slice | FastAPI owner auth; PostgreSQL migrations (37 domain tables); tenant-scoped projects/tasks/DAG; 25 configured roles; transactional events/outbox; append-only hash-chained audit; real-time dashboard and 3D shell | Organization/member administration beyond initial owner, richer CRUD forms and pagination |
| M2 Autonomous software factory | Implemented adapters; live benchmark blocked | OpenAI Agents SDK typed Chief of Staff DAG delegation and specialist calls; Temporal workflow/activity; scoped model gateway; Daytona/Codex worker; immutable independent CRUD QA harness; GitHub draft PR adapter; private artifact checksum storage; Build Inspector | Actual hosted Daytona/Codex connection, public HTTPS gateway, production artifact storage, hosted isolation proof, independent QA benchmark PR and staging preview. OpenRouter advisory calls, real inter-agent evidence handoff and GitHub repository connection are verified; hosted coding remains unexecuted |
| M3 Governance / durable operation | Core locally verified; external delivery incomplete | Atomic hierarchical budget reservations; concurrency limits; estimated telemetry reconciliation; 50/80/95% alerts; immutable-target single-use expiring approvals; STOP ALL and project pause; independent Watchtower with repeat enforcement, execution revocation, per-tenant/provider failure isolation, incidents/quarantine/heartbeat/remote cleanup logic; persistent Inbox; Gmail adapter and bounded delivery states; actual Temporal workflow dispatch blocks safely without providers | Application Gmail OAuth/authorized test delivery, real provider stop/reclaim proof, production Temporal TLS/auth, automatic GitHub App token renewal, authenticated durable approval waits tied to real protected release operations, scheduled digest/push |
| M4 Venture engine | Source-backed discovery and incubation backlog verified | Daily bounded public API collection with a 90-day freshness window and versioned/checksummed source snapshots; preliminary weighted scoring; idempotent opportunity-to-project/task creation; experiment lifecycle and evidence receipts; persistent product hypotheses, estimated economics, same-project validation links and checked prototype gates; fresh HMAC Stripe signatures, tenant match, live-only ledger, duplicate protection and refund debit tests | Actual market validation/willingness-to-pay evidence, funnel/customer workflows, independent hosted prototypes, approved releases, live billing onboarding/webhooks, subscriptions/fees/chargebacks/settlements; no verified revenue exists |
| M5 Kingdom / legacy Office | Interactive Kingdom and preserved Office locally verified; production acceptance incomplete | Original Blender island and citizens, twelve functional landmarks, water/coast/harbor, three GLB LODs, GPU-instanced cast, camera presets/follow/reset, incident-driven lighthouse, operational/citizen inspectors, reduced-motion demand rendering, accessible fallback; original Office preserved at /office; actual authenticated desktop/mobile/reconnect screenshots and walkthrough | Hardware GPU/frame-budget acceptance, crowd collision/navigation stress, richer role choreography/foliage motion, historical replay, semantic library search, formal accessibility review and further bespoke art/detail iteration |
| M6 Hardening / expansion | Local checks pass; production review pending | Restricted PostgreSQL roles/RLS; append-only history triggers; 79 backend integration tests including real Temporal execution; frontend tests/typecheck/build; nonce CSP for production scripts; CI; private local configuration; Dockerfiles/Compose; deployment/security/cost/operations/founder guides; backup/isolated-restore scripts | Hosted security/penetration tests, distributed login limiting, production role bindings/secret rotation, production backup restore/PITR proof, load/recovery tests, full production observability and deployment acceptance |

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

- `RUN_TEMPORAL_TESTS=1 .venv/bin/pytest -q`: **79 passed**. Real PostgreSQL and real Temporal. Includes auth/origin rejection, tenant isolation, database RLS without application filters, worker/Watchtower inability to self-authorize, DAG cycles, persistence, STOP ALL, audit tampering/append-only triggers, concurrent budget collisions, reservation idempotency/overrun pause, exact-artifact single-use/expired approvals, stalled-worker quarantine, mail disconnected/sent/ambiguous states, hostile file exports, redaction, real-source scoring/incubation, signed live revenue/refunds/replay and gateway rejection.
- `npm run test`: **14 passed** (authoritative state, stable/scoped citizen identities, actual task/run pairing and revoked policy, incident severity, deterministic routes, money formatting and API origin validation).
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

### Verified handoff checkpoint

Implementation commit **9fb4c41** passed independent GitHub CI: https://github.com/totnui555-commits/Codex-2/actions/runs/39426613163 . Actual Temporal, all **59 backend tests**, six frontend tests, TypeScript, production builds and Ruff passed. Development API and worker were reloaded with the handoff implementation; authenticated snapshots confirm live service heartbeats, valid audit chain, paid execution disabled and THB 0.1241 recorded model spend.

Final operator-script cleanup treats already-exited zombie processes as stopped when waiting for scheduler shutdown, avoiding a false refusal to restart in this container environment. That small cleanup is lint-checked; the single paid handoff run was not repeated. No further application/runtime code changes follow the verified implementation commit. Final evidence/operator cleanup sync skips redundant CI.

Rechecked Render services: none exist yet. The prepared free staging Blueprint has not been applied, and no hosted coding/production release success is claimed. Existing founder setup requests remain the required account/platform actions.


## Continued implementation: Watchtower resilience, product portfolio and source freshness — 2026-10-20

Implemented independent enforcement of revoked paid execution, paused projects, research-only coding and missing/expired leases. Existing incident deduplication no longer bypasses repeat quarantine or a critical company stop. Each tenant check has its own transaction and exception boundary; provider cleanup failures cannot terminate subsequent monitoring cycles. Remote sandbox eligibility now includes the task lease and current company/project policy. Both provider lookup and deletion share a 30-second observation deadline; a timeout remains stop_failed, never confirmed termination. A process heartbeat demonstrates liveness, not success of every tenant/provider check. Eleven Watchtower tests include actual restricted PostgreSQL-role enforcement and controlled provider failures; actual hosted termination remains unverified.

Added authenticated, tenant-scoped product hypotheses backed by PostgreSQL. Records include customer problem, proposed MVP, explicitly unknown price/cost inputs, estimate-only contribution/break-even calculations, optimistic revisions, experiment links, archive/freeze and release blockers. A prototype attachment requires a completed same-project Daytona/Codex run, encrypted checksum-verified artifact, distinct build/independent-QA sandbox identities and a live GitHub PR/head check against the configured repository. External GitHub I/O releases the organization lock and restores transaction-local tenant/user context before revision rechecking. No release is authorized by this registry and no forecast is written as revenue. Seven integration cases verify these boundaries; the successful prototype boundary uses controlled GitHub responses and does not establish a live hosted prototype.

Discovery now queries the official search_by_date endpoint and locally rejects timestamps outside a 90-day window or more than five minutes into the future. Versioned ResearchEvidence snapshots retain source bodies and SHA-256 provenance; repeated retrieval alone does not duplicate an opportunity/version, while changed source content appends history. Added INSERT-only research_evidence privilege for company_worker. Existing installations must reapply scripts/database_roles.sql with their database administrator. Two tests cover timestamp filtering and restricted-role source-version persistence.

Executed one actual public API collection: eight recent discussion records and source snapshots persisted. A selected source became a paused incubation project and draft experiment with zero observations. These remain unvalidated public discussions; no customers, demand, willingness to pay, sales or hosted prototype are claimed. Evidence: docs/evidence/fresh-discovery-portfolio.json. No model invocation or additional model charge occurred in this continuation; prior recorded spend remains approximately THB 0.1241.

Browser acceptance passed against the real local API/PostgreSQL: created an explicitly unvalidated product hypothesis from the fresh source, linked its draft experiment, reloaded and confirmed persistence, preserved unknown economics, displayed prototype/validation/release blockers and verified no mobile horizontal overflow or page errors. The initial selector used label text including select options; using the actual accessible combobox role/name corrected the verification selector. No product behavior was changed to force a pass. Screenshots and actual product/project/experiment IDs are in docs/evidence/product-portfolio-*.png and product-portfolio-browser.json.

Full local verification: **79 backend tests passed**, including actual Temporal; **six frontend tests passed**; web/Codex TypeScript and production builds passed; Ruff and diff whitespace checks passed. Reloaded the API, worker, scheduler and Watchtower with private detached logs; paid execution remained disabled. Independent CI for this implementation is recorded below once completed. Render/Daytona setup requests were already emailed; no duplicate notification or new hosting expense was introduced.


### Verified portfolio/recovery checkpoint

Implementation commit **5562ab9** passed the complete independent GitHub workflow: https://github.com/totnui555-commits/Codex-2/actions/runs/39438988851 . All **79 backend tests** with actual PostgreSQL/Temporal, six frontend tests, TypeScript, production builds and Ruff passed. No test was skipped to obtain this result. Current detached services have live heartbeats; the authenticated audit check is valid, model spending remains THB **0.1241**, reservations are zero and paid execution remains disabled. Actual runtime/CI receipts: docs/evidence/portfolio-runtime.json and portfolio-ci.json.

Executed an additional actual local recovery drill: pg_dump custom-format database and development artifact archive were encrypted in the ignored private backup directory (files 0600). Decrypted the backup into a newly created restore_drill_* PostgreSQL database, verified all audit chains, restored the product record and verified all **six** artifact content checksums from separately extracted backup bytes. Restricted company_api role sees no products without tenant context and the restored product with correct context. Removed the temporary restore database after verification; no traffic or primary database was switched. Evidence: docs/evidence/local-recovery-drill.json. This is a local development recovery result using the existing private artifact encryption key, not production PITR, offsite disaster recovery, independent recovery-key custody or Temporal-history recovery.

Rechecked the founder-confirmed Render workspace after CI: no web services exist. Existing free staging Blueprint apply, Daytona authentication, public gateway and production provider setup remain external account/platform gates. The authorized setup emails and persisted Inbox requests already describe these actions; no duplicate email or extra hosting expense was introduced. The draft PR description now reflects the complete current implementation. Final CI/runtime/recovery evidence sync contains documentation/evidence only and skips redundant CI; the full Master Prompt production acceptance remains incomplete.

## Kingdom Edition v2: implementation started — 2026-10-20

Read current repository, operational evidence, Next.js instructions and the supplied v2 specification. The founder explicitly asks to preserve Office and add this edition; keep Office as an independent legacy route and make Kingdom the new default. No office floors/tower geometry will be reused in the island scene. Backend, actual workers, provider status, budgets, security controls and paid execution policy are preserved.

ADR-KINGDOM-3D and the implementation roadmap now describe original Blender assets, a versioned twelve-landmark registry, stable persisted-role citizen identities, deterministic paths, authoritative execution/incident projections, interactive dashboards, camera controls, quality/accessibility and browser acceptance. New work is in progress, not yet a completed visual milestone. No additional inference or hosting spending is authorized by the art revision.


### Kingdom implementation detail

Authored original island/citizen Blender sources, reproducible generation script and self-contained GLB exports. Twelve landmark roots, separate cottages, timber-frame houses, layered roofs, stone castle turrets, elevated independent lighthouse, cobbled streets/steps, foliage/gardens, market props, pier and boat replace the visual metaphor in Kingdom. No office geometry is reused. High/balanced/low island geometry budgets are 254,921 / 140,127 / 63,789 triangles; the original citizen is 2,652 triangles and shares per-part GPU instances across the cast. Source files are preserved, and asset validation checks all landmark names/parts/LOD ordering and external-dependency absence.

Frontend uses stable tenant+persisted-role citizen identities and a baked connected path graph. Work animations require matching real running task/run records; approval and quarantine destinations/markers use actual state. Local breathing/footsteps and water are explicitly cosmetic. Lighthouse color comes only from actual open incident severity, independent from monitor heartbeat. Inspectors connect to the unchanged authenticated dashboards. Added camera presets/follow/reset, quality/labels/reduced-motion controls, GPU error fallback and keyboard-accessible landmark/citizen lists. Both Dockerfiles now copy public GLB assets into standalone output; otherwise a production build would omit the new scene files.

No paid model job or hosting service was created for this visual revision. Existing full-company hosted coding/release/provider blockers remain distinct. Current implementation is being verified; screenshot/performance acceptance is reported separately below.


### Verified Kingdom functional and visual acceptance

Executed the real authenticated browser acceptance against the running company: all twelve landmark inspectors, real Watchtower dashboard, incident count matching the server, stable citizen identity/evidence inspector, follow/presets/reset, accessible map, actual zero-cost internal task creation/event visibility, task persistence after reload, task cancellation, legacy Office render and mobile no-overflow. The final run explicitly requires a visible 3D canvas before saving the desktop screenshot. No page errors. Receipt: docs/evidence/kingdom-browser.json. Internal acceptance projects were paused afterward; actual worker/scheduler/Watchtower heartbeats remain live and the audit chain valid (kingdom-runtime.json).

Fixed a false WebGL-failure transition caused by normal canvas disposal during view switching/development refresh. The context-loss listener now belongs to the mounted canvas lifecycle and is removed on cleanup. Switching to reduced motion uses demand rendering instead of continuously redrawing an unchanged scene. The default has ambient animation; no backend work is inferred from it.

Captured actual rendered screenshots: kingdom-desktop.png, kingdom-lighthouse.png, kingdom-citizen.png, kingdom-mobile.png and kingdom-accessible.png. The original captured interaction excerpt is encoded as kingdom-walkthrough.mp4, **40 seconds at 3× speed**, with no generated/static substitute footage. The video is an excerpt of actual local interactions, not a separate live hosted deployment.

Local verification: **79 backend tests** including real PostgreSQL/Temporal and **14 frontend tests** passed, TypeScript passed, asset structure/LOD validation passed, and Ruff/diff checks passed. No new model call or hosting charge occurred; recorded spend remains THB **0.1241** and paid execution false. A new live hosted coding animation is not claimed: existing Daytona/public gateway setup blockers remain unchanged.

Measured the actual headless renderer rather than assuming hardware acceleration: ANGLE/SwiftShader, balanced quality, 25 citizens, **200 draw calls / 208,529 triangles**, approximately **44.7 MB JS heap**. A warmed 12-second RAF sample measured **1.66 FPS**, median frame 600 ms, p95 866.7 ms in this software-only development environment. This is slow and does not pass a production frame-budget acceptance criterion. Reduced motion avoids continuous redraw; lower quality and the instant 2D view are available. Hardware GPU/mobile performance, crowd collision stress and the remaining artistic/choreography criteria are still unverified. Evidence: kingdom-performance.json. Do not describe this milestone as a certified production game or completion of every v2 requirement.


### Kingdom code and packaging checkpoint

Latest executable commit **baa0375** passed independent GitHub CI: https://github.com/totnui555-commits/Codex-2/actions/runs/39445811163 . Actual PostgreSQL/Temporal, **79 backend tests**, **14 frontend tests**, the twelve-landmark/LOD asset validator, Ruff, TypeScript and production builds passed. The prior implementation run was superseded/cancelled by the reduced-motion rendering change; it is not reported as a separate passing result.

The final local production web/Codex build also passed. Executed a separate native standalone server on loopback port 3100 using copied public/static assets and no model credentials. All four GLBs returned HTTP 200 and exactly matched source SHA-256; real authenticated API proxy returned 25 roles and valid PostgreSQL audit history. Shut down that test server afterward and restored the detached development web server. This validates native standalone packaging/proxy/static delivery, not a Docker image or Render deployment. Receipt: kingdom-standalone.json.

All core development services remain live, paid execution false, and recorded model spend THB 0.1241. Existing setup requests/notifications remain relevant to external production providers; none were duplicated for this visual revision. Final evidence/docs sync includes screenshots, an actual accelerated walkthrough and explicit software-performance limitations; it skips redundant CI because executable code remains baa0375.

## Island-first Apple-inspired UX revision — 2026-10-20

Founder requests greater emphasis on the existing island and a clean Apple-inspired interaction design, using the supplied image as visual direction rather than factual operational data. Implementing a full-viewport island with floating translucent navigation/inspector, system typography, blue actions, compact real overview/activity, landmark/citizen search, focus mode and responsive sheets. Existing original GLB assets, backend, budgets and independent monitoring stay intact; legacy Office remains separate. No fictional growth/revenue or chat integration is copied from the reference image. Verification is in progress.


### Verified island-first UX checkpoint

Executable commit **d268f6d** makes the island the full-viewport hero, with floating system-font glass navigation, compact truthful overview/activity panels, local landmark/citizen search, keyboard selection, Focus/Escape restore, building directory and Display controls. Mobile retains the island with a dismissible real inspector sheet. Office and operational APIs are preserved. Safety/staging notices remain above the canvas even in Focus; no actual emergency stop was triggered for this cosmetic verification. Repeated notification notices are grouped in the display only; individual security incidents remain separate and audit records unchanged.

Actual authenticated browser acceptance passed all 16 checks without page errors, including all twelve landmarks, search/empty state, Focus/Escape, mobile inspector/no-overflow, real Watchtower counts, citizen evidence, camera controls, accessible fallback, real zero-cost task event/reload persistence and preserved Office. The verification task was cancelled and its project paused. Receipt: docs/evidence/kingdom-apple-browser.json. Actual screenshots: kingdom-apple-wide.png, kingdom-apple-desktop.png, kingdom-apple-focus.png, kingdom-apple-lighthouse.png, kingdom-apple-citizen.png, kingdom-apple-mobile.png, kingdom-apple-mobile-inspector.png and kingdom-apple-accessible.png.

Local frontend tests (**15**), TypeScript, Ruff and asset validation passed. Independent CI completed successfully for d268f6d: https://github.com/totnui555-commits/Codex-2/actions/runs/39449820405 . Its named PostgreSQL migrations, actual Temporal/pytest, Ruff, asset validation and frontend test/typecheck/production-build steps all succeeded. The backend suite contains 79 tests. Raw CI log download was blocked by the artifact host; the successful step conclusions are available through the GitHub API and recorded in kingdom-apple-ci.json. No test was disabled for this revision.

No model invocation or hosting expense occurred; recorded spend remains THB **0.1241**, paid execution disabled. The prior warmed software-renderer ~1.66 FPS limitation remains unresolved: this UI revision does not certify production GPU/mobile performance, final art quality or the entire Master Prompt. External secure coding/deployment blockers remain unchanged. This evidence-only follow-up skips redundant CI; executable code remains d268f6d.


## Online trial deployment attempt — 2026-10-20

Founder explicitly requests an online trial. Applied Render deployment skill, checked current deploy/health/free-service/environment documentation, reconfirmed the founder-selected workspace and available free Singapore PostgreSQL, and verified no existing web services. The current connector newly supports Docker creation; attempted the already-tested staging Dockerfile from the pushed implementation branch on the free plan, auto-deploy disabled, with private generated setup/session secrets. Secrets remain ignored/0600 and were not printed, committed or sent to an unapproved destination.

Render rejected creation with HTTP 400: repository URL invalid or unfetchable. GitHub confirms Codex-2 is PRIVATE. A follow-up resource listing still shows no web service. No deployed URL, successful build, spending or runtime is claimed. Repository visibility was not changed. The remaining account action is granting Render GitHub App access to Codex-2 and applying the committed Blueprint, which securely links the existing database. No authenticated Dashboard browser/Blueprint-apply tool is available in this session, and the connector does not expose PostgreSQL connection credentials. The exact founder steps and direct Dashboard link are maintained in docs/RENDER_STAGING_TH.md. Current UI/CI evidence remains valid; this attempt changes documentation only.


## Shared Apple-inspired operational interface — 2026-10-21

Founder requests the system-style design on conventional windows as well as the island. Added a scoped console visual system for Office, Overview, Projects, Tasks, Agents, Opportunities/Portfolio, Watchtower, Approvals, Inbox, Finance, Build Inspector, Audit, Settings and dialogs. New system font stack, neutral surfaces, blue controls, translucent navigation/topbar, consistent rounded cards, readable secondary text, focused form fields and semantic success/warning/danger colors replace the former olive/yellow treatment. Sign-in and installation setup use the same typography and controls. Operational data and API action handlers are unchanged; Kingdom retains its independently scoped full-viewport shell.

Responsive review found long evidence URLs overflowing Inbox cards and intrinsic grid sizing widening mobile setup. Fixed wrapping and bounded grid tracks instead of clipping evidence. Sidebar scrolls to all controls; mobile fields use 16px text to avoid automatic form zoom, keyboard focus is visible and reduced motion disables decorative transitions. Actual local acceptance and live deployment receipts follow below. No new model job, paid hosting plan or production autonomy is introduced by this revision.


Local verification for executable commit **f4dce7d**: frontend **15 tests passed**, web/Codex TypeScript passed, Ruff passed, and the real authenticated browser script passed **31 checks** without page errors or database mutations. Checks cover eleven desktop consoles, Settings/forms, keyboard focus in a project dialog, preserved Office, thirteen mobile routes, mobile navigation, private login/setup fields and the isolated Kingdom shell. Actual screenshots and receipt use docs/evidence/system-console-*. Initial test-selector mismatches were corrected to match accessible labels/counts; actual Inbox/setup overflow was fixed in the stylesheet and verified again. No control or API was stubbed.

Confirmed the founder successfully applied the existing Blueprint: service srv-dbc18bpsrm7s7399skdg is Free/Singapore, auto-deploy off, at https://company-os-staging-38tn.onrender.com; prior commit 2014ea4 was live and the hosted PostgreSQL health endpoint returned 200. Triggered exactly one manual deployment for f4dce7d (dep-dbc2440n74is73f3n4rg). Build acceptance, terminal hosted status and public checks are recorded separately when completed; a trigger response is not treated as a live release.


### Verified shared interface online

Independent CI passed for **f4dce7d**: https://github.com/totnui555-commits/Codex-2/actions/runs/39532610810 . Actual PostgreSQL migrations and Temporal/pytest, Ruff, original world asset validation, frontend tests, TypeScript and production build steps all succeeded. The unchanged backend suite contains 79 tests; the local frontend suite passed 15. The intermediate abe18e6 workflow was superseded/cancelled by the final label/mobile-input correction, not reported as a separate success. Receipt: system-console-ci.json.

Render deployment **dep-dbc2440n74is73f3n4rg** reached **live** on the existing Free Singapore service for f4dce7d. Verified the real public HTTPS login, new system styles, production stylesheets (200), actual PostgreSQL health (200), unauthenticated snapshot denied (401), 390px mobile width, 16px mobile input sizing and masked setup-token field. No page errors. The public check made no owner-login attempt, database mutation or model call; authenticated operational interactions were tested against the actual local PostgreSQL/API rather than using the founder's hosted password. The isolated APIRequestContext initially bypassed required session proxy routing; rerunning HTTP probes through the environment-aware HTTP client passed. Startup logs included temporary API proxy refusal while Python was initializing; readiness remained gated until the API completed startup and Render marked the deploy live.

Screenshots: system-console-overview.png, system-console-office.png, system-console-projects.png, system-console-agents.png, system-console-finance.png, system-console-settings.png, system-console-dialog.png, system-console-mobile*.png, plus actual online system-console-hosted-login.png and system-console-hosted-mobile.png. Receipts: system-console-browser.json, system-console-hosted-browser.json and system-console-deployment.json. README/Thai deployment guide now reflect the actual live trial instead of the resolved private-repository setup blocker. No paid hosting upgrade, external message or inference job occurred. This is a UI release on management-only staging; the existing hosted-worker/provider and 3D software-performance limits are unchanged. Final evidence-only commit skips redundant CI; deployed executable code remains f4dce7d.


## Bounded Kingdom renderer investigation — 2026-10-21

Continued from the deployed shared UI with a bounded performance investigation. Read the game-performance-optimization skill and its loop reference. This environment has no game-dev CLI or admitted sealed-run adapter; measurements are explicitly ordinary Playwright/SwiftShader telemetry, not sealed game-dev bundles, hardware proof or a certified GPU optimization. Defined one candidate iteration limited to kingdom.tsx, targeting a 20% lower median frame time at the same 1440×1000 canvas, balanced geometry and 25 persistent citizens. Existing warm 1.66 FPS evidence used another viewport/layout; it was not reused as the baseline.

Actual baseline: 1.339 FPS, median 799.9ms, p95 866.7ms, 200 draw calls / 208,529 triangles. Candidate: static-island Lambert diffuse materials in low/balanced modes, retaining PBR in High, original geometry, shadows, event projections and citizen count. TypeScript and 15 frontend tests passed before capture. Candidate measured 1.376 FPS, median 766.6ms and p95 966.7ms. Median changed only 4.16%, below the target, and p95 worsened. No causal/significant performance improvement is claimed. Candidate rejected and fully reverted; island component exactly matches the accepted source and no Render deployment was triggered. The iteration limit is exhausted, not silently extended. Before/after screenshots, exact rejected patch (its reconstructed SHA matches the measured candidate) and JSON receipts are in docs/evidence/kingdom-perf-* and kingdom-performance-{goal,comparison}.json.

Implemented scripts/profile_kingdom_browser.py as a reusable, read-only local profiling command with explicit workload/units/renderer/build metadata, source/asset checksums, strict unique evidence names, no overwrite, masked local credential handling and separate reduced-motion screenshots. Its real short smoke run completed with no page errors; no task/data mutation or inference call occurred. Ruff passed. This improves reproducibility of subsequent investigations; it does not resolve slow software rendering or certify production performance. Existing public UI deployment f4dce7d and all provider/budget controls remain in place.


### Closed compositor experiment; added owner-visible diagnostics

After closing the lighting experiment, defined one separate compositor experiment with its own fresh baseline and one-iteration limit. This tested software-renderer detection plus opaque/no-blur floating panels, without changing PBR, geometry or citizens. Baseline median/p95 766.7/866.6ms; candidate 849.9/999.9ms. Target missed and both measures worsened. This second candidate was also rejected and fully reverted. No rendering optimization is retained, and no meaningful improvement, causal bottleneck identification or hardware acceptance is claimed. Exact inactive patch, source/asset-hashed runs, goal and comparison are recorded under kingdom-compositor-* and kingdom-profile-compositor-*. Both bounded experiments are closed, not extended into further optimization iterations.

Implemented a separate diagnostic capability: Kingdom Display → Measure performance (10s) → Download performance report. The scene counter comes from Three renderer.info.render.frame; browser RAF pacing is reported separately. Reduced motion, fallback/error and unready scenes cannot start a measurement. Hidden tabs, canvas resize, renderer restart, quality/view changes and explicit cancellation invalidate or abort the window. Reports contain counts, quality, resolution and renderer metadata, not task/message content, identities, session data or model credentials. Nothing is sent to a provider. Material quality, shader, shadows and geometry remain the accepted original versions.

Six new meaningful tests reject hidden/resized/restarted/incomplete windows and stalled scenes, and ensure browser callbacks cannot be mislabeled as rendered scene frames. Frontend total is now **21 passing tests**; TypeScript passed. Actual browser acceptance verifies scene-frame counting, JSON download and privacy keys, explicit cancel, reduced-motion guard and mobile layout. New quality readiness handling waits for the loaded LOD; reselecting the current quality must not falsely clear readiness. Final browser/CI/deployment evidence follows after verification. Reusable profiler commit dd87dd9 independently passed CI: https://github.com/totnui555-commits/Codex-2/actions/runs/39587046902 . No paid hosting upgrade or inference was introduced.


### Real event-delivery regression found and fixed

The broader Kingdom browser regression created a real zero-cost task but timed out before it appeared. Investigated rather than relaxing the timing assertion: the database contained the blocked task, the UI said Live connection, but an independent browser EventSource observed no events. Direct API SSE had no content encoding; the actual Next proxy returned gzip. Its compressor buffered small company events. Fixed the API security middleware to retain `no-store` and add `no-transform` specifically for text/event-stream responses, so Next preserves streaming rather than buffering. Normal JSON caching policy remains no-store.

Actual local proxy acceptance after the change received the exact task.created aggregate and updated the real Tasks UI in **1.152 seconds**, before the 30-second polling fallback. SSE responses were uncompressed and carried no-transform; reload persistence passed. Its project was paused before task creation and task/project cleanup confirmed. Added scripts/verify_realtime_browser.py with always-on cleanup and exact event/aggregate correlation. Cancelled and paused the original failed verification task/project (receipt: kingdom-diagnostics-regression-cleanup.json), and made the existing broad verifier clean up in finally and pause its project before task creation. Backend verification with actual PostgreSQL/Temporal passed **79 tests**. This is a functional transport fix, separate from the rejected rendering experiments.


Final local acceptance: **79 backend tests** with PostgreSQL/Temporal and **21 frontend tests** passed; TypeScript, Ruff and formatting passed. Diagnostic browser checks passed **seven** cases, including real render-counter JSON export, privacy field allowlist, cancel, camera reset, reduced-motion guard and mobile layout. The full **16-case** Kingdom regression passed after the stream fix, including actual event visibility/reload persistence, all landmarks, Office, Watchtower, mobile and audit. The internal task was cancelled and its project paused; model calls remain zero for these checks and recorded spending THB 0.1241. A second independent stream probe verified exact task.created delivery and UI visibility in **1.155 seconds** with no-transform/uncompressed headers and cleanup. Prior visual checkpoint artifacts are retained; new regression captures use kingdom-diagnostics-regression-* rather than overwriting them. Final deployment/CI/public receipts follow below.


### Verified diagnostic and live-stream release

Executable **94c1079** passed independent CI: https://github.com/totnui555-commits/Codex-2/actions/runs/39590808427 . PostgreSQL migrations, actual Temporal/pytest, Ruff, original asset validation, **21 frontend tests**, TypeScript and production build steps succeeded. Local backend **79 tests**, seven diagnostics checks, sixteen Kingdom regression checks and five real proxy-event checks passed. Receipts identify the exact local test scopes; no test failure was hidden by extending the event deadline or simulating events.

Render **dep-dbc9uie1egvs739vt040** reached **live** for 94c1079 on the existing Free/Singapore service. Public HTTPS login, production CSS including diagnostic controls, PostgreSQL health, authentication-required snapshot, mobile width/inputs and masked setup fields passed without page errors. The public probe did not authenticate as the founder or claim hosted owner/event actions; exact source/deployment plus real local proxy acceptance provide the current release evidence. Actual authenticated operation on the founder's device remains available through the existing account. Receipts: kingdom-diagnostics-{ci,deployment,hosted-browser}.json; actual browser screenshots and frame export are saved separately. Earlier f6832dd and 8ea735f trial deploys completed; final acceptance is anchored to 94c1079.

No paid plan upgrade, production worker provisioning, email or model inference occurred. The two rejected render candidates remain inactive; slow software rendering and real GPU/mobile acceptance are unresolved. The shipped improvements are trustworthy client diagnostics, correct quality/camera cancellation/readiness, and unbuffered authenticated company events. The benchmark/profiling CLI is reproducible and its runs remain ordinary telemetry, not sealed hardware evidence. Final documentation/evidence-only commit skips redundant CI and does not change the deployed executable commit.


## Per-request production CSP hardening — 2026-10-22

The ordinary application UI previously allowed inline and eval scripts globally. Updated the Next.js 16 app to generate an unpredictable nonce per page request in `apps/web/src/proxy.ts`, pass that CSP into SSR, and force request rendering at the root layout so Next can attach the nonce to framework and RSC scripts. Production script policy now omits both `unsafe-inline` and `unsafe-eval`; development allows eval only for React diagnostics. Inline style attributes remain allowed because the existing island and dashboard use runtime layout and transform styles. CSP still is not a substitute for output encoding or XSS review. The security guide records this limitation and the remaining distributed login limit / production review.

The first production probe caught that Next had not included the project-root proxy in the standalone build. Moving it beside `src/app` made Next report the Proxy route and enabled the nonce path. Local standalone Chromium then loaded the production shell twice: both responses carried distinct 48-character nonces, all **11 scripts** matched each request's nonce, all **8 static assets** loaded, and there were **zero CSP violations**. Evidence: `docs/evidence/csp-browser.json` and `csp-login.png`.

Frontend suite: **23 tests passed** (including two CSP policy tests); web TypeScript and production standalone build passed. Independent CI run **39708000546** succeeded across migrations, real PostgreSQL/Temporal backend suite, Ruff, island asset validation, frontend tests/typecheck and production build (`docs/evidence/csp-ci.json`). The exact interactive check is reproducible with `CHROMIUM_PATH=/usr/bin/chromium python scripts/verify_web_csp.py --url http://127.0.0.1:3101/` after building/starting the standalone server. It made no API mutations or model calls. Render deploy **dep-dbcmpjgm7kps73c8l580** reached live for commit **4762efa** on the existing free staging service. Public desktop and 390px mobile login-page checks each returned 200, loaded 11 nonce-authorized scripts and 8 static assets, observed zero CSP violations and no horizontal overflow. The two public requests carried distinct nonces. Founder authentication was not attempted; hosted evidence covers the public login surface, while complete authenticated Kingdom actions remain verified locally in prior receipts. No API mutations, inference or paid plan upgrade occurred. Receipts: `csp-deployment.json` and `csp-hosted-browser.json`. No API behavior, database, cost limit or theme changed in this increment.
