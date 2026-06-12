# Current System Deep Analysis

## System Shape

Millets Now is a Streamlit-based ragi lot grading system. It accepts a single lot image, extracts deterministic visual proxy signals with OpenCV, retrieves authoritative grading rules from local Markdown docs, asks Qwen-VL for visible evidence, then applies deterministic FAO/BIS-aligned grade gates.

The architecture is intentionally conservative. The vision model is not the final grader. It supplies estimated visual evidence, while `RagiRuleEngine` owns the final grade, reject flag, and downgrade behavior.

## Graphify Architecture Hubs

The graph report identifies these core nodes:

- `FeedbackCollector`: stores and retrieves operator corrections.
- `RAGEngine`: loads and retrieves authoritative Markdown rule chunks.
- `MoistureCalibrator`: maps raw optical moisture scores to provisional moisture percent estimates.
- `VisionRAGPipeline`: orchestrates model calls, RAG, rules, confidence, and fallback behavior.
- `PhysicsProxiesExtractor`: extracts image features from the sample.
- `QualityGrade`, `MoistureRisk`, `GradingFeedbackItem`, `RagiRuleEngine`, `GradingResult`: core contracts.

These are the correct rebuild boundaries. Do not merge them into one large model-only path.

## `app.py`

`app.py` is the product shell.

Main responsibilities:

- Render the Streamlit workspace.
- Persist uploaded samples under `feedback_data/session_uploads/`.
- Show basic input checks: resolution, blur, and luminance.
- Initialize `PhysicsProxiesExtractor` and `VisionRAGPipeline`.
- Run analysis and stream Qwen-VL output when local streaming is available.
- Render final grade, moisture risk, confidence, signal highlights, overlays, and reject reasons.
- Capture human correction feedback.

Important current behavior:

- A run is blocked until the configured Qwen runtime is ready.
- The UI stores the latest analysis in `st.session_state["current_analysis"]`.
- The feedback UI writes JSON correction files through `FeedbackCollector`.

Improvement needed:

- The old UI was hard-wired to local Ollama. The improved version must read `QWEN_VL_PROVIDER`, `QWEN_VL_MODEL`, `QWEN_VL_BASE_URL`, and `QWEN_VL_API_KEY`.

## `physics_proxies.py`

`PhysicsProxiesExtractor` is the deterministic evidence layer.

It extracts:

- texture entropy
- LAB color darkness
- clumping density
- surface roughness
- highlight and reflectance signals
- grain mask coverage
- uniformity score
- calibration-sheet geometry when available
- physical properties such as grain size, shape, shine, and density

This layer is fast and local. It should run before Qwen-VL because it:

- gives immediate operator feedback
- reduces prompt ambiguity
- supplies fallback evidence if the cloud model fails
- supports auditability

## `rag_engine.py`

`RAGEngine` indexes only the canonical root Markdown docs:

- `FAO_BIS_RAGI_RULES.md`
- `AUTHORIZED_RAGI_DATA_SOURCES.md`
- `ARCHITECTURE.md`
- `UNIFIED_RAGI_QUALITY_AND_MOISTURE_SPEC.md`

It supports lexical retrieval and bge-m3 embeddings. The rebuild should keep lexical retrieval as a no-download fallback and use embedding retrieval only when local dependencies are ready.

The retrieved chunks are compressed before entering the Qwen prompt to keep latency and token use low.

## `vision_rag_pipeline.py`

`VisionRAGPipeline` is the orchestrator.

Current flow:

1. Try proxy fast path when evidence is obviously poor or high-risk.
2. Retrieve relevant RAG rule chunks.
3. Retrieve similar human corrections.
4. Build a compact grading prompt.
5. Call Qwen-VL with image and text.
6. Parse strict JSON.
7. Repair or recover JSON when the model returns text or reasoning.
8. Estimate moisture risk from physics proxies.
9. Apply `RagiRuleEngine`.
10. Compute confidence.
11. Return a `GradingResult`.

The improved version keeps this flow but makes the provider configurable:

- `dashscope`: OpenAI-compatible Qwen3-VL cloud API.
- `siliconflow`: OpenAI-compatible Qwen provider path retained for compatibility.
- `custom`: any OpenAI-compatible endpoint.
- `ollama`: local native Ollama path.

## `rule_engine.py`

`RagiRuleEngine` is the final decision authority.

It enforces:

- hard reject for mould, insects, stones, deleterious material, or visible hazards
- foreign matter outer thresholds
- damaged/broken/shrivelled load thresholds
- moisture downgrade and reject gates
- strict Grade A requirements
- Grade C assignment for bimodal, off-tone, mixed, dull, or high-risk lots
- Grade B only when neither A nor C applies

This design is correct and must be preserved.

## `moisture_calibration.py`

`MoistureCalibrator` maps a raw optical score to a provisional moisture percent.

Important limitation:

- The mapping is not a lab-certified moisture measurement.
- The UI/backend must treat percent as calibrated only when calibration evidence is present.
- Moisture risk can still be shown even when percent is not fully calibrated.

## `lora_finetune.py`

This file has two roles:

- Runtime feedback storage through `FeedbackCollector`.
- Offline/periodic training utilities for Qwen LoRA fine-tuning.

The feedback schema stores:

- predicted and corrected grade
- predicted and corrected moisture risk
- image feature vector
- confidence
- farm/batch metadata
- operator note

The rebuild should not start with LoRA training. First priority is fast cloud inference, stable schema, and feedback capture.

## Current Risks

- Local Ollama dependency can be slow or unavailable on low-end machines.
- Some docs still mention Gemma 4 or Grade D, which conflicts with the active system.
- The app has provisional moisture calibration and must avoid overclaiming.
- VLM output can be malformed; JSON repair and deterministic fallback are required.

## Rebuild Principle

Recreate the current system exactly at the behavioral boundary, then improve only the model transport and deployment path. Keep rule-based safety and auditability unchanged.

