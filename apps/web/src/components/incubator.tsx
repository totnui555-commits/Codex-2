"use client";
import { useState, type FormEvent } from "react";
import { api, type Row, type Snapshot } from "@/lib/domain";

export function Incubator({
  snapshot,
  refresh,
}: {
  snapshot: Snapshot;
  refresh: () => Promise<unknown>;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<Record<string, Row[]>>({});
  async function mutate(path: string, body: unknown) {
    setBusy(true);
    setError("");
    try {
      await api(path, { method: "POST", body: JSON.stringify(body) });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await mutate("/experiments", {
      project_id: data.get("project_id"),
      title: data.get("title"),
      hypothesis: data.get("hypothesis"),
      metric: data.get("metric"),
      minimum_samples: Number(data.get("minimum_samples")),
      continue_rate: Number(data.get("continue_rate")) / 100,
      stop_rate: Number(data.get("stop_rate")) / 100,
    });
  }
  async function observe(event: FormEvent<HTMLFormElement>, experiment: Row) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await mutate(`/experiments/${experiment.id}/observations`, {
      expected_version: experiment.version,
      reference: data.get("reference"),
      samples: Number(data.get("samples")),
      successes: Number(data.get("successes")),
      artifact_id: data.get("artifact_id"),
      notes: data.get("notes"),
    });
    setHistory((old) => {
      const next = { ...old };
      delete next[experiment.id];
      return next;
    });
  }
  async function loadHistory(id: string) {
    setError("");
    try {
      const rows = await api<Row[]>(`/experiments/${id}/observations`);
      setHistory((old) => ({ ...old, [id]: rows }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    }
  }
  return (
    <section className="incubator" aria-label="Product Incubator">
      <h2>Product Incubator</h2>
      <p>
        Define criteria before collecting evidence. Starting an experiment only
        opens its evidence register; it does not launch a campaign, spend money
        or publish a product.
      </p>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <details className="list-card">
        <summary>Define an experiment</summary>
        {snapshot.projects.length ? (
          <form onSubmit={create}>
            <label>
              Project
              <select name="project_id" required>
                {snapshot.projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Experiment title
              <input name="title" required minLength={3} maxLength={200} />
            </label>
            <label>
              Hypothesis
              <textarea
                name="hypothesis"
                required
                minLength={10}
                maxLength={5000}
              />
            </label>
            <label>
              Success metric
              <input
                name="metric"
                required
                minLength={3}
                maxLength={120}
                placeholder="e.g. Participants completing the usability task"
              />
            </label>
            <label>
              Minimum sample size
              <input
                name="minimum_samples"
                type="number"
                required
                min={10}
                max={1000000}
                step={1}
                defaultValue={100}
              />
            </label>
            <label>
              Continue threshold (%)
              <input
                name="continue_rate"
                type="number"
                required
                min={0.01}
                max={99.99}
                step={0.01}
                defaultValue={20}
              />
            </label>
            <label>
              Stop threshold (%)
              <input
                name="stop_rate"
                type="number"
                required
                min={0}
                max={99.98}
                step={0.01}
                defaultValue={5}
              />
            </label>
            <button className="secondary" disabled={busy}>
              Save draft experiment
            </button>
          </form>
        ) : (
          <p>Create an incubation project first.</p>
        )}
      </details>
      <div className="cards">
        {(snapshot.experiments || []).map((experiment) => {
          const d = experiment.data,
            stats = d.statistics;
          const artifacts = snapshot.artifacts.filter(
            (a) =>
              a.verified &&
              snapshot.tasks.some(
                (t) => t.id === a.task_id && t.project_id === d.project_id,
              ),
          );
          return (
            <article className="list-card" key={experiment.id}>
              <span className="badge">{d.state}</span>
              <h3>{d.title}</h3>
              <p>{d.hypothesis}</p>
              <p>
                {d.metric}: {stats.successes} / {stats.samples} · minimum{" "}
                {d.minimum_samples}
              </p>
              <p>
                Recommendation: <strong>{stats.recommendation}</strong>
                {stats.interval_95 &&
                  ` · 95% interval ${(stats.interval_95[0] * 100).toFixed(1)}–${(stats.interval_95[1] * 100).toFixed(1)}%`}
              </p>
              <p>
                Continue ≥ {(d.continue_rate * 100).toFixed(1)}%; stop ≤{" "}
                {(d.stop_rate * 100).toFixed(1)}%. Recommendations use the
                confidence interval and do not authorize execution.
              </p>
              <small>
                Owner-reported evidence; not independently verified customer
                demand or revenue.
              </small>
              <div>
                {["draft", "paused"].includes(d.state) && (
                  <button
                    className="secondary"
                    disabled={busy || snapshot.organization.stopped}
                    onClick={() =>
                      mutate(`/experiments/${experiment.id}/actions`, {
                        action: "start",
                        expected_version: experiment.version,
                      })
                    }
                  >
                    Open evidence collection
                  </button>
                )}
                {d.state === "running" && (
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() =>
                      mutate(`/experiments/${experiment.id}/actions`, {
                        action: "pause",
                        expected_version: experiment.version,
                      })
                    }
                  >
                    Pause
                  </button>
                )}
                {["running", "paused"].includes(d.state) && (
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() =>
                      mutate(`/experiments/${experiment.id}/actions`, {
                        action: "conclude",
                        expected_version: experiment.version,
                      })
                    }
                  >
                    Conclude and freeze
                  </button>
                )}
              </div>
              {d.state === "running" && (
                <details>
                  <summary>Record a new evidence batch</summary>
                  {artifacts.length ? (
                    <form onSubmit={(event) => observe(event, experiment)}>
                      <label>
                        Unique batch reference
                        <input
                          name="reference"
                          required
                          minLength={3}
                          maxLength={200}
                        />
                      </label>
                      <label>
                        Samples
                        <input
                          name="samples"
                          type="number"
                          required
                          min={1}
                          max={1000000}
                          step={1}
                        />
                      </label>
                      <label>
                        Successes
                        <input
                          name="successes"
                          type="number"
                          required
                          min={0}
                          max={1000000}
                          step={1}
                        />
                      </label>
                      <label>
                        Evidence artifact
                        <select name="artifact_id" required>
                          {artifacts.map((a) => (
                            <option key={a.id} value={a.id}>
                              {a.kind} · {a.sha256.slice(0, 12)}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Source and method notes
                        <textarea name="notes" maxLength={2000} />
                      </label>
                      <button
                        className="secondary"
                        disabled={busy || snapshot.organization.stopped}
                      >
                        Record owner-reported evidence
                      </button>
                    </form>
                  ) : (
                    <p>
                      A checksummed evidence artifact from this project is
                      required before recording observations.
                    </p>
                  )}
                </details>
              )}
              <button
                className="secondary"
                onClick={() => loadHistory(experiment.id)}
              >
                View evidence receipts
              </button>
              {history[experiment.id]?.map((receipt) => (
                <p key={receipt.id}>
                  {receipt.data.reference}: {receipt.data.successes}/
                  {receipt.data.samples} · SHA-256{" "}
                  {receipt.data.artifact_sha256} ·{" "}
                  {new Date(receipt.created_at).toLocaleString()}
                </p>
              ))}
            </article>
          );
        })}
      </div>
      {!(snapshot.experiments || []).length && (
        <p>
          No experiments recorded. Counts appear only after evidence is
          submitted.
        </p>
      )}
    </section>
  );
}
