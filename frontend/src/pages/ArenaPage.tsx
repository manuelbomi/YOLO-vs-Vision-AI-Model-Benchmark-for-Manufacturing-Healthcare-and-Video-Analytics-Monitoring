import { useEffect, useState } from "react";
import { compareModels, compareSample, sampleImageUrl } from "../lib/api";
import type { ArenaResponse } from "../types";
import { ImageUploader } from "../components/ImageUploader";
import { DetectionOverlay } from "../components/DetectionOverlay";
import { FamilyBadge } from "../components/FamilyBadge";
import "./ArenaPage.css";

const SAMPLE_IMAGES = [
  { path: "manufacturing/warehouse_1.jpg", label: "Warehouse (manufacturing)" },
  { path: "manufacturing/factory_1.jpg", label: "Factory floor (manufacturing)" },
  { path: "healthcare/ppe_workers_1.jpg", label: "PPE staff (healthcare)" },
  { path: "healthcare/medical_team_1.jpg", label: "Lab team (healthcare)" },
  { path: "video_analytics/street_1.jpg", label: "Traffic intersection (video analytics)" },
  { path: "video_analytics/street_2.jpg", label: "Night street (video analytics)" },
];

export function ArenaPage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ArenaResponse | null>(null);

  useEffect(() => {
    if (!file) return;
    setPreviewUrl(URL.createObjectURL(file));
  }, [file]);

  async function runComparison() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await compareModels(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function pickSample(path: string) {
    setLoading(true);
    setError(null);
    setFile(null);
    setPreviewUrl(sampleImageUrl(path));
    try {
      setResult(await compareSample(path));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="arena-page">
      <section className="panel">
        <h3>1. Choose an image</h3>
        <div className="sample-grid">
          {SAMPLE_IMAGES.map((s) => (
            <button key={s.path} className="sample-chip" onClick={() => pickSample(s.path)} disabled={loading}>
              <img src={sampleImageUrl(s.path)} alt={s.label} />
              <span>{s.label}</span>
            </button>
          ))}
        </div>
        <p className="or-divider">or upload your own</p>
        <ImageUploader onFileSelected={setFile} disabled={loading} label="Upload a fault/scene image" />
        <button className="run-button" onClick={runComparison} disabled={!file || loading}>
          {loading ? "Running all 4 models..." : "Run comparison"}
        </button>
        {error && <p className="error">{error}</p>}
      </section>

      {result && previewUrl && (
        <section className="panel">
          <h3>2. Results</h3>
          <div className="results-grid">
            {result.results.map((r) => (
              <div className="result-card" key={r.model_name}>
                <div className="result-card-header">
                  <strong>{r.model_name}</strong>
                  <FamilyBadge family={r.family} />
                </div>
                <DetectionOverlay imageUrl={previewUrl} result={r} />
                <div className="result-meta">
                  <span>{r.latency_ms.toFixed(0)} ms</span>
                  <span>{r.detections.length} detection(s)</span>
                </div>
              </div>
            ))}
          </div>

          <h3>Latency comparison</h3>
          <table className="latency-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Family</th>
                <th>Latency</th>
                <th>Detections</th>
              </tr>
            </thead>
            <tbody>
              {[...result.results]
                .sort((a, b) => a.latency_ms - b.latency_ms)
                .map((r) => (
                  <tr key={r.model_name}>
                    <td>{r.model_name}</td>
                    <td>
                      <FamilyBadge family={r.family} />
                    </td>
                    <td className="numeric">{r.latency_ms.toFixed(0)} ms</td>
                    <td className="numeric">{r.caption ? "—" : r.detections.length}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
