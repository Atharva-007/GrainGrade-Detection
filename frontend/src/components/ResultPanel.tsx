import type { AnalyzeResponse } from "../types";
import { StatusPill } from "./StatusPill";

type ResultPanelProps = {
  result: AnalyzeResponse | null;
  isAnalyzing: boolean;
};

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  return String(value).replaceAll("_", " ");
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

function confidenceTone(value: number | null | undefined): "ready" | "warn" | "danger" | "neutral" {
  if (value === null || value === undefined || Number.isNaN(value)) return "neutral";
  const normalized = value <= 1 ? value * 100 : value;
  if (normalized >= 80) return "ready";
  if (normalized >= 55) return "warn";
  return "danger";
}

function fileName(path: string | null | undefined): string {
  if (!path) return "Rule source not returned";
  return path.split(/[\\/]/).pop() || path;
}

export function ResultPanel({ result, isAnalyzing }: ResultPanelProps) {
  if (isAnalyzing) {
    return (
      <section className="panel result-panel result-panel--empty" id="rules">
        <div className="loading-bar" />
        <h2>Running analysis</h2>
        <p>Extracting OpenCV proxies, retrieving rules, calling Qwen-VL, and applying deterministic gates.</p>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="panel result-panel result-panel--empty" id="rules">
        <h2>Grade, moisture, and evidence will appear here</h2>
        <p>Upload a lot image and run analysis to populate the operational decision view.</p>
      </section>
    );
  }

  const gradeTone = result.quality.grade === "A" ? "ready" : result.quality.grade === "B" ? "warn" : "danger";
  const grainTone = result.quality.grain_grade === "A" ? "ready" : result.quality.grain_grade === "B" ? "warn" : "danger";
  const moistureTone = result.moisture.risk_level === "LOW" ? "ready" : result.moisture.risk_level === "MODERATE" ? "warn" : "danger";
  const meterReading = result.moisture.meter_reading;
  const breakdown = result.quality.score_breakdown;
  const penalties = breakdown?.penalties ?? [];
  const metricRows = Object.entries(breakdown?.metrics ?? {})
    .sort(([, left], [, right]) => Number(right.score ?? 0) - Number(left.score ?? 0))
    .slice(0, 8);
  const appliedRules = result.applied_rules ?? [];
  const routeAttempts = result.routing.route_attempts ?? [];

  return (
    <section className="result-stack">
      <div className="decision-band">
        <div>
          <span className="muted-label">Final Grade</span>
          <strong className={`grade grade--${result.quality.grade.toLowerCase()}`}>{result.quality.grade}</strong>
        </div>
        <div>
          <span className="muted-label">Final Score</span>
          <strong>{result.quality.score}/100</strong>
        </div>
        <div>
          <span className="muted-label">Grain Quality</span>
          <StatusPill label={`Grade ${result.quality.grain_grade}`} tone={grainTone} />
        </div>
        <div>
          <span className="muted-label">Moisture</span>
          <StatusPill label={result.moisture.risk_level} tone={moistureTone} />
        </div>
        <div>
          <span className="muted-label">Review</span>
          <StatusPill label={result.manual_review_required ? "Required" : "Clear"} tone={result.manual_review_required ? "danger" : "ready"} />
        </div>
      </div>

      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>Result</h2>
            <p>{result.operator_summary}</p>
          </div>
          <StatusPill label={`Grade ${result.quality.grade}`} tone={gradeTone} />
        </div>
        <div className="metric-grid">
          <Metric label="Final score" value={`${result.quality.score}/100`} />
          <Metric label="Grain score" value={`${result.quality.grain_score}/100`} />
          <Metric label="Moisture score" value={`${result.quality.moisture_score}/100`} />
          <Metric label="Confidence" value={`${result.confidence.overall}%`} />
          <Metric label="Crop" value={formatValue(result.selection.selected_crop ?? result.selection.requested_crop)} />
          <Metric label="Variety" value={formatValue(result.selection.selected_variety ?? result.selection.requested_variety)} />
          <Metric label="OCR confidence" value={result.moisture.ocr_confidence !== null ? `${Math.round(result.moisture.ocr_confidence * 100)}%` : "n/a"} />
          <Metric label="Uniformity" value={`${result.quality.uniformity_score.toFixed(1)}/100`} />
          <Metric label="Broken grain" value={`${result.quality.broken_grain_percent.toFixed(1)}%`} />
          <Metric label="Foreign matter" value={`${result.quality.foreign_matter_percent.toFixed(1)}%`} />
          <Metric label="Moisture source" value={formatValue(result.moisture.source)} />
        </div>
        {meterReading ? (
          <div className="notice notice--neutral">
            <strong>Moisture meter OCR</strong>
            <span>{meterReading.display_text || `${meterReading.percent}%`} from {meterReading.source}</span>
          </div>
        ) : null}
        <div className="score-breakdown">
          <div className="score-card">
            <span>Grain-only result</span>
            <strong>Grade {result.quality.grain_grade} - {result.quality.grain_score}/100</strong>
          </div>
          <div className="score-card">
            <span>Moisture contribution</span>
            <strong>{result.quality.moisture_score}/100 - {result.moisture.machine_percent !== null ? `${result.moisture.machine_percent.toFixed(2)}%` : result.moisture.risk_level}</strong>
          </div>
          <div className="score-card">
            <span>Rule source</span>
            <strong>{formatValue(breakdown?.rule_source)}</strong>
          </div>
        </div>
        {penalties.length > 0 ? (
          <div className="notice notice--neutral">
            <strong>Score penalties</strong>
            <ul>
              {penalties.slice(0, 5).map((penalty) => (
                <li key={`${penalty.name}-${penalty.reason}`}>{penalty.reason} (-{penalty.points})</li>
              ))}
            </ul>
          </div>
        ) : null}
        {result.quality.reject_reasons.length > 0 ? (
          <div className="notice notice--danger">
            <strong>Release blockers</strong>
            <ul>
              {result.quality.reject_reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      <section className="panel" id="rules">
        <div className="panel__header">
          <div>
            <h2>Applied Rules</h2>
            <p>{result.audit.rag_chunks_used} retrieved rule chunk(s), {result.routing.route_provider ?? "local"}/{result.routing.route_model ?? "deterministic route"}</p>
          </div>
          <StatusPill label={result.routing.route_fallback_used ? "Fallback route" : result.routing.route_label} tone={result.routing.route_fallback_used ? "warn" : "neutral"} />
        </div>
        {result.routing.route_error ? <div className="notice notice--danger">{result.routing.route_error}</div> : null}
        <div className="rule-context-grid" aria-label="Rule routing and audit context">
          <Metric label="Route label" value={formatValue(result.routing.route_label)} />
          <Metric label="Route attempts" value={String(routeAttempts.length)} />
          <Metric label="Session log" value={formatValue(result.audit.session_log_id ?? result.audit.session_log_path)} />
          <Metric label="Model version" value={formatValue(result.audit.model_version)} />
        </div>

        {result.signal_highlights.length > 0 ? (
          <div className="signal-strip" aria-label="Signal highlights">
            {result.signal_highlights.map((signal) => (
              <span key={signal}>{signal}</span>
            ))}
          </div>
        ) : null}

        {appliedRules.length > 0 ? (
          <div className="rule-list rule-list--detailed">
            {appliedRules.map((rule, index) => (
              <article className="rule-row" key={`${rule.rule_id ?? "rule"}-${index}`}>
                <div className="rule-row__header">
                  <div>
                    <strong>{formatValue(rule.rule_name ?? rule.rule_id ?? `Rule ${index + 1}`)}</strong>
                    <small>{formatValue(rule.rule_id ?? "rule id not returned")}</small>
                  </div>
                  <StatusPill label={formatPercent(rule.rule_confidence)} tone={confidenceTone(rule.rule_confidence)} />
                </div>
                <div className="rule-meta">
                  <span>{fileName(rule.source_file)}</span>
                </div>
                <p>{formatValue(rule.evidence ?? "Evidence captured in backend audit.")}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <strong>No applied rules returned</strong>
            <span>The backend completed the analysis but did not include rule hit details in this response.</span>
          </div>
        )}

        {routeAttempts.length > 0 ? (
          <details className="route-details">
            <summary>Route attempts</summary>
            <ol>
              {routeAttempts.map((attempt, index) => (
                <li key={`${attempt}-${index}`}>{attempt}</li>
              ))}
            </ol>
          </details>
        ) : null}
      </section>

      {metricRows.length > 0 ? (
        <section className="panel">
          <div className="panel__header">
            <div>
              <h2>Score Index</h2>
              <p>Weighted rule metrics used for grain quality and the final score.</p>
            </div>
          </div>
          <div className="score-metric-list">
            {metricRows.map(([name, metric]) => (
              <div className="score-metric-row" key={name}>
                <span>{name.replaceAll("_", " ")}</span>
                <strong>{formatValue(metric.score)}/100</strong>
                <small>{formatValue(metric.grade)} - value {formatValue(metric.value)}</small>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>Proxy Summary</h2>
            <p>Local image signals used before and after the model call.</p>
          </div>
        </div>
        <div className="proxy-grid">
          {Object.entries(result.proxy_summary).map(([key, value]) => (
            <Metric key={key} label={key.replaceAll("_", " ")} value={formatValue(value)} />
          ))}
        </div>
      </section>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
