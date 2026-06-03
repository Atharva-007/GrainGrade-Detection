# Implementation Tasks

## Phase 1 - Preserve Current Behavior

- Keep `QualityGrade` as `A/B/C`.
- Keep `MoistureRisk` as `LOW/MODERATE/HIGH/CRITICAL`.
- Keep `GradingResult` response fields unchanged.
- Keep `RagiRuleEngine` as final decision owner.
- Keep `RAGEngine.discover_documents()` limited to canonical root docs.
- Keep local OpenCV proxy extraction before Qwen-VL.

## Phase 2 - Provider Configuration

- Add provider config in `VisionRAGPipeline`.
- Read `QWEN_VL_PROVIDER`, `QWEN_VL_MODEL`, `QWEN_VL_BASE_URL`, `QWEN_VL_API_KEY`, and `QWEN_VL_TIMEOUT_SECONDS`.
- Support provider aliases:
  - `dashscope`
  - `siliconflow`
  - `custom`
  - `ollama`
- Preserve backward compatibility for `siliconflow_api_key`, `use_ollama`, and `ollama_url`.
- Default the Streamlit app to DashScope Qwen3-VL cloud mode.

## Phase 3 - Cloud Request Path

- Build one OpenAI-compatible `/chat/completions` request path for cloud providers.
- Send image as a data URL in `image_url`.
- Send compact grading prompt as text.
- Use strict JSON prompting.
- Parse standard content and provider-specific reasoning fields.
- Keep local Ollama native `/api/chat` and streaming `/api/generate` paths for local mode.

## Phase 4 - Streamlit Runtime UX

- Replace Ollama-only readiness copy with provider-neutral runtime status.
- Show cloud configuration status when provider is `dashscope`, `siliconflow`, or `custom`.
- Show Ollama service/model status only when provider is `ollama`.
- Disable Analyze until the selected runtime is configured.
- Show the configured provider/model in the workflow trace.

## Phase 5 - Tests

- Add mocked provider tests for:
  - DashScope/OpenAI-compatible request URL and payload.
  - Authorization header.
  - image data URL shape.
  - strict JSON response parsing.
  - text repair path using provider config.
- Run existing tests:
  - `test_rule_engine.py`
  - `test_rag_integration.py`
  - `test_calibration_sheets.py`
  - `test_suite.py`
- Run compile check:
  - `python -m py_compile app.py vision_rag_pipeline.py`

## Phase 6 - Graph Maintenance

After code edits, run:

```bash
graphify update .
```

This keeps `graphify-out/` aligned with the changed code.

## Done Criteria

- Documentation exists under `Grain Grade MD files/`.
- App can run in cloud provider mode from env vars.
- Local Ollama mode still works when selected.
- Existing deterministic safety logic remains unchanged.
- Tests pass or any failures are documented with exact cause.
- Graphify update has been run after code changes.

