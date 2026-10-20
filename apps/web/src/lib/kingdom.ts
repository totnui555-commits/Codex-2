import type { Row, Snapshot } from "./domain";
export type Point = [number, number, number];
export const WORLD_VERSION = "kingdom-2.0.0";
export const landmarks = [
  {
    id: "keep",
    name: "Royal Keep",
    subtitle: "Founder command",
    page: "Overview",
    position: [0, 1.5, -5] as Point,
    color: "#d6aa4e",
  },
  {
    id: "guild",
    name: "Adventurers’ Guild",
    subtitle: "Quests & planning",
    page: "Tasks",
    position: [-3, 0.55, -0.3] as Point,
    color: "#5c846c",
  },
  {
    id: "workshop",
    name: "Inventors’ Workshop",
    subtitle: "Code & sandbox runs",
    page: "Build Inspector",
    position: [6, 0.55, -1.5] as Point,
    color: "#bf7948",
  },
  {
    id: "atelier",
    name: "Artisans’ Atelier",
    subtitle: "Design & deliverables",
    page: "Agents",
    position: [6, 0.55, 2] as Point,
    color: "#9c739c",
  },
  {
    id: "alchemy",
    name: "Alchemists’ Laboratory",
    subtitle: "QA & security evidence",
    page: "Build Inspector",
    position: [9, 0.6, -3.3] as Point,
    color: "#647f9d",
  },
  {
    id: "market",
    name: "Harbor Market",
    subtitle: "Discovery & products",
    page: "Opportunities",
    position: [2.8, 0.55, 5] as Point,
    color: "#c18b4f",
  },
  {
    id: "treasury",
    name: "Royal Treasury",
    subtitle: "Costs & reservations",
    page: "Finance",
    position: [3.5, 0.7, -4.5] as Point,
    color: "#b99a4e",
  },
  {
    id: "lighthouse",
    name: "Watchtower Lighthouse",
    subtitle: "Independent oversight",
    page: "Watchtower",
    position: [-10, 1.6, -2.5] as Point,
    color: "#dda951",
  },
  {
    id: "library",
    name: "Great Library",
    subtitle: "Evidence & decisions",
    page: "Audit",
    position: [-3.5, 0.7, -5] as Point,
    color: "#6c8e91",
  },
  {
    id: "post",
    name: "Royal Post Office",
    subtitle: "Founder Inbox & mail",
    page: "Founder Inbox",
    position: [0, 0.55, 1] as Point,
    color: "#b86b55",
  },
  {
    id: "shipyard",
    name: "Harbor Shipyard",
    subtitle: "Builds & release evidence",
    page: "Build Inspector",
    position: [7, 0.3, 6] as Point,
    color: "#698e92",
  },
  {
    id: "commons",
    name: "Village Commons",
    subtitle: "Portfolio & live events",
    page: "Projects",
    position: [-3, 0.5, 3.5] as Point,
    color: "#7d9865",
  },
] as const;
export type Landmark = (typeof landmarks)[number];
export function landmark(id: string): Landmark {
  return landmarks.find((l) => l.id === id) || landmarks[1];
}
export function homeLandmark(key: string): string {
  if (/inspector|compliance|security/.test(key)) return "lighthouse";
  if (/financial|pricing/.test(key)) return "treasury";
  if (/qa/.test(key)) return "alchemy";
  if (/engineer|architect/.test(key)) return "workshop";
  if (/devops/.test(key)) return "shipyard";
  if (/designer|ux|brand/.test(key)) return "atelier";
  if (/documentation/.test(key)) return "library";
  if (/support|feedback/.test(key)) return "post";
  if (/scout|market|opportunity|incubator|growth|revenue/.test(key))
    return "market";
  if (/chief|portfolio/.test(key)) return "keep";
  return "guild";
}
export function stableSeed(value: string): number {
  let h = 2166136261;
  for (const c of value) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
  return h >>> 0;
}
export function groundHeight(x: number, z: number): number {
  let height = 0.58;
  for (const [cx, cz, sx, sz, h] of [
    [0, -5, 3.1, 2.5, 0.85],
    [-10, -2.5, 2.1, 2.1, 1.3],
  ]) {
    const q = ((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2;
    if (q < 1) height = Math.max(height, 0.5 + h * Math.sqrt(1 - q));
  }
  return height;
}
export function citizen(role: Row, snapshot: Snapshot) {
  const org = snapshot.organization.id;
  const seed = stableSeed(org + ":" + role.id);
  const runs = snapshot.runs
    .filter((r) => r.agent_role === role.key)
    .sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""));
  const running = runs.find((r) => r.status === "running");
  let run: Row | undefined = running || runs[0];
  let task = run ? snapshot.tasks.find((t) => t.id === run?.task_id) : undefined;
  const pending = snapshot.tasks
    .filter(
      (t) =>
        t.agent_role === role.key &&
        !["completed", "cancelled"].includes(t.status),
    )
    .sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""))[0];
  if (
    !running &&
    pending &&
    (!task || (pending.created_at || "") > (task.created_at || ""))
  ) {
    task = pending;
    run = runs.find((r) => r.task_id === pending.id);
  }
  const home = homeLandmark(role.key);
  let state = "idle";
  if (run && ["quarantined", "blocked", "failed"].includes(run.status))
    state = run.status;
  else if (task && ["quarantined", "blocked", "failed"].includes(task.status))
    state = task.status;
  else if (task?.status === "waiting_for_approval")
    state = "waiting_for_approval";
  else if (
    run?.status === "running" &&
    task?.status === "running" &&
    !snapshot.organization.stopped
  ) {
    state = /engineer/.test(role.key)
      ? "coding"
      : /qa/.test(role.key)
        ? "testing"
        : /designer|ux|brand/.test(role.key)
          ? "designing"
          : /scout|market|opportunity/.test(role.key)
            ? "opportunity_scanning"
            : /chief|portfolio|analyst/.test(role.key)
              ? "planning"
              : "reviewing";
  }
  if (
    run?.status === "running" &&
    (snapshot.organization.stopped ||
      snapshot.organization.paid_execution_authorized === false ||
      snapshot.projects?.some((p) => p.id === task?.project_id && p.paused))
  )
    state = "paused";
  if (
    state === "idle" &&
    task &&
    ["proposed", "ready", "scheduled"].includes(task.status)
  )
    state = "queued";
  const working = [
    "coding",
    "testing",
    "designing",
    "opportunity_scanning",
    "planning",
    "reviewing",
  ].includes(state);
  const target =
    state === "waiting_for_approval"
      ? "post"
      : state === "quarantined"
        ? "lighthouse"
        : working && state === "planning"
          ? "guild"
          : home;
  const center = landmark(target).position;
  const angle = (seed % 628) / 100;
  const position: Point = [
    center[0] + Math.cos(angle) * 1.45,
    0.58,
    center[2] + 1.65 + Math.sin(angle) * 0.45,
  ];
  position[1] = groundHeight(position[0], position[2]);
  return {
    id: `${org}:${role.id}`,
    role,
    seed,
    home,
    target,
    position,
    state,
    working,
    task,
    run,
    lastServerEventAt:
      snapshot.events.find(
        (e) => e.aggregate_id === task?.id || e.aggregate_id === run?.id,
      )?.occurred_at ||
      run?.created_at ||
      null,
    palette: ["#4e9385", "#be7756", "#8973a3", "#547b9f", "#b8984e"][seed % 5],
  };
}
export function lighthouseState(snapshot: Snapshot) {
  const open = snapshot.incidents.filter((i) => i.state === "open");
  return {
    count: open.length,
    severity: open.some((i) => i.severity === "critical")
      ? "critical"
      : open.length
        ? "advisory"
        : "calm",
    monitor: snapshot.services?.watchtower?.state || "unknown",
  };
}
// A baked street graph. Paths stay outside building footprints; coordinates are visual only.
export const street: Point[] = [
  [0, 0.58, 3],
  [0, 0.58, -1.4],
  [0, 0.58, -3.1],
  [-6, 0.58, -1.4],
  [-8, 0.58, -1.4],
  [5, 0.58, -0.1],
  [7.8, 0.58, -0.1],
  [4, 0.58, 4.4],
  [7, 0.58, 5.1],
  [-3, 0.58, 3.5],
];
export const edges = [
  [0, 1],
  [1, 2],
  [1, 3],
  [3, 4],
  [1, 5],
  [5, 6],
  [0, 7],
  [7, 8],
  [0, 9],
];
export function route(from: Point, to: Point): Point[] {
  const nearest = (p: Point) =>
    street.reduce(
      (best, n, i) =>
        Math.hypot(n[0] - p[0], n[2] - p[2]) <
        Math.hypot(street[best][0] - p[0], street[best][2] - p[2])
          ? i
          : best,
      0,
    );
  const start = nearest(from),
    end = nearest(to),
    queue = [start],
    previous = new Map<number, number>();
  previous.set(start, -1);
  while (queue.length) {
    const at = queue.shift()!;
    if (at === end) break;
    for (const [a, b] of edges) {
      const next = a === at ? b : b === at ? a : -1;
      if (next >= 0 && !previous.has(next)) {
        previous.set(next, at);
        queue.push(next);
      }
    }
  }
  const path: number[] = [];
  let at = end;
  while (at >= 0 && previous.has(at)) {
    path.unshift(at);
    at = previous.get(at)!;
  }
  return [from, ...path.map((i) => street[i]), to];
}
