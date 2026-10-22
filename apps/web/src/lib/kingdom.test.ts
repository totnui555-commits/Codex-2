import { describe, it, expect } from "vitest";
import {
  citizen,
  kingdomActivity,
  homeLandmark,
  landmarks,
  lighthouseState,
  route,
  street,
} from "./kingdom";
import type { Row, Snapshot } from "./domain";
const role = {
  id: "persistent-role-1",
  key: "backend_engineer",
  config: { role: "Engineer" },
} as unknown as Row;
function snapshot(changes: Partial<Snapshot> = {}): Snapshot {
  return {
    organization: { id: "org-a", stopped: false },
    roles: [role],
    runs: [],
    tasks: [],
    events: [],
    incidents: [],
    ...changes,
  } as unknown as Snapshot;
}
describe("kingdom authoritative world projection", () => {
  it("preserves citizen identity across role renames/reordering and isolates organizations", () => {
    const a = citizen(role, snapshot()),
      renamed = citizen(
        { ...role, config: { role: "Renamed engineer" } },
        snapshot(),
      );
    expect(a.id).toBe(renamed.id);
    expect(a.position).toEqual(renamed.position);
    expect(
      citizen({ ...role, id: "another-persisted-id" }, snapshot()).id,
    ).not.toBe(a.id);
    expect(
      citizen(
        role,
        snapshot({ organization: { id: "org-b" } as unknown as Row }),
      ).id,
    ).not.toBe(a.id);
  });
  it("never reports work without a matching running task and run", () => {
    expect(citizen(role, snapshot()).working).toBe(false);
    const run = {
      id: "run",
      agent_role: role.key,
      status: "running",
      task_id: "task",
    } as unknown as Row;
    expect(citizen(role, snapshot({ runs: [run] })).working).toBe(false);
    const active = snapshot({
      runs: [run],
      tasks: [{ id: "task", status: "running" } as unknown as Row],
    });
    expect(citizen(role, active)).toMatchObject({
      working: true,
      state: "coding",
      target: "workshop",
    });
    active.organization.stopped = true;
    expect(citizen(role, active).working).toBe(false);
  });
  it("carries an actual waiting approval to the post without inventing completion", () => {
    const c = citizen(
      role,
      snapshot({
        runs: [
          {
            id: "run",
            agent_role: role.key,
            task_id: "task",
            status: "completed",
          } as unknown as Row,
        ],
        tasks: [
          { id: "task", status: "waiting_for_approval" } as unknown as Row,
        ],
      }),
    );
    expect(c).toMatchObject({
      state: "waiting_for_approval",
      target: "post",
      working: false,
    });
  });
  it("projects quarantine independently from ambience and refuses synthetic critical alerts", () => {
    expect(
      citizen(
        role,
        snapshot({
          runs: [
            {
              id: "run",
              agent_role: role.key,
              status: "quarantined",
            } as unknown as Row,
          ],
        }),
      ),
    ).toMatchObject({
      state: "quarantined",
      target: "lighthouse",
      working: false,
    });
    expect(lighthouseState(snapshot())).toMatchObject({
      severity: "calm",
      monitor: "unknown",
    });
    expect(
      lighthouseState(
        snapshot({
          incidents: [
            {
              id: "resolved",
              state: "resolved",
              severity: "critical",
            } as unknown as Row,
          ],
        }),
      ).severity,
    ).toBe("calm");
    expect(
      lighthouseState(
        snapshot({
          incidents: [
            {
              id: "open",
              state: "open",
              severity: "critical",
            } as unknown as Row,
          ],
        }),
      ),
    ).toMatchObject({ severity: "critical", count: 1 });
  });
  it("maps twelve distinct landmarks to actual dashboards and every role to valid destinations", () => {
    expect(new Set(landmarks.map((l) => l.id)).size).toBe(12);
    for (const key of [
      "backend_engineer",
      "qa_engineer",
      "venture_scout",
      "inspector_general",
      "financial_controller",
      "ui_designer",
      "devops_release",
      "documentation",
      "support",
    ]) {
      expect(landmarks.some((l) => l.id === homeLandmark(key))).toBe(true);
    }
    expect(landmarks.find((l) => l.id === "lighthouse")?.page).toBe(
      "Watchtower",
    );
  });
  it("shows genuine preflight blockers even when no provider run was created", () => {
    const task = {
      id: "blocked-task",
      agent_role: role.key,
      status: "blocked",
      created_at: "2026-10-20T00:00:00Z",
    } as unknown as Row;
    expect(citizen(role, snapshot({ tasks: [task] }))).toMatchObject({
      state: "blocked",
      working: false,
    });
    expect(
      citizen(role, snapshot({ tasks: [{ ...task, status: "ready" }] })),
    ).toMatchObject({ state: "queued", working: false });
  });
  it("stops working presentation when the project or paid policy is revoked", () => {
    const active = snapshot({
      runs: [
        {
          id: "run",
          agent_role: role.key,
          status: "running",
          task_id: "task",
        } as unknown as Row,
      ],
      tasks: [
        { id: "task", project_id: "p", status: "running" } as unknown as Row,
      ],
      projects: [{ id: "p", paused: true } as unknown as Row],
    });
    expect(citizen(role, active)).toMatchObject({
      state: "paused",
      working: false,
    });
    active.projects = [];
    active.organization.paid_execution_authorized = false;
    expect(citizen(role, active).working).toBe(false);
  });
  it("routes reproducibly through a connected baked street graph", () => {
    for (const to of street) {
      const path = route(street[4], to);
      expect(path.at(-1)).toEqual(to);
      expect(path).toEqual(route(street[4], to));
      expect(path.every((p) => p.every(Number.isFinite))).toBe(true);
    }
  });
  it("coalesces duplicate email notices without hiding independent security incidents", () => {
    const result = kingdomActivity([
      { id: "a", event_type: "notification.disconnected" },
      { id: "b", event_type: "notification.disconnected" },
      { id: "c", event_type: "watchtower.incident" },
      { id: "d", event_type: "watchtower.incident" },
    ] as unknown as Row[]);
    expect(result).toHaveLength(3);
    expect(result[0]).toMatchObject({
      label: "Email connection needed",
      count: 2,
    });
    expect(result.filter((r) => r.label === "Watchtower alert")).toHaveLength(
      2,
    );
  });
});
