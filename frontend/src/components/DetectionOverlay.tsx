import type { PredictionResult } from "../types";
import "./DetectionOverlay.css";

interface DetectionOverlayProps {
  imageUrl: string;
  result: PredictionResult;
}

const FAMILY_COLOR: Record<string, string> = {
  yolo: "var(--family-yolo)",
  cnn: "var(--family-cnn)",
  transformer: "var(--family-transformer)",
  vlm: "var(--family-vlm)",
};

export function DetectionOverlay({ imageUrl, result }: DetectionOverlayProps) {
  const color = FAMILY_COLOR[result.family];

  return (
    <div className="detection-overlay">
      <div className="detection-overlay-frame" style={{ aspectRatio: `${result.image_width} / ${result.image_height}` }}>
        <img src={imageUrl} alt="" />
        {result.detections.map((det, i) => {
          const [x1, y1, x2, y2] = det.box;
          const left = (x1 / result.image_width) * 100;
          const top = (y1 / result.image_height) * 100;
          const width = ((x2 - x1) / result.image_width) * 100;
          const height = ((y2 - y1) / result.image_height) * 100;
          return (
            <div
              key={i}
              className="detection-box"
              style={{ left: `${left}%`, top: `${top}%`, width: `${width}%`, height: `${height}%`, borderColor: color }}
            >
              <span className="detection-label" style={{ background: color }}>
                {det.label} {(det.confidence * 100).toFixed(0)}%
              </span>
            </div>
          );
        })}
      </div>

      {result.caption && (
        <p className="detection-caption">
          <strong>Caption:</strong> "{result.caption}"
        </p>
      )}
    </div>
  );
}
