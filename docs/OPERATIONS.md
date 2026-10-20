# Operations and recovery

## Process model

FastAPI serves management/policy/events. Temporal worker executes bounded activities. Scheduler drains transactional outbox rows, starts stable-ID workflows, performs one public-source research batch per UTC day and delivers email. Watchtower separately inspects evidence, leases and audit integrity every 15 seconds. All persist state in PostgreSQL; no browser needs to stay open. Temporal dependency waits use durable timers and a bounded 24-hour wait window.

## Stop / investigate / resume

Use authenticated Settings → STOP ALL. It closes future execution gates, quarantines eligible tasks and revokes model-gateway capabilities at their next request. Current bounded remote calls may finish; stop is not a claim that remote resources have already terminated. Inspect provider sandbox status and recorded outcomes, cancel remote sessions if required and revoke scoped tokens at providers. Watchtower can stop work; it cannot authorize spending or production.

Review incidents and the audit chain. Restore from an independently retained audit-head checkpoint if history integrity is suspect. Never erase or edit audit rows to hide an incident. Resume opens company gates but does not automatically release quarantined tasks. Reconciliation and a new explicitly reviewed task are required after quarantine.

## Retry and recovery

Outbox delivery is at least once with stable workflow IDs, capped retries and a dead-letter state. Investigate dead-letter rows through an administrator before resetting them. Paid activity retries are disabled at Temporal level; a crashed paid activity becomes a blocked review case instead of silently double-spending. Reservation amounts remain held when usage is unknown. Task attempts are bounded. Approved artifact changes require a new approval; an existing consumed/expired approval cannot authorize another action.

Gmail 429s retry with bounded backoff. A network error with uncertain delivery is recorded as unknown, requires inspection of Gmail, and is not blindly resent. A disconnected channel retains its in-app request. Never infer approval from delivery, email replies or silence.

## Backups

Use `scripts/backup.sh` with an encrypted destination volume for private development backups; production should use managed PITR and separate encrypted artifact backups. Validate the database name and restore into a new isolated instance using `scripts/restore.sh`. Run migrations/role grants, verify audit hashes and object checksums, validate tenant isolation, then explicitly switch traffic. Back up Temporal state independently; the development SQLite file needs a consistent SQLite backup or a stopped service before copying.

Target RPO/RTO are founder decisions; none are guaranteed by this repository. A real disaster-recovery drill remains a production acceptance requirement.

## Health

`GET /health` verifies database reachability, not every external integration. Authenticated `/integrations` reports configuration only, not provider readiness. Authenticated `/metrics` exposes API request counts; run/task/ledger metrics are computed from snapshots. Watchtower liveness must be monitored as a separate process. Production distributed rate limiting, exporter instrumentation, secret rotation, provider token renewal and cluster alerts are deployment responsibilities.
