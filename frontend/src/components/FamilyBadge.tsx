import type { ModelFamily } from "../types";
import "./FamilyBadge.css";

const FAMILY_LABEL: Record<ModelFamily, string> = {
  yolo: "YOLO",
  cnn: "CNN (two-stage)",
  transformer: "Transformer",
  vlm: "Small VLM",
};

export function FamilyBadge({ family }: { family: ModelFamily }) {
  return (
    <span className={`family-badge family-${family}`}>
      <span className="family-dot" aria-hidden />
      {FAMILY_LABEL[family]}
    </span>
  );
}
