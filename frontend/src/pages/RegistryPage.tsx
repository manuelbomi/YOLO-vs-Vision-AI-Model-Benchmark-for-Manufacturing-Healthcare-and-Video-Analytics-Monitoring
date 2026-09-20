import { useEffect, useState } from "react";
import { archiveModel, fetchRegistry, promoteModel } from "../lib/api";
import type { ModelVersion } from "../types";
import "./RegistryPage.css";

const STATUS_COLOR: Record<string, string> = {
  draft: "#898781",
  staging: "#fab219",
  approved: "#0ca30c",
  archived: "#52514e",
};

export function RegistryPage() {
  const [models, setModels] = useState<ModelVersion[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function reload() {
    try {
      setModels(await fetchRegistry());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    reload();
  }, []);

  async function handlePromote(id: number) {
    setBusyId(id);
    try {
      await promoteModel(id);
      await reload();
    } finally {
      setBusyId(null);
    }
  }

  async function handleArchive(id: number) {
    setBusyId(id);
    try {
      await archiveModel(id);
      await reload();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="registry-page">
      <section className="panel">
        <h3>Model registry</h3>
        <p className="muted">
          A minimal, self-contained model-governance record per benchmarked
          model version (SQLite + SQLModel — see README &gt; Model
          governance). Empty at first: run{" "}
          <code>python scripts/seed_registry.py</code> to register the 4
          benchmarked models with their measured metrics, then promote/archive
          them here.
        </p>

        {error && <p className="error">{error}</p>}

        {models && models.length === 0 && (
          <p className="muted">
            No models registered yet — run{" "}
            <code>python scripts/seed_registry.py</code> against the API.
          </p>
        )}

        {models && models.length > 0 && (
          <table className="registry-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Version</th>
                <th>Family</th>
                <th>Metrics</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.id}>
                  <td>{m.name}</td>
                  <td>{m.version}</td>
                  <td>{m.family}</td>
                  <td className="metrics-cell">
                    {Object.entries(m.metrics).map(([k, v]) => (
                      <span key={k}>
                        {k}: {v}
                      </span>
                    ))}
                  </td>
                  <td>
                    <span className="status-badge" style={{ color: STATUS_COLOR[m.approval_status] }}>
                      ● {m.approval_status}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <button
                      disabled={busyId === m.id || m.approval_status === "archived"}
                      onClick={() => handlePromote(m.id)}
                    >
                      Promote
                    </button>
                    <button
                      disabled={busyId === m.id || m.approval_status === "archived"}
                      onClick={() => handleArchive(m.id)}
                    >
                      Archive
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
