import { useState } from "react";
import { liveStreamUrl } from "../lib/api";
import type { ArenaModelInfo } from "../types";
import { FamilyBadge } from "../components/FamilyBadge";
import "./LiveMonitorPage.css";

interface LiveMonitorPageProps {
  models: ArenaModelInfo[];
}

export function LiveMonitorPage({ models }: LiveMonitorPageProps) {
  const [selectedModel, setSelectedModel] = useState<string>(models[0]?.name ?? "");
  const [streamKey, setStreamKey] = useState(0);

  const model = models.find((m) => m.name === selectedModel);

  return (
    <div className="live-page">
      <section className="panel">
        <h3>Live Monitor — manufacturing demo feed</h3>
        <p className="muted">
          A real RTSP stream (MediaMTX + FFmpeg looping the manufacturing sample
          clip — see <code>scripts/start_rtsp_demo.py</code> / the{" "}
          <code>mediamtx</code>/<code>camera-sim</code> Docker services), run
          live through the model below and streamed back as annotated MJPEG.
          Not a screen recording — this is genuine per-frame inference.
        </p>

        <div className="model-select-row">
          <label>
            Model:
            <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
              {models.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name}
                </option>
              ))}
            </select>
          </label>
          {model && <FamilyBadge family={model.family} />}
          <button className="restart-button" onClick={() => setStreamKey((k) => k + 1)}>
            Restart stream
          </button>
        </div>

        {selectedModel && (
          <div className="stream-frame">
            <img key={streamKey} src={liveStreamUrl(selectedModel, "demo")} alt={`Live ${selectedModel} feed`} />
          </div>
        )}

        <p className="muted">
          Slower models (DETR, BLIP) will visibly lag behind the source's
          native frame rate — that's an honest, real finding about their
          resource cost for live monitoring, not a bug.
        </p>
      </section>
    </div>
  );
}
