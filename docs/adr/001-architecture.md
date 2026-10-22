# ADR 001: Persistent modular monolith and isolated execution
Accepted 2026-10-20. FastAPI owns tenant authorization, events, audit, budgets and policy. PostgreSQL transactions serialize budget and aggregate mutations. Temporal owns durable waits/retries and scheduled delivery. Workers receive identifiers and retrieve scoped data, never broad application secrets. Watchtower is a separate service with a stop-only role. Web rendering consumes snapshots and authenticated replayable events; it never invents agent activity. Provider integrations fail closed when missing or unauthorized. Hosted sandbox execution is distinct from host development and test doubles.

```mermaid
flowchart LR
 Founder --> Web[Next.js / R3F]
 Web --> API[FastAPI / owner authorization]
 API --> DB[(PostgreSQL / audit / events / outbox)]
 API --> Temporal
 Temporal --> Specialists[Agents SDK specialists]
 Specialists --> Sandbox[Daytona / Codex SDK]
 Sandbox --> QA[Independent verification]
 QA --> PR[GitHub draft PR]
 Watchtower --> DB
 Watchtower --> Stop[Quarantine / stop]
 DB --> Mail[Email delivery worker]
 Approval[Artifact-bound founder approval] --> Release[Protected side effects]
```
