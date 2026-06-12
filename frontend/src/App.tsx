import { useEffect, useMemo, useState } from "react";
import { analyzeImage, fetchCrops, fetchHealth, submitFeedback } from "./api";
import { FeedbackPanel } from "./components/FeedbackPanel";
import { ResultPanel } from "./components/ResultPanel";
import { StatusPill } from "./components/StatusPill";
import { UploadPanel } from "./components/UploadPanel";
import type { AnalyzeResponse, CropCatalogResponse, FeedbackPayload, HealthResponse } from "./types";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [cropCatalog, setCropCatalog] = useState<CropCatalogResponse>({ crops: [] });
  const [grainFile, setGrainFile] = useState<File | null>(null);
  const [grainPreviewUrl, setGrainPreviewUrl] = useState<string | null>(null);
  const [moistureFile, setMoistureFile] = useState<File | null>(null);
  const [moisturePreviewUrl, setMoisturePreviewUrl] = useState<string | null>(null);
  const [cropType, setCropType] = useState("finger_millets");
  const [cropVariety, setCropVariety] = useState("");
  const [confidenceThreshold, setConfidenceThreshold] = useState(60);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState("");

  useEffect(() => {
    Promise.all([fetchHealth(), fetchCrops()])
      .then(([nextHealth, crops]) => {
        setHealth(nextHealth);
        setCropCatalog(crops);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!grainFile) {
      setGrainPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(grainFile);
    setGrainPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [grainFile]);

  useEffect(() => {
    if (!moistureFile) {
      setMoisturePreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(moistureFile);
    setMoisturePreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [moistureFile]);

  useEffect(() => {
    const selectedCrop = cropCatalog.crops.find((crop) => crop.value === cropType) ?? cropCatalog.crops[0];
    if (!selectedCrop) return;
    if (selectedCrop.value !== cropType) {
      setCropType(selectedCrop.value);
    }
    const hasCurrentVariety = selectedCrop.varieties.some((variety) => variety.label === cropVariety);
    if (!hasCurrentVariety) {
      setCropVariety(selectedCrop.varieties[0]?.label ?? "");
    }
  }, [cropCatalog.crops, cropType, cropVariety]);

  const runtime = health?.runtime;
  const modelReady = Boolean(runtime?.model_ready);
  const runtimeTone = modelReady ? "ready" : runtime?.runtime_online ? "warn" : "danger";

  const summary = useMemo(() => {
    if (!result) {
      return [
        ["Runtime", runtime?.runtime_label ?? "Checking"],
        ["Rules indexed", String(runtime?.chunk_count ?? 0)],
        ["Feedback queued", String(health?.pending_feedback ?? 0)]
      ];
    }
    return [
      ["Grade", result.quality.grade],
      ["Moisture", result.moisture.machine_percent !== null ? `${result.moisture.machine_percent}%` : result.moisture.risk_level],
      ["Confidence", `${result.confidence.overall}%`]
    ];
  }, [health?.pending_feedback, result, runtime?.chunk_count, runtime?.runtime_label]);

  async function handleAnalyze() {
    if (!grainFile || !moistureFile) return;
    setIsAnalyzing(true);
    setError("");
    setFeedbackStatus("");
    try {
      const payload = await analyzeImage(
        grainFile,
        moistureFile,
        cropType,
        cropVariety,
        confidenceThreshold
      );
      setResult(payload);
      const nextHealth = await fetchHealth().catch(() => null);
      if (nextHealth) setHealth(nextHealth);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleFeedback(payload: FeedbackPayload) {
    setIsSubmittingFeedback(true);
    setFeedbackStatus("");
    setError("");
    try {
      const response = await submitFeedback(payload);
      setFeedbackStatus(
        response.saved
          ? `Correction saved. Pending corrections: ${response.pending_count}. Training export: ${response.training_export_saved ? "ready" : "not written"}.`
          : "Correction was not saved."
      );
      const nextHealth = await fetchHealth().catch(() => null);
      if (nextHealth) setHealth(nextHealth);
    } catch (err) {
      setFeedbackStatus(err instanceof Error ? err.message : "Feedback failed.");
    } finally {
      setIsSubmittingFeedback(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark">AG</div>
          <div>
            <strong>AI Grain Grade</strong>
            <span>Inspection console</span>
          </div>
        </div>

        <nav className="nav-list" aria-label="Primary">
          <a className="nav-item nav-item--active" href="#inspect">Inspect Batch</a>
          <a className="nav-item" href="#rules">Applied Rules</a>
          <a className="nav-item" href="#correction">Operator Correction</a>
        </nav>

        <div className="runtime-card">
          <span>Runtime</span>
          <StatusPill label={runtime?.runtime_label ?? "Checking"} tone={runtimeTone} />
          <small>{runtime?.provider_label ?? "Waiting for API"}</small>
        </div>
      </aside>

      <section className="workspace" id="inspect">
        <header className="topbar">
          <div>
            <h1>Inspect Batch</h1>
            <p>{runtime?.runtime_detail ?? "Checking backend runtime and model configuration."}</p>
          </div>
          <StatusPill label={modelReady ? "Model ready" : "Config needed"} tone={runtimeTone} />
        </header>

        <section className="summary-strip" aria-label="Current status">
          {summary.map(([label, value]) => (
            <div key={label} className="summary-item">
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </section>

        {error ? <div className="notice notice--danger">{error}</div> : null}

        <div className="work-grid">
          <div className="left-column">
            <UploadPanel
              grainFile={grainFile}
              grainPreviewUrl={grainPreviewUrl}
              moistureFile={moistureFile}
              moisturePreviewUrl={moisturePreviewUrl}
              cropOptions={cropCatalog.crops}
              cropType={cropType}
              cropVariety={cropVariety}
              confidenceThreshold={confidenceThreshold}
              isAnalyzing={isAnalyzing}
              modelReady={modelReady}
              onGrainFileChange={setGrainFile}
              onMoistureFileChange={setMoistureFile}
              onCropTypeChange={(value) => {
                setCropType(value);
                const selectedCrop = cropCatalog.crops.find((crop) => crop.value === value);
                setCropVariety(selectedCrop?.varieties[0]?.label ?? "");
              }}
              onCropVarietyChange={setCropVariety}
              onConfidenceThresholdChange={(value) => setConfidenceThreshold(Math.max(0, Math.min(100, value)))}
              onAnalyze={handleAnalyze}
            />
            <FeedbackPanel
              result={result}
              isSubmitting={isSubmittingFeedback}
              statusText={feedbackStatus}
              onSubmit={handleFeedback}
            />
          </div>

          <div className="right-column">
            <ResultPanel result={result} isAnalyzing={isAnalyzing} />
          </div>
        </div>
      </section>
    </main>
  );
}
