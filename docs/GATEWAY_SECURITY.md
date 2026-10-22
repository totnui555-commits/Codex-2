# Coding model gateway enforcement

Hosted coding capabilities are signed, expire after five minutes, and bind both a run ID and organization ID to the sandbox-model-gateway audience. The trusted coding orchestrator supplies the organization independently of the model's brief. Older capabilities without an organization claim are rejected.

Every gateway transaction sets PostgreSQL's transaction-local tenant context from the verified claim. The run must belong to that organization, be running, own the task's current unexpired lease, and retain a budget reservation. The company must permit paid execution and a build/growth mode, and neither STOP ALL nor a project pause may be active. These checks also run while forwarding each streamed provider line and before returning a non-streamed response.

Revocation closes the upstream connection and stops forwarding output. This is not a guarantee that a remote provider has not already incurred charges. The gateway preserves available usage and keeps the reservation for reconciliation; uncertain usage is never recorded as a completed known-cost call. State transitions create redacted audit events. Transport interruption before a trustworthy receipt remains an accounting uncertainty.

Malformed request objects/tool lists, hosted provider tools and background provider execution are rejected before reserving a call allowance. Request bodies are bounded during receipt. The server fixes the coding model, output-token ceiling, store=false and background=false. Provider credentials remain on the trusted server.

Verification uses real PostgreSQL and the actual restricted company_api RLS role. Controlled HTTP transports in security tests represent provider success, revocation and streaming boundaries; these are explicitly tests, not evidence of a live hosted Codex/Daytona integration. The external hosted coding benchmark still requires Daytona account authentication and a deployed HTTPS gateway.
