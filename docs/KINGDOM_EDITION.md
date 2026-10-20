# Kingdom Edition v2 — world contract and acceptance

The founder supplied the complete v2 design on 20 October 2026. Their direct request preserves the original Office as a separate version; Kingdom is the new default at `/` or `/kingdom`, and legacy Office remains at `/office`. Kingdom has no office floors or tower cutaways. ADR 002 records this deliberate scope precedence.

## Data boundary

The existing authenticated FastAPI snapshot and replayable event connection remain authoritative. The world receives the same tenant-scoped snapshot as every management screen. Backend jobs, budgets, integrations, independent Watchtower, approvals and email are unchanged. No provider connection is simulated to animate the island.

`WORLD_VERSION` and the landmark registry are versioned source. Every persisted role maps to a stable citizen ID formed from organization ID and role ID, independent of display name or list order. These are persistent configured citizen identities, not a claim that a paid process runs continuously. The deterministic seed supplies avatar palette, outfit and home/position. A later dedicated agent-instance/profile table can extend this without replacing role IDs.

| Visual field | Source |
|---|---|
| citizen_id | Organization + persisted role ID |
| role / mission / ceilings | Existing role configuration |
| avatar skin / home | Deterministic identity seed and role-to-landmark registry |
| execution state / task_id / run_id | Actual task/run records; active work requires a matching running task and run |
| destination | State + role mapping; approval → post, quarantine → lighthouse |
| world position / local motion | Seeded visual profile and client interpolation on a baked connected street graph; cosmetic, not persisted execution telemetry |
| last server evidence | Linked event time or run creation time; absent evidence remains unknown |
| monitor health | Independent Watchtower heartbeat, separately from incident severity |
| beacon | Actual open incidents only; calm / advisory / critical |

Idle strolls/breathing never invoke a model. Quarantined/blocked/failed states do not animate as working. Waiting-for-approval mail markers require a real linked waiting task. No completed coding/deployment celebration is invented. Losing connection labels the last known state and stops active-work animation. Reduced motion removes waves/gait/pulsing and snaps destination changes.

## Landmarks and real dashboards

Royal Keep → Overview + Settings/STOP ALL + Approvals. Guild → Tasks. Workshop → Build Inspector. Atelier → Agents/design roles. Alchemy → Build Inspector/test evidence. Market → Opportunities/Product Incubator/Portfolio. Treasury → Finance. Lighthouse → Watchtower. Library → Audit/decision history. Post → Founder Inbox. Shipyard → Build Inspector/release evidence. Commons → Projects. Inspectors show actual linked task, run, incident, budget or message data, with a button to open the full existing dashboard. The current library is an evidence/audit entry point, not a newly implemented semantic knowledge-search service.

## Original art and reliability

Original Blender sources and a reproducible generator are under `assets/kingdom/`; self-contained GLB packs are under `apps/web/public/kingdom/`. Twelve functional landmarks, cottages, foliage, gardens, coast, pier and boat occupy one continuous island. Three model-quality tiers, instanced citizens, static contact shadows, bounded orthographic controls, presets, follow/reset, optional labels, reduced motion and a keyboard-accessible landmark/citizen directory are implemented. A WebGL/asset error exposes the operational map rather than granting any new authority. Both production Dockerfiles copy the public assets alongside standalone Next output.

## Verification scope

Unit tests check stable scoped identities, authentic running-task/run pairs, approval/quarantine projection, incident severity, registry destinations and deterministic route connectivity. Asset validation checks GLB structure, twelve landmark identities, named villager parts, no external dependencies and ordered LOD triangle budgets.

The browser acceptance uses real authenticated services, actual existing records, landmark/citizen navigation, camera controls, fallback, a zero-cost internal task event, persisted reload and legacy Office/mobile checks. Its internal task is cancelled afterward. It never fabricates a running agent or incident. A new live hosted-coding animation cannot be certified while Daytona/public gateway remain disconnected; existing model advisory history is shown honestly. Software Chromium render observations and a recorded walkthrough are evidence of interaction, not hardware GPU, load-test or artistic production sign-off.
