import { useEffect, useState } from "react";
import { fetchLiveSources, liveStreamUrl } from "../lib/api";
import type { ArenaModelInfo, LiveSource } from "../types";
import { FamilyBadge } from "../components/FamilyBadge";
import "./LiveMonitorPage.css";

interface LiveMonitorPageProps {
  models: ArenaModelInfo[];
}

const SCENARIO_LABEL: Record<string, string> = {
  manufacturing: "Manufacturing",
  healthcare: "Healthcare",
  video_analytics: "Video analytics",
};

export function LiveMonitorPage({ models }: LiveMonitorPageProps) {
  const [selectedModel, setSelectedModel] = useState<string>(models[0]?.name ?? "");
  const [sources, setSources] = useState<Record<string, LiveSource>>({});
  const [selectedSource, setSelectedSource] = useState<string>("manufacturing");
  const [streamKey, setStreamKey] = useState(0);

  useEffect(() => {
    fetchLiveSources()
      .then(setSources)
      .catch(() => undefined);
  }, []);

  const model = models.find((m) => m.name === selectedModel);
  const source = sources[selectedSource];

  return (
    <div className="live-page">
      <section className="panel">
        <h3>Live Monitor — real RTSP demo feeds</h3>
        <p className="muted">
          Three independent, real RTSP streams (MediaMTX + FFmpeg looping
          each scenario's sample clip — see{" "}
          <code>scripts/start_rtsp_demo.py</code> / the{" "}
          <code>mediamtx</code>/<code>camera-sim-*</code> Docker services),
          run live through the model below and streamed back as annotated
          MJPEG. Not a screen recording — this is genuine per-frame
          inference.
        </p>

        <div className="model-select-row">
          <label>
            Scenario:
            <select value={selectedSource} onChange={(e) => setSelectedSource(e.target.value)}>
              {Object.keys(sources).length > 0
                ? Object.keys(sources).map((key) => (
                    <option key={key} value={key}>
                      {SCENARIO_LABEL[key] ?? key}
                    </option>
                  ))
                : Object.entries(SCENARIO_LABEL).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
            </select>
          </label>
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

        {source && <p className="muted">{source.description}</p>}

        {selectedModel && (
          <div className="stream-frame">
            {/* key includes model+source, not just streamKey: an MJPEG
                stream is a long-lived connection, and merely changing
                `src` on the same <img> can leave the old connection open
                (competing for the browser's per-origin connection limit)
                instead of the browser cleanly aborting it. A full remount
                forces that teardown. */}
            <img
              key={`${selectedModel}-${selectedSource}-${streamKey}`}
              src={liveStreamUrl(selectedModel, selectedSource)}
              alt={`Live ${selectedModel} feed for ${selectedSource}`}
            />
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
