import type {
  AnalyzeResponse,
  CropCatalogResponse,
  FeedbackPayload,
  FeedbackResponse,
  HealthResponse,
  RuntimeStatus
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function parseJson<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : "Request failed.";
    throw new Error(detail);
  }
  return payload as T;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/api/health`);
  return parseJson<HealthResponse>(response);
}

export async function fetchRuntime(): Promise<RuntimeStatus> {
  const response = await fetch(`${API_BASE}/api/runtime`);
  return parseJson<RuntimeStatus>(response);
}

export async function fetchCrops(): Promise<CropCatalogResponse> {
  const response = await fetch(`${API_BASE}/api/crops`);
  return parseJson<CropCatalogResponse>(response);
}

export async function analyzeImage(
  grainFile: File,
  moistureFile: File,
  cropType: string,
  cropVariety: string,
  confidenceThreshold: number
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("grain_image", grainFile);
  form.append("moisture_image", moistureFile);
  form.append("crop_type", cropType);
  form.append("crop_variety", cropVariety);
  form.append("confidence_threshold", String(confidenceThreshold));
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: form
  });
  return parseJson<AnalyzeResponse>(response);
}

export async function submitFeedback(payload: FeedbackPayload): Promise<FeedbackResponse> {
  const response = await fetch(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseJson<FeedbackResponse>(response);
}
