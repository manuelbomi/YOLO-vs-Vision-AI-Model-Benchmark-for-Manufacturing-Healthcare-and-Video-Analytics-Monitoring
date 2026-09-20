// Mirrors api/models/base.py, api/registry/schemas.py, and
// api/drift/stats.py field-for-field so the wire format and these types
// never drift out of sync silently.

export type ModelFamily = "yolo" | "cnn" | "transformer" | "vlm";

export interface Detection {
  label: string;
  confidence: number;
  box: [number, number, number, number];
}

export interface PredictionResult {
  model_name: string;
  family: ModelFamily;
  latency_ms: number;
  image_width: number;
  image_height: number;
  detections: Detection[];
  caption: string | null;
}

export interface ArenaModelInfo {
  name: string;
  family: ModelFamily;
  description: string;
  approx_download_mb: number;
}

export interface ArenaResponse {
  image_width: number;
  image_height: number;
  results: PredictionResult[];
}

export type ApprovalStatus = "draft" | "staging" | "approved" | "archived";

export interface ModelVersion {
  id: number;
  name: string;
  version: string;
  family: string;
  framework: string;
  task_type: string;
  approx_download_mb: number;
  metrics: Record<string, number>;
  notes: string;
  approval_status: ApprovalStatus;
  created_at: string;
  promoted_at: string | null;
}

export interface FeatureDriftResult {
  feature: string;
  reference_mean: number;
  current_mean: number;
  psi: number;
  ks_statistic: number;
  ks_pvalue: number;
  cohens_d: number;
  verdict: "none" | "moderate" | "significant";
  low_variance_warning: boolean;
}

export interface LiveSource {
  url: string;
  description: string;
}

export type DeliveryStatus = "delivered" | "retrying" | "failed";

export interface WebhookDelivery {
  id: number;
  event_type: string;
  url: string;
  payload: Record<string, unknown>;
  status: DeliveryStatus;
  attempt_count: number;
  last_status_code: number | null;
  last_error: string | null;
  created_at: string;
  last_attempt_at: string | null;
  next_attempt_at: string | null;
  delivered_at: string | null;
}
