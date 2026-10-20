"use client";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { useCallback, useEffect, useRef, useState, FormEvent } from "react";
import {
  Box,
  LayoutDashboard,
  FolderKanban,
  ListTodo,
  Bot,
  TrendingUp,
  ShieldCheck,
  Inbox,
  CheckCheck,
  Wallet,
  Settings,
  Search,
  Bell,
  ArrowUpRight,
  ArrowRight,
  Plus,
  Radio,
  Maximize2,
  RotateCcw,
  Layers,
  ChevronRight,
  ChevronDown,
  Command,
  Pause,
  Play,
  Power,
  Activity,
  ExternalLink,
  Mail,
  Link2,
  Clock,
  Check,
  AlertTriangle,
  X,
  LogOut,
  PanelLeftClose,
  Sun,
  Globe,
  FileCode2,
  Terminal,
  Menu,
} from "lucide-react";
import {
  api,
  agentState,
  floors,
  money,
  type Row,
  type Snapshot,
} from "@/lib/domain";
import { Incubator } from "./incubator";
import { ProductPortfolio } from "./product-portfolio";
const Office = dynamic(() => import("./office"), {
  ssr: false,
  loading: () => (
    <div className="scene-loading">
      <Box size={32} />
      <span>Opening your office…</span>
    </div>
  ),
});
const nav = [
  { name: "Office", icon: Box },
  { name: "Overview", icon: LayoutDashboard },
  { name: "Projects", icon: FolderKanban },
  { name: "Tasks", icon: ListTodo },
  { name: "Agents", icon: Bot },
  { name: "Opportunities", icon: TrendingUp },
  { name: "Watchtower", icon: ShieldCheck },
  { name: "Approvals", icon: CheckCheck },
  { name: "Founder Inbox", icon: Inbox },
  { name: "Finance", icon: Wallet },
  { name: "Build Inspector", icon: Terminal },
  { name: "Audit", icon: Activity },
  { name: "Settings", icon: Settings },
];
const time = (s: string) =>
  new Date(s).toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit" });
