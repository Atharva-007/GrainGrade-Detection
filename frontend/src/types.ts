export type RuntimeStatus = {
  runtime_online: boolean;
  model_ready: boolean;
  runtime_label: string;
  runtime_detail: string;
  chunk_count: number;
  crop_route_count: number;
  provider: string;
  model: string;
  provider_label: string;
};

export type HealthResponse = {
  status: string;
  runtime: RuntimeStatus;
  pending_feedback: number;
};

export type CropVariety = {
  value: string;
  label: string;
  source_file: string | null;
};

export type CropOption = {
  value: string;
  label: string;
  aliases: string[];
  varieties: CropVariety[];
  rule_summary: string[];
};

export type CropCatalogResponse = {
  crops: CropOption[];
};

export type ScoreBreakdown = {
  grain_grade: "A" | "B" | "C";
  grain_score: number;
  moisture_score: number;
  final_score: number;
  metrics: Record<string, {
    value?: number | string | null;
    grade?: string;
    score?: number;
    thresholds?: Record<string, number | string>;
  }>;
  penalties: Array<{
    name: string;
    points: number;
    reason: string;
  }>;
  rule_source: string;
};

export type AppliedRule = {
  rule_id?: string | null;
  rule_name?: string | null;
  source_file?: string | null;
  evidence?: string | null;
  rule_confidence?: number | null;
};

export type AnalyzeResponse = {
  analysis_id: string;
  image_name: string;
  grain_image_name: string;
  moisture_image_name: string | null;
  quality: {
    grade: "A" | "B" | "C";
    grain_grade: "A" | "B" | "C";
    score: number;
    grain_score: number;
    moisture_score: number;
    score_breakdown: ScoreBreakdown;
    reject_recommended: boolean;
    reject_reasons: string[];
    broken_grain_percent: number;
    foreign_matter_percent: number;
    uniformity_score: number;
    mold_visible: boolean;
  };
  moisture: {
    risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
    percent_estimate: number | null;
    machine_percent: number | null;
    source: string;
    ocr_confidence: number | null;
    calibrated: boolean;
    meter_reading?: {
      percent: number;
      source: string;
      confidence: number;
      raw_text: string;
      display_text: string;
    };
  };
  confidence: {
    overall: number;
    pass1_safety_gate: number;
    pass2_grading: number;
  };
  selection: {
    selected_crop: string | null;
    selected_variety: string | null;
    requested_crop?: string | null;
    requested_variety?: string | null;
    selected_crop_confidence: number;
    selection_source: string;
  };
  routing: {
    route_label: string;
    route_provider: string | null;
    route_model: string | null;
    route_base_url: string | null;
    route_fallback_used: boolean;
    route_attempts: string[];
    route_error: string | null;
  };
  applied_rules: AppliedRule[];
  audit: {
    timestamp: string;
    model_version: string;
    rag_chunks_used: number;
    session_log_id?: string;
    session_log_path?: string | null;
  };
  proxy_summary: Record<string, number | string | null>;
  manual_review_required: boolean;
  operator_summary: string;
  signal_highlights: string[];
};

export type FeedbackPayload = {
  analysis_id: string;
  true_grade: "A" | "B" | "C";
  true_grain_grade?: "A" | "B" | "C";
  true_moisture_risk: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  notes: string;
};

export type FeedbackResponse = {
  saved: boolean;
  pending_count: number;
  analysis_id: string;
  feedback_path?: string | null;
  training_export_saved?: boolean;
  session_log_path?: string | null;
};
