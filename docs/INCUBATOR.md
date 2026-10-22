# Evidence-based incubation

The Opportunities screen now contains a working Product Incubator backed by PostgreSQL's existing tenant-scoped `experiments` and `customer_metrics` tables. No migration is needed: these document tables already exist and retain the same RLS and service-role boundaries.

An authenticated owner defines the project, hypothesis, binary success metric, minimum sample size and stop/continue thresholds before opening evidence collection. States are draft → running ↔ paused → concluded. Concluded experiments are frozen. Starting an experiment only changes the evidence register; it grants no permission to launch a campaign, buy traffic, invoke a model or publish a product.

Each observation batch requires a unique source reference, sample/success counts and a checksum-verified artifact from a task in the same project. The artifact checksum establishes storage integrity, not truth of the reported measurements. These observations are explicitly owner-reported and not independently verified customer demand or sales. Do not submit participant identifiers or other personal information. Sample independence and source methodology must be reviewed separately; the platform cannot infer them from aggregate counts. Correct a mistaken batch by concluding the experiment and opening a documented replacement, rather than overwriting its history.

Organization locks serialize writes; expected versions reject stale mutations. Identical source-reference retries return the existing receipt without recounting. Conflicting reference reuse is rejected. Cross-project and cross-tenant artifacts are rejected; company STOP ALL and project pause prevent starts/new observations. Pausing and concluding remain possible to safely close the evidence register.

The recommendation uses a Wilson 95% interval for the supplied binary observations. Below the predeclared minimum sample size the result is inconclusive. Continue requires the lower bound to meet the continue threshold; stop requires the upper bound to meet the stop threshold. Everything else is inconclusive. Recommendations never authorize spending or modify the signed payment-provider revenue ledger.

Endpoints:

- `POST /experiments`: define a draft.
- `POST /experiments/{id}/actions`: start, pause or conclude with `expected_version`.
- `POST /experiments/{id}/observations`: submit an evidence batch with `expected_version`.
- `GET /experiments/{id}/observations`: inspect evidence receipts.
- `GET /snapshot`: contains the latest tenant-scoped experiments and aggregates.

Verification: five backend tests cover lifecycle/persistence, receipt idempotency, stale writes, artifact/project isolation, tenant isolation, authentication, STOP ALL and statistical uncertainty. The real browser check creates an explicitly internal zero-observation experiment, reloads it, exercises start/pause/conclude and verifies the audit chain and responsive layout. It does not manufacture customer metrics. Evidence is in `docs/evidence/incubator-browser-check.json` and desktop/mobile captures. A real public-source candidate was also linked to a paused validation backlog and draft experiment; `source-to-incubator.json` records the link. Its thresholds are proposed defaults, not empirically established business targets.

Hosted coding, customer acquisition, production email OAuth, cloud object storage and independent measurement-provider ingestion remain separate unverified work. This increment does not complete the full production roadmap.