function Badge({
  children,
  kind = "",
}: {
  children: React.ReactNode;
  kind?: string;
}) {
  return <span className={"badge " + kind}>{children}</span>;
}
function Empty({
  title,
  body,
  icon: Icon = Box,
}: {
  title: string;
  body: string;
  icon?: any;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Icon size={25} />
      </div>
      <h3>{title}</h3>
      <p>{body}</p>
    </div>
  );
}
function Status({ value }: { value: string }) {
  return (
    <span className={"status " + value}>
      <i />
      {value.replaceAll("_", " ")}
    </span>
  );
}
export default function MissionControl() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null),
    [auth, setAuth] = useState(false),
    [boot, setBoot] = useState(false),
    [page, setPage] = useState("Office"),
    [error, setError] = useState(""),
    [toast, setToast] = useState(""),
    [busy, setBusy] = useState(false),
    [connected, setConnected] = useState(false),
    [floor, setFloor] = useState<number | null>(null),
    [selected, setSelected] = useState<Row | null>(null),
    [reset, setReset] = useState(0),
    [flat, setFlat] = useState(false),
    [modal, setModal] = useState<"project" | "task" | null>(null),
    [search, setSearch] = useState(""),
    [sidebar, setSidebar] = useState(false),
    [audit, setAudit] = useState<Row[]>([]),
    [replay, setReplay] = useState<number | null>(null);
  const [inspection, setInspection] = useState<any>(null);
  const source = useRef<EventSource | null>(null);
  const loaded = useRef(false);
  const refresh = useCallback(async () => {
    const s = await api<Snapshot>("/snapshot");
    setSnapshot(s);
    setAuth(true);
    return s;
  }, []);
  useEffect(() => {
    const sync = () => {
      const path = window.location.pathname;
      const match = nav.find(
        (n) => "/" + n.name.toLowerCase().replaceAll(" ", "-") === path,
      );
      setPage(path === "/inbox" ? "Founder Inbox" : match?.name || "Office");
    };
    sync();
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);
  useEffect(() => {
    api("/auth/me")
      .then(() => refresh())
      .catch(() => setAuth(false))
      .finally(() => {
        loaded.current = true;
        setBoot(true);
      });
  }, [refresh]);
  useEffect(() => {
    if (!auth) return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    refresh()
      .then((s) => {
        if (disposed) return;
        const es = new EventSource("/api/events?after=" + s.cursor);
        source.current = es;
        es.onopen = () => setConnected(true);
        es.onerror = () => setConnected(false);
        es.addEventListener("company", () => {
          if (timer) clearTimeout(timer);
          timer = setTimeout(
            () => refresh().catch(() => setConnected(false)),
            150,
          );
        });
      })
      .catch(() => setConnected(false));
    const interval = setInterval(
      () => refresh().catch(() => setConnected(false)),
      30000,
    );
    return () => {
      disposed = true;
      source.current?.close();
      clearInterval(interval);
      if (timer) clearTimeout(timer);
    };
  }, [auth, refresh]);
  useEffect(() => {
    if (toast) {
      const id = setTimeout(() => setToast(""), 4500);
      return () => clearTimeout(id);
    }
  }, [toast]);
  useEffect(() => {
    if (page === "Audit" && auth)
      api<Row[]>("/audit")
        .then(setAudit)
        .catch((e) => setError(e.message));
  }, [page, auth, snapshot?.cursor]);
  async function action(path: string, body?: any, method = "POST") {
    setBusy(true);
    try {
      const result = await api(path, {
        method,
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      await refresh();
      setToast("Saved to the company record");
      setModal(null);
      return result;
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function authenticate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const f = new FormData(e.currentTarget);
    try {
      await api(bootMode ? "/auth/bootstrap" : "/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: f.get("email"),
          password: f.get("password"),
          ...(bootMode
            ? {
                organization_name: f.get("organization"),
                bootstrap_token: f.get("token"),
              }
            : {}),
        }),
      });
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const [bootMode, setBootMode] = useState(false);
  function go(name: string) {
    window.history.pushState(
      null,
      "",
      name === "Office"
        ? "/"
        : name === "Founder Inbox"
          ? "/inbox"
          : "/" + name.toLowerCase().replaceAll(" ", "-"),
    );
    setPage(name);
    setSelected(null);
    setSearch("");
    setReplay(null);
    setSidebar(false);
  }
  function selectFloor(n: number) {
    setFloor(n);
    setSelected(null);
  }
  if (!boot)
    return (
      <div className="boot">
        <Box size={40} />
        <span>AI COMPANY OS</span>
        <p>Connecting to mission control</p>
      </div>
    );
  if (!auth || !snapshot)
    return (
      <main className="login">
        <div className="login-art">
          <div className="wordmark">
            <Box /> AI COMPANY OS
          </div>
          <div>
            <span className="eyebrow">YOUR VENTURE STUDIO, REIMAGINED</span>
            <h1>
              Big ideas.
              <br />
              Real execution.
            </h1>
            <p>
              A company you can see.
              <br />A workforce you can trust.
            </p>
          </div>
          <span className="login-footer">FOUNDER-LED. AGENT-POWERED.</span>
          <div className="login-cube">
            <Box size={180} strokeWidth={0.7} />
          </div>
        </div>
        <div className="login-form">
          <span className="eyebrow">MISSION CONTROL</span>
          <h2>{bootMode ? "Build your company." : "Welcome back, founder."}</h2>
          <p>
            {bootMode
              ? "Initialize a private installation with your secure setup token."
              : "Sign in to see what your company is building."}
          </p>
          <form onSubmit={authenticate}>
            <label>
              Email
              <input
                name="email"
                type="email"
                required
                autoComplete="username"
                defaultValue="traisorn.th@gmail.com"
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                minLength={12}
                required
                autoComplete={bootMode ? "new-password" : "current-password"}
              />
            </label>
            {bootMode && (
              <>
                <label>
                  Company name
                  <input
                    name="organization"
                    required
                    defaultValue="AI Company OS"
                  />
                </label>
                <label>
                  Installation setup token
                  <input
                    name="token"
                    type="password"
                    required
                    autoComplete="off"
                  />
                </label>
              </>
            )}
            {error && (
              <p role="alert" className="form-error">
                {error}
              </p>
            )}
            <button className="primary" disabled={busy}>
              {busy
                ? "Connecting…"
                : bootMode
                  ? "Initialize company"
                  : "Enter mission control"}
              <ArrowRight size={16} />
            </button>
          </form>
          <button
            className="text-button"
            onClick={() => {
              setBootMode(!bootMode);
              setError("");
            }}
          >
            {bootMode
              ? "Already set up? Sign in"
              : "First time here? Initialize installation"}
          </button>
          <div className="login-note">
            <ShieldCheck size={17} />
            Private by default. Every action is accountable.
          </div>
        </div>
      </main>
    );
  const s = snapshot;
  const events = s.events.slice().sort((a, b) => b.cursor - a.cursor);
  const filtered = (rows: Row[]) =>
    rows.filter((r) =>
      JSON.stringify(r).toLowerCase().includes(search.toLowerCase()),
    );
  const chosenFloor = floor !== null ? floors[floor] : null;
  const displayedRoles = chosenFloor
    ? s.roles.filter((r) => r.config.floor === chosenFloor.name)
    : s.roles;
  const activeRuns = s.runs.filter((r) => r.status === "running");
  const submitted = (
    e: FormEvent<HTMLFormElement>,
    handler: (f: FormData) => void,
  ) => {
    e.preventDefault();
    handler(new FormData(e.currentTarget));
  };
  return (
    <div className={"app " + (sidebar ? "sidebar-open" : "")}>
      <aside className="sidebar">
        <a className="wordmark" href="#" onClick={() => go("Office")}>
          <div className="brand-icon">
            <Box size={24} />
          </div>
          <span>
            AI COMPANY OS<small>THE AUTONOMOUS VENTURE STUDIO</small>
          </span>
        </a>
        <div className="workspace">
          <span className="workspace-logo">A</span>
          <span>
            {s.organization.name}
            <small>Founder workspace</small>
          </span>
          <ChevronDown size={14} />
        </div>
        <span className="nav-section">WORKSPACE</span>
        <nav>
          {nav.slice(0, 6).map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={page === name ? "active" : ""}
              onClick={() => go(name)}
            >
              <Icon size={17} />
              {name}
              {name === "Office" && <span className="tiny">3D</span>}
            </button>
          ))}
        </nav>
        <span className="nav-section">CONTROL ROOM</span>
        <nav>
          {nav.slice(6, -1).map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={page === name ? "active" : ""}
              onClick={() => go(name)}
            >
              <Icon size={17} />
              {name}
              {name === "Founder Inbox" &&
                s.messages.filter((m) => m.state === "open").length > 0 && (
                  <span className="count">
                    {s.messages.filter((m) => m.state === "open").length}
                  </span>
                )}
              {name === "Approvals" && s.kpis.approvals_needed > 0 && (
                <span className="count">{s.kpis.approvals_needed}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="autonomy">
            <div>
              <span className="live-dot" />
              <b>
                {s.organization.stopped
                  ? "Company paused"
                  : "Management online"}
              </b>
            </div>
            <p>
              {s.organization.mode.replaceAll("_", " ")}
              <ShieldCheck size={13} />
            </p>
            <div className="mini-track">
              <i
                style={{
                  width:
                    100 -
                    Math.min(
                      100,
                      (Number(s.kpis.monthly_spend) /
                        Number(s.organization.monthly_limit)) *
                        100,
                    ) +
                    "%",
                }}
              />
            </div>
            <span>Within founder-defined boundaries</span>
          </div>
          <button onClick={() => go("Settings")} className="settings-link">
            <Settings size={16} />
            Settings
          </button>
          <div className="founder">
            <div className="avatar">T</div>
            <span>
              Traisorn<small>Founder & CEO</small>
            </span>
            <button
              title="Sign out"
              onClick={async () => {
                await api("/auth/logout", { method: "POST" });
                setAuth(false);
              }}
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-menu icon-button"
              aria-label="Open navigation"
              onClick={() => setSidebar(!sidebar)}
            >
              <Menu size={18} />
            </button>
            <Box size={15} />
            <span>Workspace</span>
            <ChevronRight size={13} />
            <b>{page === "Office" ? "Mission Control" : page}</b>
          </div>
          <div className="top-actions">
            <div className={"connection " + (connected ? "connected" : "")}>
              <i />
              {connected ? "Live connection" : "Reconnecting"}
            </div>
            <span className="top-divider" />
            <button
              className="icon-button"
              aria-label="Open founder notifications"
              onClick={() => go("Founder Inbox")}
            >
              <Bell size={18} />
              {s.messages.some((m) => m.state === "open") && (
                <span className="notification-dot" />
              )}
            </button>
            <div className="avatar small">T</div>
          </div>
        </header>
        <div className="page-heading">
          <div>
            <div className="eyebrow">YOUR COMPANY, IN MOTION</div>
            <h1>
              {page === "Office" ? "Mission Control" : page}
              <span className="heading-dot">.</span>
            </h1>
            <p>
              {page === "Office"
                ? "A little world. A lot of possibility."
                : page === "Opportunities"
                  ? "Find a real problem. Build something worth paying for."
                  : page === "Watchtower"
                    ? "Independent oversight. Evidence behind every claim."
                    : "The work, the decisions, and everything that moves us forward."}
            </p>
          </div>
          <div className="heading-actions">
            <span className="date-label">
              {new Date().toLocaleDateString("en", {
                day: "numeric",
                month: "short",
                year: "numeric",
                timeZone: "Asia/Bangkok",
              })}
            </span>
            <Button onClick={() => setModal("project")}>
              <Plus size={16} />
              New project
            </Button>
          </div>
        </div>
        {s.deployment?.runtime === "staging" && (
          <div className="info-strip" role="status">
            <AlertTriangle size={17} />
            Staging workspace. Free hosting may sleep; the database expires
            after 30 days. Background workers are not deployed here. Keep
            production and customer data out of this environment.
          </div>
        )}
        {s.organization.stopped && (
          <div className="stop-banner">
            <Power size={17} />
            STOP ALL is active. Execution is paused.
            <button onClick={() => action("/company/resume")}>
              Resume company
            </button>
          </div>
        )}
        <section className="kpis">
          <div className="kpi">
            <span>
              <Bot size={16} />
              Workforce
            </span>
            <div>
              <b>{s.kpis.active_agents}</b>
              <small>/ {s.roles.length} agents</small>
              <Badge kind="green">
                {activeRuns.length ? "Working" : "Ready"}
              </Badge>
            </div>
            <p>Allocated only when work exists</p>
          </div>
          <div className="kpi">
            <span>
              <FolderKanban size={16} />
              Active projects
            </span>
            <div>
              <b>
                {s.projects
                  .filter((p) => !p.paused)
                  .length.toString()
                  .padStart(2, "0")}
              </b>
              <small>in the portfolio</small>
            </div>
            <p>
              {s.tasks.filter((t) => t.status === "completed").length} tasks
              verified & complete
            </p>
          </div>
          <div className="kpi">
            <span>
              <Wallet size={16} />
              Monthly spend
            </span>
            <div>
              <b>{money(s.kpis.monthly_spend)}</b>
              <small>/ {money(s.organization.monthly_limit)}</small>
            </div>
            <p>
              {money(s.kpis.reserved)} reserved ·{" "}
              {money(s.kpis.available_budget)} available
            </p>
          </div>
          <div className="kpi">
            <span>
              <ShieldCheck size={16} />
              Company health
            </span>
            <div>
              <b>
                {s.incidents.filter((i) => i.state === "open").length
                  ? "Review"
                  : s.services?.watchtower?.state === "live"
                    ? "Clear"
                    : "Unknown"}
              </b>
              <Badge
                kind={
                  s.services?.watchtower?.state === "live" ? "green" : "amber"
                }
              >
                {s.services?.watchtower?.state === "live"
                  ? "Watchtower live"
                  : "Monitor not reporting"}
              </Badge>
            </div>
            <p>
              {s.incidents.filter((i) => i.state === "open").length} open
              incidents · {s.kpis.approvals_needed} approvals
            </p>
          </div>
        </section>
        {page === "Office" ? (
          <div className="office-layout">
            <section className="office-panel">
              <div className="office-toolbar">
                <div className="view-tabs">
                  <button
                    className={!flat ? "selected" : ""}
                    onClick={() => setFlat(false)}
                  >
                    <Box size={14} />
                    Office view
                  </button>
                  <button
                    className={flat ? "selected" : ""}
                    onClick={() => setFlat(true)}
                  >
                    <LayoutDashboard size={14} />
                    2D view
                  </button>
                </div>
                <div className="scene-actions">
                  <select
                    aria-label="Select office floor"
                    value={floor ?? ""}
                    onChange={(e) =>
                      setFloor(
                        e.target.value === "" ? null : Number(e.target.value),
                      )
                    }
                  >
                    <option value="">All floors</option>
                    {floors
                      .slice()
                      .reverse()
                      .map((f) => (
                        <option key={f.short} value={floors.indexOf(f)}>
                          {f.name}
                        </option>
                      ))}
                  </select>
                  <button
                    className="icon-button"
                    aria-label="Reset camera"
                    onClick={() => setReset(reset + 1)}
                  >
                    <RotateCcw size={15} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label="Expand office"
                    onClick={() =>
                      document
                        .querySelector(".office-panel")
                        ?.requestFullscreen()
                    }
                  >
                    <Maximize2 size={15} />
                  </button>
                </div>
              </div>
              <div className="scene">
                <div className="scene-corner">
                  <span className="eyebrow">THE HEADQUARTERS</span>
                  <h2>{chosenFloor?.name || "Good things are building."}</h2>
                  <p>
                    {chosenFloor?.label || "Six floors. One shared ambition."}
                  </p>
                </div>
                {flat ? (
                  <div className="floor-grid">
                    {floors
                      .slice()
                      .reverse()
                      .map((f) => (
                        <button
                          key={f.name}
                          onClick={() => selectFloor(floors.indexOf(f))}
                        >
                          <b>{f.short}</b>
                          <span>
                            {f.name}
                            <small>
                              {
                                s.roles.filter((r) => r.config.floor === f.name)
                                  .length
                              }{" "}
                              configured roles
                            </small>
                          </span>
                          <ArrowUpRight size={16} />
                        </button>
                      ))}
                  </div>
                ) : (
                  <Office
                    snapshot={s}
                    selectedFloor={floor}
                    onFloor={selectFloor}
                    onAgent={(r) => {
                      setSelected(r);
                      setReplay(null);
                    }}
                    resetKey={reset}
                    focusedAgent={selected || undefined}
                  />
                )}
                <div className="scene-bottom">
                  <span>
                    <i className="live-dot" />
                    Authoritative server state
                  </span>
                  <span>
                    Drag to orbit <b>·</b> Scroll to zoom <b>·</b> Click to
                    explore
                  </span>
                </div>
                <div className="compass">
                  N<span>↗</span>
                </div>
              </div>
              <div className="office-footer">
                <div>
                  <Layers size={16} />
                  <b>{chosenFloor?.name || "All departments"}</b>
                  <span>{displayedRoles.length} agents</span>
                </div>
                <div className="legend">
                  <span>
                    <i style={{ background: "#75a783" }} />
                    Working
                  </span>
                  <span>
                    <i style={{ background: "#aeb4ad" }} />
                    Idle
                  </span>
                  <span>
                    <i style={{ background: "#e6b84e" }} />
                    Needs attention
                  </span>
                </div>
              </div>
            </section>
            <aside className="right-panel">
              {selected ? (
                <>
                  <div className="section-title">
                    <h3>Agent inspector</h3>
                    <button
                      className="icon-button"
                      onClick={() => setSelected(null)}
                    >
                      <X size={15} />
                    </button>
                  </div>
                  <div className="agent-inspector">
                    <div className="agent-icon">
                      <Bot size={32} />
                    </div>
                    <Badge>{selected.config.floor}</Badge>
                    <h2>{selected.config.role}</h2>
                    <Status value={agentState(selected.key, s)} />
                    <p>{selected.config.mission}</p>
                    <dl>
                      <dt>Max runtime</dt>
                      <dd>{selected.config.max_runtime}s</dd>
                      <dt>Run ceiling</dt>
                      <dd>{money(selected.config.max_cost.amount)}</dd>
                      <dt>Allowed tools</dt>
                      <dd>{selected.config.allowed_tools.join(", ")}</dd>
                      <dt>Version</dt>
                      <dd>{selected.config.version}</dd>
                    </dl>
                    <h4>Current work</h4>
                    {s.runs
                      .filter((r) => r.agent_role === selected.key)
                      .map((r) => (
                        <article className="list-card" key={r.id}>
                          <Status value={r.status} />
                          <p>
                            {s.tasks.find((t) => t.id === r.task_id)?.title}
                          </p>
                          <small>Provider: {r.provider}</small>
                        </article>
                      ))}
                    {!s.runs.some((r) => r.agent_role === selected.key) && (
                      <p className="muted">
                        No runs yet. This agent is idle. No model tokens are
                        being used.
                      </p>
                    )}
                    <button
                      className="secondary"
                      onClick={() => {
                        go("Tasks");
                        setModal("task");
                      }}
                    >
                      Assign a task
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="section-title">
                    <h3>Company pulse</h3>
                    <Badge kind="green">
                      <span className="live-dot" />
                      LIVE
                    </Badge>
                  </div>
                  <div className="pulse-summary">
                    <span className="pulse-icon">
                      <Activity size={22} />
                    </span>
                    <div>
                      <b>
                        {s.kpis.jobs_running
                          ? "Work is underway"
                          : "Ready for what’s next"}
                      </b>
                      <p>
                        {s.kpis.jobs_running} running · {s.kpis.jobs_waiting}{" "}
                        queued tasks
                      </p>
                    </div>
                  </div>
                  <div className="section-title activity-heading">
                    <h3>Recent activity</h3>
                    <button onClick={() => go("Audit")}>
                      View all
                      <ArrowUpRight size={13} />
                    </button>
                  </div>
                  <div className="activity-list">
                    {events.slice(0, 5).map((e, i) => (
                      <div className="activity-item" key={e.id}>
                        <div className={"activity-symbol color-" + i}>
                          {e.event_type.startsWith("task") ? (
                            <FileCode2 size={15} />
                          ) : e.event_type.startsWith("inbox") ? (
                            <Mail size={15} />
                          ) : e.event_type.startsWith("opportunity") ? (
                            <TrendingUp size={15} />
                          ) : (
                            <Box size={15} />
                          )}
                        </div>
                        <div>
                          <b>
                            {e.event_type
                              .replaceAll(".", " · ")
                              .replaceAll("_", " ")}
                          </b>
                          <p>
                            {e.payload.title ||
                              e.payload.subject ||
                              e.payload.name ||
                              e.payload.status ||
                              "Recorded and audited"}
                          </p>
                          <span>{time(e.created_at)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="founder-note">
                    <div>
                      <span>YOUR NEXT MOVE</span>
                      <ArrowUpRight size={17} />
                    </div>
                    <h3>
                      {s.messages.some((m) => m.state === "open")
                        ? "The team needs your input."
                        : "Make room for your next idea."}
                    </h3>
                    <p>
                      {s.messages.some((m) => m.state === "open")
                        ? "Review the setup request to connect your workforce."
                        : "Create a project and give the team a clear goal."}
                    </p>
                    <button onClick={() => go("Founder Inbox")}>
                      Open Founder Inbox
                      <ArrowRight size={15} />
                    </button>
                  </div>
                  <div className="integration-mini">
                    <div className="section-title">
                      <h3>Connections</h3>
                      <button onClick={() => go("Settings")}>
                        <Link2 size={14} />
                      </button>
                    </div>
                    {Object.entries(s.integrations)
                      .slice(0, 4)
                      .map(([k, v]) => (
                        <div key={k}>
                          <span>
                            {k === "model"
                              ? "Research model"
                              : k === "sandbox"
                                ? "Coding sandboxes"
                                : k === "github"
                                  ? "GitHub"
                                  : "Artifact storage"}
                          </span>
                          <Status value={v} />
                        </div>
                      ))}
                  </div>
                </>
              )}
            </aside>
          </div>
        ) : (
          <section className="content-panel">
            <div className="content-toolbar">
              <h2>
                {page === "Overview"
                  ? "At a glance"
                  : page === "Tasks"
                    ? "Work queue"
                    : page === "Finance"
                      ? "Real costs. Verified receipts."
                      : page}
              </h2>
              <div>
                <label className="search">
                  <Search size={15} />
                  <input
                    placeholder="Search records…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                  <kbd>⌘ K</kbd>
                </label>
                {page === "Tasks" && (
                  <Button onClick={() => setModal("task")}>
                    <Plus size={15} />
                    Create task
                  </Button>
                )}
              </div>
            </div>
            {page === "Projects" && (
              <div className="cards">
                {filtered(s.projects).map((p) => (
                  <article className="project-card" key={p.id}>
                    <div className="project-icon">
                      <FolderKanban size={23} />
                    </div>
                    <Badge>{p.paused ? "Paused" : "Active"}</Badge>
                    <h3>{p.name}</h3>
                    <p>{p.description || "A new space for useful work."}</p>
                    <div className="project-progress">
                      <i
                        style={{
                          width:
                            (s.tasks.filter(
                              (t) =>
                                t.project_id === p.id &&
                                t.status === "completed",
                            ).length /
                              Math.max(
                                1,
                                s.tasks.filter((t) => t.project_id === p.id)
                                  .length,
                              )) *
                              100 +
                            "%",
                        }}
                      />
                    </div>
                    <footer>
                      <span>
                        {s.tasks.filter((t) => t.project_id === p.id).length}{" "}
                        tasks · {money(p.budget_limit)} ceiling
                      </span>
                      <button
                        className="icon-button"
                        aria-label={
                          p.paused ? "Resume project" : "Pause project"
                        }
                        onClick={() =>
                          action(
                            "/projects/" + p.id,
                            { paused: !p.paused },
                            "PATCH",
                          )
                        }
                      >
                        {p.paused ? <Play size={15} /> : <Pause size={15} />}
                      </button>
                    </footer>
                  </article>
                ))}
                {!s.projects.length && (
                  <Empty
                    title="Every good company starts with a project."
                    body="Create a project with a clear goal, then build a verifiable task backlog."
                    icon={FolderKanban}
                  />
                )}
              </div>
            )}
            {page === "Tasks" && (
              <div className="kanban">
                {["ready", "running", "reviewing", "blocked", "completed"].map(
                  (state) => (
                    <div className="kanban-column" key={state}>
                      <h3>
                        <span className={"column-dot " + state} />
                        {state.replaceAll("_", " ")}
                        <small>
                          {s.tasks.filter((t) => t.status === state).length}
                        </small>
                      </h3>
                      {filtered(s.tasks)
                        .filter((t) =>
                          state === "blocked"
                            ? [
                                "blocked",
                                "waiting_for_approval",
                                "quarantined",
                                "failed",
                              ].includes(t.status)
                            : t.status === state,
                        )
                        .map((t) => (
                          <article className="task-card" key={t.id}>
                            <Badge>
                              {
                                s.projects.find((p) => p.id === t.project_id)
                                  ?.name
                              }
                            </Badge>
                            <h4>{t.title}</h4>
                            <p>{t.objective}</p>
                            <ul>
                              {t.acceptance.map((a: string) => (
                                <li key={a}>{a}</li>
                              ))}
                            </ul>
                            <Status value={t.status} />
                            <footer>
                              <span>
                                <Bot size={13} />
                                {t.agent_role.replaceAll("_", " ")}
                              </span>
                              {["ready", "running", "blocked"].includes(
                                t.status,
                              ) && (
                                <button
                                  onClick={() =>
                                    action("/tasks/" + t.id + "/cancel")
                                  }
                                  title="Cancel task"
                                >
                                  <X size={14} />
                                </button>
                              )}
                              {["failed", "blocked"].includes(t.status) && (
                                <button
                                  onClick={() =>
                                    action("/tasks/" + t.id + "/retry")
                                  }
                                  title="Retry task"
                                >
                                  <RotateCcw size={14} />
                                </button>
                              )}
                            </footer>
                            {t.error && <p className="form-error">{t.error}</p>}
                          </article>
                        ))}
                    </div>
                  ),
                )}
              </div>
            )}
            {page === "Agents" && (
              <div className="cards agent-cards">
                {filtered(s.roles).map((r) => (
                  <button
                    className="agent-card"
                    key={r.id}
                    onClick={() => {
                      setSelected(r);
                      setPage("Office");
                    }}
                  >
                    <div className="agent-icon">
                      <Bot size={25} />
                    </div>
                    <h3>{r.config.role}</h3>
                    <span>{r.config.floor}</span>
                    <Status value={agentState(r.key, s)} />
                    <small>
                      v{r.config.version} · max {r.config.max_turns} turns
                    </small>
                  </button>
                ))}
              </div>
            )}
            {page === "Opportunities" && (
              <>
                <div className="info-strip">
                  <Globe size={17} />
                  Source-backed research only. Scores are preliminary
                  heuristics; willingness to pay is unverified.
                </div>
                <div className="cards">
                  {filtered(s.opportunities).map((o) => (
                    <article className="opportunity-card" key={o.id}>
                      <div>
                        <Badge>Research candidate</Badge>
                        <b className="score">
                          {o.score}
                          <small>/100</small>
                        </b>
                      </div>
                      <h3>{o.title}</h3>
                      <p>{o.hypothesis}</p>
                      <ul>
                        {o.uncertainties.map((u: string) => (
                          <li key={u}>{u}</li>
                        ))}
                      </ul>
                      {o.evidence.map((e: any) => (
                        <a
                          key={e.url}
                          href={e.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <ExternalLink size={13} />
                          {e.source || "Evidence"} ·{" "}
                          {new Date(e.retrieved_at).toLocaleDateString()}
                        </a>
                      ))}
                      <button
                        className="secondary"
                        disabled={!!o.project_id || busy}
                        onClick={() =>
                          action("/opportunities/" + o.id + "/incubate")
                        }
                      >
                        {o.project_id
                          ? "Backlog created"
                          : "Create incubation backlog"}
                        <ArrowRight size={14} />
                      </button>
                    </article>
                  ))}
                  {!s.opportunities.length && (
                    <Empty
                      title="Good opportunities need evidence."
                      body="The daily research worker collects permitted public sources. No opportunities or demand estimates have been invented."
                      icon={TrendingUp}
                    />
                  )}
                </div>
              </>
            )}
            {page === "Opportunities" && (
              <Incubator snapshot={s} refresh={refresh} />
            )}
            {page === "Opportunities" && (
              <ProductPortfolio snapshot={s} refresh={refresh} />
            )}
            {page === "Watchtower" && (
              <>
                <div className="info-strip">
                  <ShieldCheck size={17} />
                  Independent monitoring can quarantine work and raise
                  incidents. It cannot approve spending or releases.
                </div>
                {s.incidents.length ? (
                  <div className="cards">
                    {filtered(s.incidents).map((i) => (
                      <article className="list-card" key={i.id}>
                        <Badge kind="amber">{i.severity}</Badge>
                        <h3>{i.kind.replaceAll("_", " ")}</h3>
                        <p>{i.details.reason || JSON.stringify(i.details)}</p>
                        <Status value={i.state} />
                      </article>
                    ))}
                  </div>
                ) : (
                  <Empty
                    title="A clear view from the Watchtower."
                    body="No incidents recorded. The separate monitor checks worker leases, verified completion, audit integrity and exposed secrets."
                    icon={ShieldCheck}
                  />
                )}
                <button
                  className="secondary"
                  onClick={async () => {
                    const r = await api("/audit/verify");
                    setToast(
                      r.valid
                        ? "Audit hash chain verified"
                        : "Audit integrity check FAILED",
                    );
                  }}
                >
                  Verify audit integrity
                  <CheckCheck size={16} />
                </button>
              </>
            )}
            {page === "Founder Inbox" && (
              <div className="inbox-list">
                {filtered(s.messages).map((m) => (
                  <article key={m.id} className="inbox-card">
                    <div className="inbox-card-heading">
                      <div className="mail-icon">
                        <Mail size={21} />
                      </div>
                      <div>
                        <h3>{m.subject}</h3>
                        <span>{new Date(m.created_at).toLocaleString()}</span>
                      </div>
                      <Badge kind={m.state === "open" ? "amber" : "green"}>
                        {m.state === "open" ? "Action required" : "Answered"}
                      </Badge>
                    </div>
                    <p>{m.body}</p>
                    {m.options.length > 0 && (
                      <div className="options">
                        {m.options.map((o: string, i: number) => (
                          <span key={o}>
                            <b>{String.fromCharCode(65 + i)}</b>
                            {o}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="delivery-status">
                      <Mail size={13} />
                      Email:{" "}
                      {s.deliveries.find((d) => d.message_id === m.id)?.state ||
                        "pending"}
                      <span>
                        Replies here do not grant sensitive approvals.
                      </span>
                    </div>
                    {m.state === "open" ? (
                      <form
                        onSubmit={(e) =>
                          submitted(e, (f) =>
                            action("/inbox/" + m.id + "/respond", {
                              response: f.get("response"),
                            }),
                          )
                        }
                      >
                        <input
                          name="response"
                          required
                          placeholder="Your decision or direction…"
                        />
                        <button className="primary" disabled={busy}>
                          Send response
                          <ArrowRight size={15} />
                        </button>
                      </form>
                    ) : (
                      <div className="response">
                        <Check size={14} />
                        {m.response}
                      </div>
                    )}
                  </article>
                ))}
                {!s.messages.length && (
                  <Empty
                    title="Your inbox is clear."
                    body="The company will ask here when it needs a critical decision, credential or approval."
                    icon={Inbox}
                  />
                )}
              </div>
            )}
            {page === "Approvals" && (
              <div className="cards">
                {filtered(s.approvals).map((a) => (
                  <article className="approval-card" key={a.id}>
                    <Badge kind="amber">{a.state}</Badge>
                    <h3>{a.action.replaceAll("_", " ")}</h3>
                    <p>Target: {a.target}</p>
                    <label>
                      Immutable artifact SHA-256<code>{a.artifact_sha256}</code>
                    </label>
                    <p>
                      Maximum exposure: {money(a.max_exposure)}
                      <br />
                      Expires: {new Date(a.expires_at).toLocaleString()}
                    </p>
                    <pre>{JSON.stringify(a.context, null, 2)}</pre>
                    {a.state === "pending" && (
                      <div className="button-row">
                        {["approved", "changes_requested", "rejected"].map(
                          (d) => (
                            <button
                              key={d}
                              disabled={busy}
                              className={
                                d === "approved" ? "primary" : "secondary"
                              }
                              onClick={() =>
                                action("/approvals/" + a.id + "/decide", {
                                  decision: d,
                                  artifact_sha256: a.artifact_sha256,
                                })
                              }
                            >
                              {d === "approved"
                                ? "Approve"
                                : d === "rejected"
                                  ? "Reject"
                                  : "Request changes"}
                            </button>
                          ),
                        )}
                      </div>
                    )}
                  </article>
                ))}
                {!s.approvals.length && (
                  <Empty
                    title="No decisions waiting."
                    body="Protected actions need your approval for a specific artifact, destination, financial limit and expiry."
                    icon={CheckCheck}
                  />
                )}
              </div>
            )}
            {page === "Finance" && (
              <>
                <div className="finance-summary">
                  <article>
                    <span>Confirmed gross receipts</span>
                    <h2>
                      {
                        s.revenue.filter(
                          (r) => r.kind === "confirmed_gross_revenue",
                        ).length
                      }{" "}
                      transactions
                    </h2>
                    <p>Signed live payment webhooks only</p>
                  </article>
                  <article>
                    <span>Model & infrastructure usage</span>
                    <h2>{money(s.kpis.monthly_spend)}</h2>
                    <p>
                      Estimates are labeled; provider telemetry is retained.
                    </p>
                  </article>
                  <article>
                    <span>Net cash & contribution</span>
                    <h2>Not measured</h2>
                    <p>Requires settlement, fee, tax and cost evidence.</p>
                  </article>
                </div>
                <h3>Verified revenue ledger</h3>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Provider</th>
                        <th>Type</th>
                        <th>Amount (minor units)</th>
                        <th>Currency</th>
                        <th>Evidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {s.revenue.map((r) => (
                        <tr key={r.id}>
                          <td>{r.provider}</td>
                          <td>{r.kind}</td>
                          <td>{r.amount_minor}</td>
                          <td>{r.currency}</td>
                          <td>{r.external_id}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!s.revenue.length && (
                    <Empty
                      title="No verified revenue yet."
                      body="Forecasts, interest and research scores are never recorded as income."
                      icon={Wallet}
                    />
                  )}
                </div>
              </>
            )}
            {page === "Audit" && (
              <>
                <div className="audit-heading">
                  <p>
                    Transactionally recorded events with redacted payloads and a
                    hash chain.
                  </p>
                  <button
                    className="secondary"
                    onClick={async () => {
                      const r = await api("/audit/verify");
                      setToast(
                        r.valid
                          ? "All audit records verified"
                          : "Audit integrity FAILED",
                      );
                    }}
                  >
                    Verify chain
                    <ShieldCheck size={15} />
                  </button>
                </div>
                <div className="audit-list">
                  {filtered(audit).map((a) => (
                    <details key={a.id}>
                      <summary>
                        <span className="audit-sequence">#{a.sequence}</span>
                        <b>{a.action}</b>
                        <span>{new Date(a.created_at).toLocaleString()}</span>
                        <ChevronDown size={14} />
                      </summary>
                      <pre>{JSON.stringify(a, null, 2)}</pre>
                    </details>
                  ))}
                </div>
              </>
            )}
            {page === "Build Inspector" && (
              <>
                <div className="info-strip">
                  <Terminal size={17} />
                  Provider sessions, immutable artifacts and independent
                  verification. No terminal output is invented.
                </div>
                <h3>Execution runs</h3>
                <div className="cards">
                  {s.runs.map((run) => (
                    <article className="list-card" key={run.id}>
                      <Status value={run.status} />
                      <h3>
                        {s.tasks.find((t) => t.id === run.task_id)?.title}
                      </h3>
                      <p>
                        {run.agent_role.replaceAll("_", " ")} · {run.provider}
                      </p>
                      <code>
                        {run.provider_run_id || "No remote session created"}
                      </code>
                      <p>Started {new Date(run.created_at).toLocaleString()}</p>
                      <pre>{JSON.stringify(run.usage, null, 2)}</pre>
                    </article>
                  ))}
                </div>
                {!s.runs.length && (
                  <Empty
                    title="No coding sessions have run."
                    body="A real hosted provider session appears here after credentials, isolation controls and a budget pass preflight."
                    icon={Terminal}
                  />
                )}
                <h3>Verified artifacts</h3>
                <div className="cards">
                  {s.artifacts.map((artifact) => (
                    <article className="list-card" key={artifact.id}>
                      <Badge>{artifact.kind}</Badge>
                      <p>{artifact.uri}</p>
                      <code>{artifact.sha256}</code>
                      <p>{artifact.details.verification}</p>
                      <button
                        className="secondary"
                        onClick={async () => {
                          try {
                            setInspection(
                              await api(
                                "/artifacts/" + artifact.id + "/content",
                              ),
                            );
                          } catch (e) {
                            setError((e as Error).message);
                          }
                        }}
                      >
                        Inspect checksummed content
                        <ArrowUpRight size={14} />
                      </button>
                      {s.tasks.find((t) => t.id === artifact.task_id)
                        ?.status === "waiting_for_approval" && (
                        <button
                          className="secondary"
                          onClick={() =>
                            action(
                              "/tasks/" +
                                artifact.task_id +
                                "/accept-artifact/" +
                                artifact.id,
                            )
                          }
                        >
                          Accept this artifact
                          <Check size={14} />
                        </button>
                      )}
                    </article>
                  ))}
                </div>
              </>
            )}
            {page === "Settings" && (
              <div className="settings-grid">
                <article>
                  <h3>Founder control</h3>
                  <p>
                    Authorization is enforced on the server. Paid execution
                    requires explicit opt-in and configured provider prices.
                  </p>
                  <form
                    onSubmit={(e) =>
                      submitted(e, (f) =>
                        action(
                          "/company/policy",
                          {
                            mode: f.get("mode"),
                            monthly_limit: Number(f.get("limit")),
                            max_paid_concurrency: Number(f.get("concurrency")),
                            paid_execution_authorized: f.get("paid") === "on",
                          },
                          "PUT",
                        ),
                      )
                    }
                  >
                    <label>
                      Autonomy mode
                      <select name="mode" defaultValue={s.organization.mode}>
                        <option value="research_only">Research only</option>
                        <option value="build_autopilot">Build autopilot</option>
                        <option value="approved_growth">Approved growth</option>
                      </select>
                    </label>
                    <label>
                      Monthly limit · THB
                      <input
                        name="limit"
                        type="number"
                        min="0"
                        max="1000000"
                        defaultValue={s.organization.monthly_limit}
                      />
                    </label>
                    <label>
                      Concurrent paid runs
                      <select
                        name="concurrency"
                        defaultValue={s.organization.max_paid_concurrency}
                      >
                        <option value="1">1</option>
                        <option value="2">2</option>
                      </select>
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        name="paid"
                        defaultChecked={
                          s.organization.paid_execution_authorized
                        }
                      />
                      Authorize paid execution within these limits
                    </label>
                    <button className="primary" disabled={busy}>
                      Save owner policy
                      <Check size={15} />
                    </button>
                  </form>
                  <button
                    className="danger"
                    onClick={() => action("/company/stop")}
                  >
                    <Power size={16} />
                    STOP ALL
                  </button>
                </article>
                <article>
                  <h3>Provider connections</h3>
                  <p>
                    Credentials belong in your deployment secret manager.
                    Connection status indicates configuration, not a verified
                    provider handshake.
                  </p>
                  {Object.entries(s.integrations).map(([k, v]) => (
                    <div className="provider-row" key={k}>
                      <span>{k}</span>
                      <Status value={v} />
                    </div>
                  ))}
                  <div className="info-strip">
                    <Mail size={17} />
                    Founder notification destination: traisorn.th@gmail.com
                  </div>
                  <p className="muted">
                    Read the deployment guide for scoped credentials, Gmail send
                    authorization, sandbox gateway, private artifact storage and
                    signed billing webhooks.
                  </p>
                </article>
              </div>
            )}
            {page === "Overview" && (
              <div className="overview-grid">
                <article className="overview-card">
                  <span className="eyebrow">THE WORK</span>
                  <h2>{s.tasks.length} tasks. Real accountability.</h2>
                  <div className="overview-stats">
                    {["ready", "running", "completed", "blocked"].map((st) => (
                      <div key={st}>
                        <b>{s.tasks.filter((t) => t.status === st).length}</b>
                        <Status value={st} />
                      </div>
                    ))}
                  </div>
                  <button className="secondary" onClick={() => go("Tasks")}>
                    Explore work queue
                    <ArrowRight size={15} />
                  </button>
                </article>
                <article className="overview-card">
                  <span className="eyebrow">WHAT NEEDS YOU</span>
                  <h2>
                    {s.messages.filter((m) => m.state === "open").length}{" "}
                    founder requests
                  </h2>
                  <p>
                    Decisions, critical blockers and provider setup. Routine
                    work stays with the team.
                  </p>
                  <button
                    className="secondary"
                    onClick={() => go("Founder Inbox")}
                  >
                    Open inbox
                    <ArrowRight size={15} />
                  </button>
                </article>
                <article className="overview-card">
                  <span className="eyebrow">INDEPENDENT OVERSIGHT</span>
                  <h2>{s.incidents.length} incidents recorded</h2>
                  <p>
                    Watchtower monitors the real evidence behind operational
                    claims.
                  </p>
                  <button
                    className="secondary"
                    onClick={() => go("Watchtower")}
                  >
                    Visit Watchtower
                    <ArrowRight size={15} />
                  </button>
                </article>
              </div>
            )}
          </section>
        )}
        <footer className="page-footer">
          <span>
            <span className="live-dot" />
            Persistent PostgreSQL state ·{" "}
            {s.organization.mode.replaceAll("_", " ")}
          </span>
          <span>
            Built with intention. Governed by you.
            <Box size={13} />
          </span>
        </footer>
      </main>
      {modal && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div className="modal">
            <div className="section-title">
              <h2 id="modal-title">
                {modal === "project"
                  ? "Start something useful."
                  : "Make the next step clear."}
              </h2>
              <button
                aria-label="Close dialog"
                className="icon-button"
                onClick={() => setModal(null)}
              >
                <X size={19} />
              </button>
            </div>
            <p>
              {modal === "project"
                ? "Give your team a goal worth building toward."
                : "Tasks need a project, an objective and verifiable acceptance criteria."}
            </p>
            <form
              onSubmit={(e) =>
                submitted(e, (f) =>
                  modal === "project"
                    ? action("/projects", {
                        name: f.get("name"),
                        description: f.get("description"),
                      })
                    : action("/tasks", {
                        project_id: f.get("project"),
                        title: f.get("name"),
                        objective: f.get("description"),
                        acceptance: String(f.get("acceptance"))
                          .split("\n")
                          .filter(Boolean),
                        agent_role: f.get("role"),
                      }),
                )
              }
            >
              {modal === "task" && (
                <label>
                  Project
                  <select name="project" required>
                    <option value="">Choose a project</option>
                    {s.projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <label>
                {modal === "project" ? "Project name" : "Task title"}
                <input
                  name="name"
                  minLength={3}
                  maxLength={160}
                  required
                  placeholder={
                    modal === "project"
                      ? "e.g. A better invoicing workflow"
                      : "e.g. Research customer pain points"
                  }
                />
              </label>
              <label>
                {modal === "project" ? "Goal & context" : "Objective"}
                <textarea
                  name="description"
                  minLength={modal === "task" ? 5 : 0}
                  rows={3}
                  required
                  placeholder="What should the team accomplish?"
                />
              </label>
              {modal === "task" && (
                <>
                  <label>
                    Acceptance criteria · one per line
                    <textarea
                      name="acceptance"
                      required
                      rows={3}
                      placeholder="Cite at least three primary sources"
                    />
                  </label>
                  <label>
                    Responsible agent
                    <select name="role">
                      {s.roles.map((r) => (
                        <option key={r.id} value={r.key}>
                          {r.config.role}
                        </option>
                      ))}
                    </select>
                  </label>
                </>
              )}
              <button className="primary" disabled={busy}>
                {busy
                  ? "Saving…"
                  : modal === "project"
                    ? "Create project"
                    : "Create task"}
                <ArrowRight size={15} />
              </button>
            </form>
          </div>
        </div>
      )}
      {error && (
        <div className="error-toast" role="alert">
          <AlertTriangle size={18} />
          {error}
          <button aria-label="Dismiss error" onClick={() => setError("")}>
            <X size={16} />
          </button>
        </div>
      )}
      {inspection && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Artifact inspection"
        >
          <div className="modal">
            <div className="section-title">
              <h2>Artifact evidence</h2>
              <button
                className="icon-button"
                aria-label="Close artifact inspection"
                onClick={() => setInspection(null)}
              >
                <X size={18} />
              </button>
            </div>
            <code>{inspection.artifact.sha256}</code>
            {inspection.content?.pr?.url?.startsWith("https://github.com/") && (
              <a
                className="secondary"
                href={inspection.content.pr.url}
                target="_blank"
                rel="noreferrer"
              >
                Open verified draft PR
                <ExternalLink size={14} />
              </a>
            )}
            <pre>{JSON.stringify(inspection.content, null, 2)}</pre>
          </div>
        </div>
      )}
      {toast && (
        <div className="toast" role="status">
          <Check size={17} />
          {toast}
        </div>
      )}
    </div>
  );
}
