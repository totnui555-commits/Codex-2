# Cost controls

New organizations default to research_only and **paid execution disabled**. THB 2,000/month, 500/project, 100/task, 30/run and two concurrent paid reservations are ceiling proposals, not evidence of founder consent or provider prices. Owner policy opt-in is audited. Provider credentials, model prices, dated USD→THB FX and dated sandbox minute prices are prerequisites.

Reservations lock the organization row, account for company/month/project/task/run/concurrency hierarchy and are idempotent by run ID. A worst-case model estimate uses bounded input bytes and max output tokens. Hosted coding also reserves a conservative 20 sandbox minutes for build/QA and cleanup deadlines. If the estimate exceeds a ceiling, the job cannot begin. Gateway limits per-request input bytes/output tokens, per-run request count and cumulative reserved cost. No model/provider key enters generated code.

Usage is reconciled from provider token telemetry and the configured price/FX snapshot, explicitly marked estimated until billing reconciliation is available. Sandbox costs currently use conservative reserved-minute estimates rather than verified provider invoices. Hosting/storage/email overhead and net settlement are unknown unless ingested; total company profit is never inferred. Unknown usage retains reservations. An actual reconciled overrun stops the company and requests founder review.

Reservations/usage are in THB. Revenue keeps exact provider minor units in its native currency and is never silently converted or summed across currencies. Multi-currency price/FX document contracts exist; full price management and live FX ingestion are not implemented. Inspect original currency and source telemetry before commercial financial decisions.
