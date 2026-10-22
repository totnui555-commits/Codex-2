"use client";
import { useState, type FormEvent } from "react";
import { api, money, type Snapshot } from "@/lib/domain";

export function ProductPortfolio({
  snapshot,
  refresh,
}: {
  snapshot: Snapshot;
  refresh: () => Promise<unknown>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [readiness, setReadiness] = useState<Record<string, any>>({});
  async function mutate(path: string, payload: unknown) {
    setBusy(true);
    setError("");
    try {
      await api(path, { method: "POST", body: JSON.stringify(payload) });
      await refresh();
      setReadiness({});
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const f = new FormData(event.currentTarget);
    const optionalMinor = (key: string) =>
      String(f.get(key) || "").trim() === "" ? null : Number(f.get(key));
    await mutate("/products", {
      project_id: f.get("project_id"),
      name: f.get("name"),
      problem: f.get("problem"),
      target_customer: f.get("target_customer"),
      mvp_scope: String(f.get("mvp_scope"))
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean),
      currency: f.get("currency"),
      proposed_price_minor: optionalMinor("price"),
      estimated_variable_cost_minor: optionalMinor("variable"),
      estimated_monthly_fixed_cost_minor: optionalMinor("fixed"),
    });
  }
  async function check(id: string) {
    try {
      const result = await api(`/products/${id}/readiness`);
      setReadiness((old) => ({ ...old, [id]: result }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    }
  }
  return (
    <section className="incubator" aria-label="Product Portfolio">
      <h2>Product Portfolio</h2>
      <p>
        Turn a project into a defined product hypothesis. Prototype evidence,
        experiment results and publishing are tracked separately.
      </p>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <details className="list-card">
        <summary>Define a product hypothesis</summary>
        {snapshot.projects.length ? (
          <form onSubmit={create}>
            <label>
              Product project
              <select name="project_id" required>
                {snapshot.projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Product name
              <input name="name" minLength={3} maxLength={160} required />
            </label>
            <label>
              Customer problem
              <textarea
                name="problem"
                minLength={10}
                maxLength={5000}
                required
              />
            </label>
            <label>
              Target customer
              <input
                name="target_customer"
                minLength={3}
                maxLength={500}
                required
              />
            </label>
            <label>
              MVP scope · one item per line
              <textarea name="mvp_scope" required maxLength={20000} />
            </label>
            <label>
              Estimate currency
              <select name="currency">
                <option>THB</option>
                <option>USD</option>
              </select>
            </label>
            <label>
              Proposed price · satang/cents
              <input
                name="price"
                type="number"
                min={0}
                max={100000000}
                step={1}
                placeholder="Leave blank if unknown"
              />
            </label>
            <label>
              Estimated variable cost · satang/cents
              <input
                name="variable"
                type="number"
                min={0}
                max={100000000}
                step={1}
                placeholder="Leave blank if unknown"
              />
            </label>
            <label>
              Estimated monthly fixed cost · satang/cents
              <input
                name="fixed"
                type="number"
                min={0}
                max={100000000}
                step={1}
                placeholder="Leave blank if unknown"
              />
            </label>
            <button className="secondary" disabled={busy}>
              Save product hypothesis
            </button>
          </form>
        ) : (
          <p>Create an incubation project first.</p>
        )}
      </details>
      <div className="cards">
        {(snapshot.products || []).map((p) => {
          const d = p.data;
          const experiments = (snapshot.experiments || []).filter(
            (e) => e.data.project_id === d.project_id,
          );
          const artifacts = snapshot.artifacts.filter(
            (a) =>
              a.verified &&
              a.kind === "verified_pull_request" &&
              snapshot.tasks.some(
                (t) => t.id === a.task_id && t.project_id === d.project_id,
              ),
          );
          return (
            <article className="list-card" key={p.id}>
              <span className="badge">{d.state.replaceAll("_", " ")}</span>
              <h3>{d.name}</h3>
              <p>{d.problem}</p>
              <p>For: {d.target_customer}</p>
              <ul>
                {d.mvp_scope.map((item: string) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <p>
                Proposed price:{" "}
                {d.proposed_price_minor === null
                  ? "Unknown"
                  : money(d.proposed_price_minor / 100, d.currency)}
              </p>
              <p>
                Estimated break-even customers:{" "}
                {d.economics.break_even_customers ??
                  "Unknown / not achievable with these inputs"}
              </p>
              <small>
                Owner-supplied estimates; costs are incomplete. These figures
                are not sales, cash received or verified profit.
              </small>
              {d.prototype?.pr_url && (
                <p>
                  <a href={d.prototype.pr_url} target="_blank" rel="noreferrer">
                    Inspect prototype PR
                  </a>{" "}
                  · {d.prototype.commit.slice(0, 12)}
                </p>
              )}
              <p>
                {d.experiment_id
                  ? "Validation experiment linked"
                  : "No validation experiment linked"}{" "}
                · Not published
              </p>
              {d.state !== "archived" && (
                <>
                  {experiments.length > 0 && (
                    <form
                      onSubmit={(event) => {
                        event.preventDefault();
                        const f = new FormData(event.currentTarget);
                        mutate(`/products/${p.id}/experiment`, {
                          expected_version: p.version,
                          experiment_id: f.get("experiment_id"),
                        });
                      }}
                    >
                      <label>
                        Validation experiment
                        <select
                          name="experiment_id"
                          defaultValue={d.experiment_id || experiments[0].id}
                        >
                          {experiments.map((e) => (
                            <option key={e.id} value={e.id}>
                              {e.data.title} · {e.data.state}
                            </option>
                          ))}
                        </select>
                      </label>
                      <button className="secondary" disabled={busy}>
                        Link validation
                      </button>
                    </form>
                  )}
                  {artifacts.length > 0 && (
                    <form
                      onSubmit={(event) => {
                        event.preventDefault();
                        const f = new FormData(event.currentTarget);
                        mutate(`/products/${p.id}/prototype`, {
                          expected_version: p.version,
                          artifact_id: f.get("artifact_id"),
                        });
                      }}
                    >
                      <label>
                        Checked prototype artifact
                        <select name="artifact_id">
                          {artifacts.map((a) => (
                            <option key={a.id} value={a.id}>
                              {a.sha256.slice(0, 12)}
                            </option>
                          ))}
                        </select>
                      </label>
                      <button className="secondary" disabled={busy}>
                        Verify and attach prototype
                      </button>
                    </form>
                  )}
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() =>
                      mutate(`/products/${p.id}/archive`, {
                        expected_version: p.version,
                      })
                    }
                  >
                    Archive hypothesis
                  </button>
                </>
              )}
              <button className="secondary" onClick={() => check(p.id)}>
                Check remaining release gates
              </button>
              {readiness[p.id] && (
                <ul>
                  {readiness[p.id].blockers.map((item: string) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
            </article>
          );
        })}
      </div>
      {!(snapshot.products || []).length && (
        <p>
          No product hypotheses recorded. No prototypes or sales have been
          invented.
        </p>
      )}
    </section>
  );
}
