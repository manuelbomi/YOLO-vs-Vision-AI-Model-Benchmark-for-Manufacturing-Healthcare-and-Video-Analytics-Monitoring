import { useEffect, useState } from "react";
import { fetchArenaModels, fetchHealth } from "./lib/api";
import type { ArenaModelInfo } from "./types";
import { HealthBanner } from "./components/HealthBanner";
import { ArenaPage } from "./pages/ArenaPage";
import { LiveMonitorPage } from "./pages/LiveMonitorPage";
import { DriftPage } from "./pages/DriftPage";
import { RegistryPage } from "./pages/RegistryPage";
import { WebcamPage } from "./pages/WebcamPage";
import "./App.css";

type Tab = "arena" | "live" | "webcam" | "drift" | "registry";

const TABS: { id: Tab; label: string }[] = [
  { id: "arena", label: "Model Arena" },
  { id: "live", label: "Live Monitor" },
  { id: "webcam", label: "Webcam (WebRTC)" },
  { id: "drift", label: "Drift Monitor" },
  { id: "registry", label: "Model Registry" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("arena");
  const [healthStatus, setHealthStatus] = useState<"checking" | "ok" | "not-ready" | "unreachable">("checking");
  const [healthError, setHealthError] = useState<string | null>(null);
  const [models, setModels] = useState<ArenaModelInfo[]>([]);

  useEffect(() => {
    fetchHealth()
      .then((h) => setHealthStatus(h.models_ready ? "ok" : "not-ready"))
      .catch((err: Error) => {
        setHealthStatus("unreachable");
        setHealthError(err.message);
      });
    fetchArenaModels()
      .then(setModels)
      .catch(() => undefined);
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <h1>Vision Model Benchmark</h1>
        <p className="subtitle">
          Compare YOLO, a two-stage CNN detector, a transformer detector, and a
          small vision-language model across manufacturing, healthcare, and
          video-analytics scenarios — with real RTSP/WebRTC ingestion, data
          drift detection, and a model registry.
        </p>
      </header>

      <HealthBanner status={healthStatus} error={healthError} />

      <nav className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? "tab active" : "tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === "arena" && <ArenaPage />}
        {tab === "live" && <LiveMonitorPage models={models} />}
        {tab === "webcam" && <WebcamPage models={models} />}
        {tab === "drift" && <DriftPage />}
        {tab === "registry" && <RegistryPage />}
      </main>

      <footer className="page-footer">
        <p>
          Backend: FastAPI in <code>api/</code>. See <code>README.md</code> and{" "}
          <code>frontend/README.md</code>.
        </p>
      </footer>
    </div>
  );
}
