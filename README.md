# AI COMPANY OS

A persistent, founder-governed venture studio with a live isometric office. Built from an empty repository. **This is an implemented local platform with explicitly blocked external-provider milestones, not a completed production autonomous company.** See [PROGRESS.md](PROGRESS.md) and [the acceptance plan](docs/IMPLEMENTATION_PLAN.md).

## Run locally

Python 3.12+, Node 22+ and Docker are required. No paid credentials are required to run management, governance, public-source discovery and the office. In this managed cloud environment, add `-f docker-compose.yml -f docker-compose.cloud.yml` to Compose commands so build/runtime CA trust is preserved.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-deps -e .
npm ci
cp .env.example .env
# Set a private PostgreSQL password, SESSION_SECRET (32+ random chars), BOOTSTRAP_TOKEN,
# POSTGRES_PASSWORD, and SECURE_COOKIES=false for loopback-only HTTP development.
docker compose up --build -d
```

Open http://localhost:3000. Choose **Initialize installation**, enter the setup token from your private environment configuration, choose a strong password and create the founder account. Bootstrap works once. Never commit `.env`. The current execution workspace is already initialized; private local sign-in details are in `.local/owner-credentials.json` with mode 0600.

For host development instead of container app services:

```bash
.venv/bin/alembic upgrade head
.venv/bin/python -m company_os.bootstrap
.venv/bin/uvicorn company_os.api:app --host 127.0.0.1 --port 8000
npm run dev
# Separate long-running processes:
.venv/bin/python -m company_os.worker
.venv/bin/python -m company_os.scheduler
.venv/bin/python -m company_os.watchtower
```

The scheduler needs Temporal at `TEMPORAL_ADDRESS`; the browser is never the worker. The development Temporal CLI uses SQLite with a persistent volume. Production requires managed Temporal or a separately operated supported cluster, TLS, authenticated namespaces and backups.

## What works

- PostgreSQL migrations, authenticated tenant-scoped projects and DAG tasks; persistent snapshots and reconnectable event stream/outbox.
- Append-only event/audit history, hash-chain verification, PostgreSQL RLS and separate restricted runtime-role definitions.
- Atomic company/project/task/run reservations, explicit paid-execution opt-in, single-use immutable-artifact approvals and emergency stop.
- Real Temporal activity dispatch; a job with missing providers durably blocks and creates an Inbox request without invoking a model.
- Configured OpenAI Agents SDK Chief of Staff planning and specialist invocation, Daytona/Codex factory, scoped model gateway, independent CRUD harness, private checksum-verified artifacts and GitHub draft PR adapters.
- Independent Watchtower process, persistent Founder Inbox, bounded Gmail delivery retries/unknown-outcome handling.
- Daily bounded public-source discovery with actual URLs/dates, clearly heuristic scoring, idempotent opportunity-to-project/backlog creation.
- Signed live Stripe webhook ledger; test events, invalid signatures, stale signatures, duplicates and tenant mismatches are rejected/ignored correctly.
- Original six-floor R3F office, agent/floor selection, orbit/zoom/reset, accessible 2D view and operational screens tied to persisted state.

## Verification

```bash
# Isolated test database; never point TEST_DATABASE_URL at an installation with real data.
DATABASE_URL=postgresql+psycopg://company:password@localhost:5432/company_test .venv/bin/alembic upgrade head
# Apply scripts/database_roles.sql to the test database as administrator for role-boundary tests.
RUN_TEMPORAL_TESTS=1 .venv/bin/pytest -q
npm run test
npm run typecheck
npm run build
.venv/bin/ruff check apps/api/company_os scripts
```

The browser check uses the initialized local owner account and creates real verification project/task records. Run `.venv/bin/python scripts/browser_check.py` only on a local acceptance installation. Evidence is in `docs/evidence/`.

## Honest boundaries

No model, hosted sandbox or autonomous coding PR has been executed without credentials and approved spending. No real sales are claimed. No public site, production release, customer outreach, payment onboarding or paid advertising is performed automatically. The coding factory is currently specialized for the documented CRUD benchmark; arbitrary repo test manifests, deployments and preview hosting remain future work. Detailed gaps: [milestone status](PROGRESS.md), [benchmark](docs/BENCHMARK.md), [security](docs/SECURITY.md).

See [deployment](docs/DEPLOYMENT.md), [operations](docs/OPERATIONS.md), [founder guide](docs/FOUNDER_GUIDE.md), [API contracts](docs/CONTRACTS.md) and [cost controls](docs/COST_CONTROLS.md).

## Latest activation checkpoint

OpenRouter now executed two real bounded specialist jobs through Temporal, with encrypted persistent local artifacts and a founder review gate. GitHub is connected through the inherited authorized identity. The current development artifact store is local encrypted storage (see docs/LOCAL_ARTIFACT_STORAGE.md), not cloud S3. Initial research verification consumed approximately THB 0.03 for these two jobs; the second has provider-reported USD cost. Paid execution was disabled again after verification. Current setup guidance in Thai: docs/FOUNDER_SETUP_TH.md. The hosted coding/Daytona benchmark is still blocked; OpenRouter Codex routing is prepared but not live-verified in a sandbox.

The Product Incubator now supports persistent, versioned experiment criteria, owner-reported checksummed evidence receipts, idempotent counts, stop/continue/inconclusive recommendations and lifecycle controls in Opportunities. See [the concrete workflow and limitations](docs/INCUBATOR.md). Full local backend verification including real Temporal: 35 tests passed; hosted coding and production provider setup remain incomplete.
