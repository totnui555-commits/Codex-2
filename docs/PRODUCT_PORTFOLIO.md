# Product hypotheses and evidence

Open **Opportunities → Product Portfolio** after founder authentication. Select an incubation project and record the problem, proposed customer and MVP scope. A record is a hypothesis, not an operating business. Leave price and costs blank when unknown; values are integer satang/cents. Contribution and break-even are estimates and never enter the verified revenue ledger. Costs remain explicitly incomplete.

Link an experiment from the same project. Experiments retain their own evidence receipts, sample counts, uncertainty and conclusion. No samples means inconclusive; attaching a draft experiment does not validate demand. Revisions prevent stale writes. Archiving freezes subsequent changes.

Prototype attachment requires all of:

- A completed same-project Daytona/Codex run and task.
- A verified `verified_pull_request` artifact with `independent_hosted_QA` provenance.
- Readable encrypted artifact bytes matching the stored SHA-256.
- Successful trusted QA in a sandbox distinct from the build/export sandbox.
- An allowed GitHub repository PR whose current head matches the full recorded commit.

The server reads GitHub outside the organization lock and restores transaction-local tenant context before rechecking the product revision. A report, URL alone or an unverified coding output cannot become a checked prototype. Provider failures leave the product unchanged.

**Check remaining release gates** displays missing prototype/validation evidence and the independent release/deployment gate. This registry never authorizes publication. No production deployment or hosted prototype is present in the current installation.

Source discovery uses the official public API with a 90-day publication window. Source content versions are retained with checksums; retrieval timestamps alone do not create duplicates. Community discussion is unvalidated evidence, not proof of customer demand. Existing installations must reapply `scripts/database_roles.sql` to grant workers INSERT access to source snapshots, without granting update/delete.

Validation uses actual PostgreSQL, authenticated API/browser persistence, tenant isolation and controlled GitHub/Daytona boundary tests. Controlled provider responses are not live external execution evidence. Actual source receipts and browser results are under `docs/evidence/`.
