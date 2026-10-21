# Shared operational interface

The conventional console and login/setup screens use a system font stack, neutral #F5F5F7 background, #007AFF actions, white cards, subtle borders and translucent navigation. No external fonts, visual dependencies or tracking resources were added. The original Office scene remains intact; only its surrounding controls change.

`system-console.css` is scoped to `.console-mode` and `.system-login`. Kingdom retains `.kingdom-mode` and its existing independent shell. Semantic red/amber/green treatments keep risk and operational status distinct from the blue interaction accent. Provider status, financial values, approvals and staging notices still come from the authenticated API.

Responsive layouts support scrollable tables/task lanes, wrapped evidence URLs, mobile navigation, full-size form fields and dialogs. Controls retain keyboard focus indicators and respect reduced motion. Blur has an opaque fallback. This is an Apple-inspired web interface, not an Apple product or a claim of formal accessibility certification.

Verification: `npm run test`, `npm run typecheck` and `python scripts/verify_system_console_browser.py`. The browser script uses the ignored local owner credentials and actual local API, navigates existing pages and opens forms without submitting them. It checks mobile overflow, navigation, setup field privacy, modal focus and the independent Kingdom shell. Evidence files use `docs/evidence/system-console-*`. Hosted login/health/static checks are recorded separately from authenticated local acceptance.
