import { useEffect, useState, type ReactNode } from "react";
import type { AnalyzeResponse, FeedbackPayload } from "../types";
import { StatusPill } from "./StatusPill";

type GradeValue = "A" | "B" | "C";
type MoistureValue = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

type FeedbackPanelProps = {
  result: AnalyzeResponse | null;
  isSubmitting: boolean;
  statusText: string;
  onSubmit: (payload: FeedbackPayload) => void;
};

const gradeOptions: GradeValue[] = ["A", "B", "C"];
const moistureOptions: MoistureValue[] = ["LOW", "MODERATE", "HIGH", "CRITICAL"];

function gradeTone(value: GradeValue): "ready" | "warn" | "danger" {
  return value === "A" ? "ready" : value === "B" ? "warn" : "danger";
}

function moistureTone(value: MoistureValue): "ready" | "warn" | "danger" {
  return value === "LOW" ? "ready" : value === "MODERATE" ? "warn" : "danger";
}

function formatMoisture(result: AnalyzeResponse): string {
  if (result.moisture.machine_percent !== null) {
    return `${result.moisture.machine_percent.toFixed(2)}%`;
  }
  if (result.moisture.percent_estimate !== null) {
    return `${result.moisture.percent_estimate.toFixed(2)}% estimate`;
  }
  return result.moisture.risk_level;
}

export function FeedbackPanel({ result, isSubmitting, statusText, onSubmit }: FeedbackPanelProps) {
  const [trueGrade, setTrueGrade] = useState<GradeValue>("B");
  const [trueGrainGrade, setTrueGrainGrade] = useState<GradeValue>("B");
  const [trueMoisture, setTrueMoisture] = useState<MoistureValue>("MODERATE");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (result) {
      setTrueGrade(result.quality.grade);
      setTrueGrainGrade(result.quality.grain_grade ?? result.quality.grade);
      setTrueMoisture(result.moisture.risk_level);
      setNotes("");
    }
  }, [result]);

  const disabled = !result || isSubmitting;

  return (
    <section className="panel feedback-panel" id="correction">
      <div className="panel__header">
        <div>
          <h2>Operator Correction</h2>
          <p>Store the human correction so future similar samples can reuse it.</p>
        </div>
      </div>

      {result ? (
        <div className="correction-summary" aria-label="Current model prediction">
          <div>
            <span>Final model grade</span>
            <StatusPill label={`Grade ${result.quality.grade}`} tone={gradeTone(result.quality.grade)} />
          </div>
          <div>
            <span>Grain-only grade</span>
            <StatusPill label={`Grade ${result.quality.grain_grade}`} tone={gradeTone(result.quality.grain_grade)} />
          </div>
          <div>
            <span>Moisture reading</span>
            <strong>{formatMoisture(result)}</strong>
          </div>
          <div>
            <span>Analysis id</span>
            <strong>{result.analysis_id}</strong>
          </div>
        </div>
      ) : (
        <div className="empty-state empty-state--compact">
          <strong>No analysis selected</strong>
          <span>Run one batch analysis before submitting an operator correction.</span>
        </div>
      )}

      <div className="correction-grid">
        <CorrectionGroup label="Correct final grade">
          <div className="segmented-control" role="group" aria-label="Correct final grade">
            {gradeOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={`segment-button segment-button--${gradeTone(option)} ${trueGrade === option ? "segment-button--selected" : ""}`}
                disabled={disabled}
                onClick={() => setTrueGrade(option)}
              >
                Grade {option}
              </button>
            ))}
          </div>
        </CorrectionGroup>

        <CorrectionGroup label="Correct grain grade">
          <div className="segmented-control" role="group" aria-label="Correct grain grade">
            {gradeOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={`segment-button segment-button--${gradeTone(option)} ${trueGrainGrade === option ? "segment-button--selected" : ""}`}
                disabled={disabled}
                onClick={() => setTrueGrainGrade(option)}
              >
                Grade {option}
              </button>
            ))}
          </div>
        </CorrectionGroup>

        <CorrectionGroup label="Correct moisture">
          <div className="segmented-control segmented-control--moisture" role="group" aria-label="Correct moisture">
            {moistureOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={`segment-button segment-button--${moistureTone(option)} ${trueMoisture === option ? "segment-button--selected" : ""}`}
                disabled={disabled}
                onClick={() => setTrueMoisture(option)}
              >
                {option}
              </button>
            ))}
          </div>
        </CorrectionGroup>
      </div>

      <label className="notes-field">
        <span>Correction note</span>
        <textarea disabled={disabled} value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="What should the next run learn from this result?" />
      </label>

      <button
        type="button"
        className="secondary-action"
        disabled={disabled}
        onClick={() => {
          if (!result) return;
          onSubmit({
            analysis_id: result.analysis_id,
            true_grade: trueGrade,
            true_grain_grade: trueGrainGrade,
            true_moisture_risk: trueMoisture,
            notes
          });
        }}
      >
        {isSubmitting ? "Saving..." : "Save operator correction"}
      </button>

      {statusText ? <p className="form-status">{statusText}</p> : null}
    </section>
  );
}

function CorrectionGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="correction-group">
      <span>{label}</span>
      {children}
    </div>
  );
}
