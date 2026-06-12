import type { CropOption } from "../types";

type UploadPanelProps = {
  grainFile: File | null;
  grainPreviewUrl: string | null;
  moistureFile: File | null;
  moisturePreviewUrl: string | null;
  cropOptions: CropOption[];
  cropType: string;
  cropVariety: string;
  confidenceThreshold: number;
  isAnalyzing: boolean;
  modelReady: boolean;
  onGrainFileChange: (file: File | null) => void;
  onMoistureFileChange: (file: File | null) => void;
  onCropTypeChange: (cropType: string) => void;
  onCropVarietyChange: (cropVariety: string) => void;
  onConfidenceThresholdChange: (value: number) => void;
  onAnalyze: () => void;
};

export function UploadPanel({
  grainFile,
  grainPreviewUrl,
  moistureFile,
  moisturePreviewUrl,
  cropOptions,
  cropType,
  cropVariety,
  confidenceThreshold,
  isAnalyzing,
  modelReady,
  onGrainFileChange,
  onMoistureFileChange,
  onCropTypeChange,
  onCropVarietyChange,
  onConfidenceThresholdChange,
  onAnalyze
}: UploadPanelProps) {
  const selectedCrop = cropOptions.find((option) => option.value === cropType);
  const varieties = selectedCrop?.varieties ?? [];
  const canAnalyze = Boolean(grainFile && moistureFile && cropType && cropVariety && modelReady && !isAnalyzing);

  return (
    <section className="panel upload-panel">
      <div className="panel__header">
        <div>
          <h2>Batch inputs</h2>
          <p>Upload the grain lot and the moisture meter display for one combined grade decision.</p>
        </div>
      </div>

      <div className="drop-grid">
        <UploadSlot
          title="Grain image"
          previewUrl={grainPreviewUrl}
          file={grainFile}
          alt="Selected grain lot preview"
          onChange={onGrainFileChange}
        />
        <UploadSlot
          title="Moisture meter image"
          previewUrl={moisturePreviewUrl}
          file={moistureFile}
          alt="Selected moisture meter display preview"
          onChange={onMoistureFileChange}
        />
      </div>

      <div className="field-grid">
        <label>
          <span>Grain type</span>
          <select value={cropType} onChange={(event) => onCropTypeChange(event.target.value)}>
            {cropOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Variety</span>
          <select value={cropVariety} onChange={(event) => onCropVarietyChange(event.target.value)}>
            {varieties.map((option) => (
              <option key={option.value} value={option.label}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Confidence floor</span>
          <input
            type="number"
            min="0"
            max="100"
            value={confidenceThreshold}
            onChange={(event) => onConfidenceThresholdChange(Number(event.target.value))}
          />
        </label>

        <label>
          <span>Meter OCR</span>
          <input value="Required from moisture image" readOnly />
        </label>
      </div>

      <button
        className="primary-action"
        type="button"
        disabled={!canAnalyze}
        onClick={onAnalyze}
      >
        {isAnalyzing ? "Analyzing..." : "Analyze batch"}
      </button>
    </section>
  );
}

function UploadSlot({
  title,
  previewUrl,
  file,
  alt,
  onChange
}: {
  title: string;
  previewUrl: string | null;
  file: File | null;
  alt: string;
  onChange: (file: File | null) => void;
}) {
  return (
    <div>
      <label className="drop-zone drop-zone--compact">
        <input
          type="file"
          accept="image/jpeg,image/png"
          onChange={(event) => onChange(event.target.files?.[0] ?? null)}
        />
        {previewUrl ? (
          <img src={previewUrl} alt={alt} />
        ) : (
          <span>
            <strong>{title}</strong>
            <small>Select JPG or PNG</small>
          </span>
        )}
      </label>
      {file ? <div className="file-row">{file.name}</div> : null}
    </div>
  );
}
