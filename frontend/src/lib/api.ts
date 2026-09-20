import type {
  ArenaModelInfo,
  ArenaResponse,
  FeatureDriftResult,
  LiveSource,
  ModelVersion,
  WebhookDelivery,
} from "../types";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function fetchHealth(): Promise<{ status: string; models_ready: boolean; models_loaded: number }> {
  const response = await fetch(`${API_BASE}/api/health`);
  return handle(response);
}

// ---- Arena ----

export async function fetchArenaModels(): Promise<ArenaModelInfo[]> {
  const response = await fetch(`${API_BASE}/api/arena/models`);
  return handle(response);
}

export async function compareModels(file: File): Promise<ArenaResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/api/arena/compare`, { method: "POST", body: formData });
  return handle(response);
}

export async function compareSample(samplePath: string): Promise<ArenaResponse> {
  const formData = new FormData();
  formData.append("sample_path", samplePath);
  const response = await fetch(`${API_BASE}/api/arena/compare`, { method: "POST", body: formData });
  return handle(response);
}

export function sampleImageUrl(path: string): string {
  return `${API_BASE}/samples/${path}`;
}

// ---- Live ----

export async function fetchLiveSources(): Promise<Record<string, LiveSource>> {
  const response = await fetch(`${API_BASE}/api/live/sources`);
  return handle(response);
}

export function liveStreamUrl(model: string, source = "demo"): string {
  return `${API_BASE}/api/live/stream?model=${encodeURIComponent(model)}&source=${encodeURIComponent(source)}`;
}

// ---- Drift ----

export async function checkDrift(reference: File[], current: File[]): Promise<FeatureDriftResult[]> {
  const formData = new FormData();
  reference.forEach((f) => formData.append("reference", f));
  current.forEach((f) => formData.append("current", f));
  const response = await fetch(`${API_BASE}/api/drift/check`, { method: "POST", body: formData });
  return handle(response);
}

// ---- Registry ----

export async function fetchRegistry(): Promise<ModelVersion[]> {
  const response = await fetch(`${API_BASE}/api/registry/models`);
  return handle(response);
}

export async function promoteModel(id: number): Promise<ModelVersion> {
  const response = await fetch(`${API_BASE}/api/registry/models/${id}/promote`, { method: "POST" });
  return handle(response);
}

export async function archiveModel(id: number): Promise<ModelVersion> {
  const response = await fetch(`${API_BASE}/api/registry/models/${id}/archive`, { method: "POST" });
  return handle(response);
}

export async function registerModel(payload: {
  name: string;
  version: string;
  family: string;
  framework: string;
  task_type: string;
  approx_download_mb: number;
  metrics: Record<string, number>;
}): Promise<ModelVersion> {
  const response = await fetch(`${API_BASE}/api/registry/models`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(response);
}

// ---- Webhooks ----

export async function fetchWebhookConfig(): Promise<{ url: string | null; last_delivery: unknown }> {
  const response = await fetch(`${API_BASE}/api/webhooks/config`);
  return handle(response);
}

export async function setWebhookUrl(url: string | null): Promise<{ url: string | null }> {
  const response = await fetch(`${API_BASE}/api/webhooks/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return handle(response);
}

export async function sendTestWebhook(): Promise<unknown> {
  const response = await fetch(`${API_BASE}/api/webhooks/test`, { method: "POST" });
  return handle(response);
}

export async function fetchWebhookDeliveries(): Promise<WebhookDelivery[]> {
  const response = await fetch(`${API_BASE}/api/webhooks/deliveries`);
  return handle(response);
}

export async function retryWebhookDelivery(id: number): Promise<WebhookDelivery> {
  const response = await fetch(`${API_BASE}/api/webhooks/deliveries/${id}/retry`, { method: "POST" });
  return handle(response);
}

// ---- WebRTC ----

export async function sendWebrtcOffer(sdp: string, type: string, model: string): Promise<RTCSessionDescriptionInit> {
  const response = await fetch(`${API_BASE}/api/webrtc/offer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sdp, type, model }),
  });
  const answer = await handle<{ sdp: string; type: string }>(response);
  return { sdp: answer.sdp, type: answer.type as RTCSdpType };
}
