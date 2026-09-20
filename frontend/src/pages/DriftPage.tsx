import { useEffect, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  checkDrift,
  fetchWebhookConfig,
  fetchWebhookDeliveries,
  retryWebhookDelivery,
  sendTestWebhook,
  setWebhookUrl,
} from "../lib/api";
import type { FeatureDriftResult, WebhookDelivery } from "../types";
import { MultiImageUploader } from "../components/MultiImageUploader";
import "./DriftPage.css";

const VERDICT_COLOR: Record<string, string> = {
  none: "#0ca30c",
  moderate: "#fab219",
  significant: "#d03b3b",
};

const DELIVERY_STATUS_COLOR: Record<string, string> = {
  delivered: "var(--status-good)",
  retrying: "var(--status-warning)",
  failed: "var(--status-critical)",
};

export function DriftPage() {
  const [referenceFiles, setReferenceFiles] = useState<File[]>([]);
  const [currentFiles, setCurrentFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<FeatureDriftResult[] | null>(null);

  const [webhookUrlInput, setWebhookUrlInput] = useState("");
  const [webhookSaved, setWebhookSaved] = useState<string | null>(null);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [webhookBusy, setWebhookBusy] = useState(false);
  const [webhookError, setWebhookError] = useState<string | null>(null);

  async function refreshDeliveries() {
    try {
      setDeliveries(await fetchWebhookDeliveries());
    } catch (err) {
      setWebhookError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    fetchWebhookConfig().then((config) => setWebhookSaved(config.url)).catch(() => undefined);
    refreshDeliveries();
    // Deliveries change on their own as the background retry worker fires
    // (see api/webhooks_worker.py) -- poll rather than only refreshing on
    // user action, so a delivery that just went from "retrying" to
    // "delivered" (or "failed") shows up without a manual refresh.
    const interval = setInterval(refreshDeliveries, 5000);
    return () => clearInterval(interval);
  }, []);

  async function run() {
    if (referenceFiles.length < 3 || currentFiles.length < 3) {
      setError("Each batch needs at least 3 images for the statistics to be meaningful.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setResults(await checkDrift(referenceFiles, currentFiles));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
    refreshDeliveries();
  }

  async function saveWebhookUrl() {
    setWebhookBusy(true);
    setWebhookError(null);
    try {
      const result = await setWebhookUrl(webhookUrlInput || null);
      setWebhookSaved(result.url);
    } catch (err) {
      setWebhookError(err instanceof Error ? err.message : String(err));
    } finally {
      setWebhookBusy(false);
    }
  }

  async function fireTestEvent() {
    setWebhookBusy(true);
    setWebhookError(null);
    try {
      await sendTestWebhook();
      await refreshDeliveries();
    } catch (err) {
      setWebhookError(err instanceof Error ? err.message : String(err));
    } finally {
      setWebhookBusy(false);
    }
  }

  async function retryNow(id: number) {
    setWebhookBusy(true);
    try {
      await retryWebhookDelivery(id);
      await refreshDeliveries();
    } catch (err) {
      setWebhookError(err instanceof Error ? err.message : String(err));
    } finally {
      setWebhookBusy(false);
    }
  }

  return (
    <div className="drift-page">
      <section className="panel">
        <h3>Data drift check</h3>
        <p className="muted">
          Upload a "reference" (baseline) batch and a "current" batch of
          images. This computes Population Stability Index, a two-sample
          KS-test, and Cohen's d on simple image features (brightness,
          contrast, saturation) between the two batches — see README &gt; Data
          drift for what these numbers mean. A tip from building this: use
          images with real per-image variance in each batch, not exact
          duplicates — identical images give zero within-batch variance,
          which breaks the standardized-effect-size math.
        </p>

        <div className="upload-row">
          <MultiImageUploader label="Reference batch" onFilesSelected={setReferenceFiles} disabled={loading} />
          <MultiImageUploader label="Current batch" onFilesSelected={setCurrentFiles} disabled={loading} />
        </div>

        <button className="run-button" onClick={run} disabled={loading}>
          {loading ? "Checking..." : "Check drift"}
        </button>
        {error && <p className="error">{error}</p>}
      </section>

      {results && (
        <section className="panel">
          <h3>PSI by feature</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={results} margin={{ top: 20, right: 16, bottom: 8, left: 0 }}>
              <XAxis dataKey="feature" tick={{ fill: "var(--text-secondary)", fontSize: 13 }} axisLine={{ stroke: "var(--grid)" }} tickLine={false} />
              <YAxis hide />
              <Tooltip formatter={(value) => [Number(value).toFixed(3), "PSI"]} />
              <Bar dataKey="psi" radius={[4, 4, 0, 0]} maxBarSize={64}>
                {results.map((r) => (
                  <Cell key={r.feature} fill={VERDICT_COLOR[r.verdict]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <table className="drift-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Reference mean</th>
                <th>Current mean</th>
                <th>PSI</th>
                <th>KS p-value</th>
                <th>Cohen's d</th>
                <th>Verdict</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.feature}>
                  <td>{r.feature}</td>
                  <td className="numeric">{r.reference_mean.toFixed(2)}</td>
                  <td className="numeric">{r.current_mean.toFixed(2)}</td>
                  <td className="numeric">{r.psi.toFixed(3)}</td>
                  <td className="numeric">{r.ks_pvalue.toFixed(4)}</td>
                  <td className="numeric">{r.cohens_d.toFixed(2)}</td>
                  <td>
                    <span className="verdict-badge" style={{ color: VERDICT_COLOR[r.verdict] }}>
                      ● {r.verdict}
                    </span>
                    {r.low_variance_warning && (
                      <span className="low-variance-note" title="Both batches had ~zero within-batch variance, so this verdict falls back to a plain relative-mean-shift check instead of the standardized statistics.">
                        {" "}⚠ low-variance fallback
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="panel">
        <h3>Webhooks</h3>
        <p className="muted">
          When a drift check finds a "significant" verdict, this platform
          fires a <code>drift.significant</code> webhook — a plain HTTP POST
          of the finding to a URL you configure below. Delivery is durable:
          a failed attempt is retried with exponential backoff by a
          background worker (see <code>api/webhooks_worker.py</code>) for up
          to 5 attempts before it's marked permanently failed, rather than
          being logged once and forgotten.
        </p>

        <div className="webhook-config-row">
          <input
            type="text"
            placeholder="https://example.com/your-webhook-endpoint"
            value={webhookUrlInput}
            onChange={(e) => setWebhookUrlInput(e.target.value)}
            disabled={webhookBusy}
          />
          <button className="run-button" onClick={saveWebhookUrl} disabled={webhookBusy}>
            Save
          </button>
          <button className="run-button" onClick={fireTestEvent} disabled={webhookBusy || !webhookSaved}>
            Send test event
          </button>
        </div>
        <p className="muted">
          {webhookSaved ? <>Currently configured: <code>{webhookSaved}</code></> : "No webhook URL configured yet."}
        </p>
        {webhookError && <p className="error">{webhookError}</p>}

        {deliveries.length > 0 && (
          <table className="drift-table">
            <thead>
              <tr>
                <th>Event</th>
                <th>Status</th>
                <th>Attempts</th>
                <th>Last error</th>
                <th>Next retry</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {deliveries.map((d) => (
                <tr key={d.id}>
                  <td>{d.event_type}</td>
                  <td>
                    <span className="verdict-badge" style={{ color: DELIVERY_STATUS_COLOR[d.status] }}>
                      ● {d.status}
                    </span>
                  </td>
                  <td className="numeric">{d.attempt_count}</td>
                  <td>{d.last_error ?? "—"}</td>
                  <td>{d.next_attempt_at ? new Date(d.next_attempt_at).toLocaleTimeString() : "—"}</td>
                  <td>
                    {d.status !== "delivered" && (
                      <button className="retry-button" onClick={() => retryNow(d.id)} disabled={webhookBusy}>
                        Retry now
                      </button>
                    )}
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
