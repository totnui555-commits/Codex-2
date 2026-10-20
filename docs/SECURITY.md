# Security model and remaining review

Authenticated owners are the only API principals allowed to change policy, budgets, company mode, approvals or global pause. Passwords use Argon2. Sessions are expiring HttpOnly/SameSite cookies with server-side version revocation. Unsafe requests reject foreign Origin/cross-site Fetch Metadata. Production requires HTTPS secure cookies and ingress limits. Session secrets and bootstrap tokens have no production defaults.

Every domain fetch uses tenant scope; PostgreSQL row policies add defense in depth when using restricted runtime roles. Services require separate database roles: workers and Watchtower cannot grant themselves paid authorization, change role policy, change limits or approve actions. Migration credentials are never given to generated code.

Events and audit rows are appended transactionally with the business mutation/outbox. History triggers prevent update/delete; a hash chain detects privileged tampering. A database administrator can still replace the chain/head: independently anchor audit heads and use managed retention for stronger tamper evidence. Runtime audit roles do not possess delete or table-owner privileges.

Budgets serialize on organization row locks, include outstanding reservations and do not trust model self-reporting. Approvals bind action, tenant, exact SHA-256, target, maximum exposure and expiry; consumption is one-time. Owner Inbox responses do not grant sensitive approvals. Critical operations are not implemented as generic shell or model tools.

The hosted coding adapter uses a preaudited snapshot, a unique sandbox per build/QA, bounded runtime, no production credentials, limited egress and short-lived run-scoped model gateway. Code exports reject traversal, sensitive paths, dependency/infrastructure changes, excessive sizes and invalid checksums. Independent QA executes code in a second hosted environment. No untrusted code runs on the API/worker host. The included snapshot and provider network controls still need a real isolation/security test before production use.

Prompt injection controls are architectural: retrieved sources and repositories are untrusted data; planners can return only bounded typed DAGs using configured roles; agents have no policy/spend/approval endpoints or broad service credentials. These controls reduce authority, not a claim that prompts themselves prevent all injection.

Outstanding: penetration test; nonce CSP; distributed login limiting; stronger scoped secret rotation; OAuth lifecycle/UI; automatic short-lived GitHub App token renewal; sandbox isolation proof and remote cancellation/reclamation tests; deployment-specific data retention/PII review; full consent and privacy review for commercial operation. No legal jurisdiction or compliance certification is assumed.
