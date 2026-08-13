const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface JobCreateResponse {
  processing_id: string;
  status: string;
  message: string;
}

export interface JobStatusResponse {
  processing_id: string;
  status: string;
}

export interface JobFailureResponse {
  processing_id: string;
  status: string;
  failure_reason: string;
}

export interface ImageInfo {
  filename: string;
  width: number | null;
  height: number | null;
}

export interface BlurAnalysis {
  is_blurry: boolean;
  score: number;
  threshold: number;
}

export interface BrightnessAnalysis {
  is_low_light: boolean;
  average_brightness: number;
  threshold: number;
}

export interface DuplicateAnalysis {
  is_duplicate: boolean;
  similarity: number;
}

export interface OcrAnalysis {
  raw_text: string | null;
  normalized_text: string | null;
  confidence: number | null;
}

export interface VehicleNumberAnalysis {
  detected_number: string | null;
  format_valid: boolean;
  confidence: number | null;
}

export interface DimensionAnalysis {
  width: number;
  height: number;
  valid: boolean;
}

export interface DetailedAnalysis {
  blur: BlurAnalysis;
  brightness: BrightnessAnalysis;
  duplicate: DuplicateAnalysis;
  ocr: OcrAnalysis;
  vehicle_number: VehicleNumberAnalysis;
  dimensions: DimensionAnalysis;
}

export interface JobSummary {
  overall_status: string;
  confidence: number;
  issues: string[];
}

export interface JobResultsResponse {
  processing_id: string;
  status: string;
  image?: ImageInfo;
  analysis?: DetailedAnalysis;
  summary?: JobSummary;
  message?: string;
}

export interface JobHistoryItem {
  processing_id: string;
  filename: string;
  status: string;
  created_at: string;
  updated_at: string;
  summary?: JobSummary;
}

export interface JobHistoryResponse {
  items: JobHistoryItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export async function uploadImage(file: File): Promise<JobCreateResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/api/v1/images/`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
  }

  return response.json();
}

export async function getImageStatus(id: string): Promise<JobStatusResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/images/${id}/status`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch status with status ${response.status}`);
  }

  return response.json();
}

export async function getImageResults(id: string): Promise<JobResultsResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/images/${id}/results`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch results with status ${response.status}`);
  }

  return response.json();
}

export async function getImageFailure(id: string): Promise<JobFailureResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/images/${id}/failure`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch failure details with status ${response.status}`);
  }

  return response.json();
}

export async function getImagesHistory(
  page: number = 1,
  limit: number = 20,
  status?: string,
  search?: string
): Promise<JobHistoryResponse> {
  const params = new URLSearchParams();
  params.append("page", page.toString());
  params.append("limit", limit.toString());
  if (status) params.append("status", status);
  if (search) params.append("search", search);

  const response = await fetch(`${BASE_URL}/api/v1/images/?${params.toString()}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch history with status ${response.status}`);
  }

  return response.json();
}
