export type Row = {
  id: string;
  organization_id?: string;
  created_at: string;
  [key: string]: any;
};
export interface Snapshot {
  deployment?: { runtime: string };
  services?: Record<string, { last_seen_at: string; state: string }>;
  organization: Row;
  projects: Row[];
  tasks: Row[];
  dependencies: Row[];
  roles: Row[];
  runs: Row[];
  artifacts: Row[];
  approvals: Row[];
  messages: Row[];
  deliveries: Row[];
  opportunities: Row[];
  experiments?: Row[];
  products?: Row[];
  revenue: Row[];
  usage: Row[];
  incidents: Row[];
  events: Row[];
  cursor: number;
  kpis: {
    active_agents: number;
    jobs_running: number;
    jobs_waiting: number;
    approvals_needed: number;
    monthly_spend: string;
    reserved: string;
    available_budget: string;
    currency: string;
  };
  integrations: Record<string, string>;
}
export async function api<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch("/api" + path, {
    credentials: "same-origin",
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    let message = "Request failed";
    try {
      const data = await response.json();
      message =
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail);
    } catch {}
    throw new Error(message);
  }
  return response.json();
}
export function agentState(role: string, snapshot: Snapshot): string {
  const run = snapshot.runs.find(
    (r) =>
      r.agent_role === role &&
      ["running", "quarantined", "blocked"].includes(r.status),
  );
  if (!run) return "idle";
  if (run.status !== "running") return run.status;
  return /engineer/.test(role)
    ? "coding"
    : /qa/.test(role)
      ? "testing"
      : /scout|intelligence/.test(role)
        ? "researching"
        : "reviewing";
}
export const floors = [
  {
    name: "Operations",
    short: "01",
    label: "Keep the company running",
    color: "#8fa9aa",
  },
  {
    name: "Quality & Watchtower",
    short: "02",
    label: "Independent by design",
    color: "#849e84",
  },
  {
    name: "Engineering Lab",
    short: "03",
    label: "From brief to build",
    color: "#7e9eb8",
  },
  {
    name: "Design Studio",
    short: "04",
    label: "Make useful things beautiful",
    color: "#b3a1bd",
  },
  {
    name: "Revenue Lab",
    short: "05",
    label: "Evidence before investment",
    color: "#cfaa65",
  },
  {
    name: "Executive Command",
    short: "RF",
    label: "The bigger picture",
    color: "#e7c447",
  },
];
export function money(value: number | string, currency = "THB") {
  return new Intl.NumberFormat("en", {
    style: "currency",
    currency,
    maximumFractionDigits:
      Math.abs(Number(value)) > 0 && Math.abs(Number(value)) < 1 ? 4 : 2,
  }).format(Number(value));
}
