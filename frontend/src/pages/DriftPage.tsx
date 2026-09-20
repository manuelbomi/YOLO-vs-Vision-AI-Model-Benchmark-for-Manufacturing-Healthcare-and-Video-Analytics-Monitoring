import { useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { checkDrift } from "../lib/api";
import type { FeatureDriftResult } from "../types";
import { MultiImageUploader } from "../components/MultiImageUploader";
import "./DriftPage.css";

const VERDICT_COLOR: Record<string, string> = {
  none: "#0ca30c",
  moderate: "#fab219",
  significant: "#d03b3b",
};

export function DriftPage() {
  const [referenceFiles, setReferenceFiles] = useState<File[]>([]);
  const [currentFiles, setCurrentFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<FeatureDriftResult[] | null>(null);

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
    </div>
  );
}
