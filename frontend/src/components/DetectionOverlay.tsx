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
  segmentation: "var(--family-segmentation)",
};

export function DetectionOverlay({ imageUrl, result }: DetectionOverlayProps) {
  const color = FAMILY_COLOR[result.family];
  const hasMasks = result.detections.some((d) => d.mask && d.mask.length > 0);

  return (
    <div className="detection-overlay">
      <div className="detection-overlay-frame" style={{ aspectRatio: `${result.image_width} / ${result.image_height}` }}>
        <img src={imageUrl} alt="" />
        {hasMasks && (
          // Pixel-space viewBox with preserveAspectRatio="none" maps 1:1
          // onto the percentage-based boxes below, since the frame's own
          // aspect-ratio is locked to the image's -- no separate coordinate
          // scaling needed.
          <svg
            className="detection-mask-layer"
            viewBox={`0 0 ${result.image_width} ${result.image_height}`}
            preserveAspectRatio="none"
          >
            {result.detections.map(
              (det, i) =>
                det.mask &&
                det.mask.length > 0 && (
                  <polygon
                    key={i}
                    points={det.mask.map(([x, y]) => `${x},${y}`).join(" ")}
                    fill={color}
                    fillOpacity={0.35}
                    stroke={color}
                    strokeWidth={2}
                  />
                )
            )}
          </svg>
        )}
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
