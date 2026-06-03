# Millets Now Grain Grade Rebuild - Master Index

## Purpose

This documentation package explains the current Millets Now ragi grain-grade project and defines the improved rebuild using cloud Qwen3-VL through an OpenAI-compatible API.

The goal is to recreate the same grain grading behavior, then improve speed and deployment reliability by moving the vision model call from local Ollama-only inference to configurable cloud Qwen3-VL inference.

## Current Source Of Truth

Use these existing files as the active source of truth:

- `UNIFIED_RAGI_QUALITY_AND_MOISTURE_SPEC.md`: canonical product scope, grade schema, moisture-risk policy, and safety limits.
- `FAO_BIS_RAGI_RULES.md`: authoritative retrieval/rule anchor for grade, reject, moisture, and foreign-matter thresholds.
- `AUTHORIZED_RAGI_DATA_SOURCES.md`: approved public sources and physical properties to extract.
- `ARCHITECTURE.md`: implementation architecture and active-learning overview.

Older docs under `docs/prompts/model-doc/` are useful for prompt history, but they include legacy `Gemma 4` and `Grade D` concepts. In this rebuild, `D` must be represented as `quality_grade = "C"` plus `reject_recommended = true`.

## New Documentation Files

- `01_CURRENT_SYSTEM_DEEP_ANALYSIS.md`: detailed walkthrough of every important current module.
- `02_GRAIN_GRADE_PRODUCT_SPEC.md`: exact product behavior to recreate.
- `03_QWEN3_VL_CLOUD_ARCHITECTURE.md`: improved cloud Qwen3-VL architecture and provider configuration.
- `04_IMPLEMENTATION_TASKS.md`: engineering checklist for rebuilding and verifying the improved system.

## Current Code Map

- `app.py`: Streamlit UI, upload flow, image validation metrics, runtime status, feedback form, and result rendering.
- `physics_proxies.py`: OpenCV feature extraction, calibration-sheet detection, sample-field crop, grain segmentation, and visual proxy metrics.
- `vision_rag_pipeline.py`: RAG retrieval, Qwen-VL calls, prompt assembly, JSON repair, moisture-risk estimation, deterministic fallback, and final result contract.
- `rag_engine.py`: Markdown chunking and lexical/embedding retrieval over the root authoritative docs.
- `rule_engine.py`: deterministic FAO/BIS-aligned final grade gate.
- `moisture_calibration.py`: provisional optical-score to moisture-percent mapping.
- `lora_finetune.py`: feedback storage, feedback retrieval, and Qwen LoRA training utilities.

## Rebuild Order

1. Preserve current schema and grade policy.
2. Preserve OpenCV physics proxies and overlays.
3. Preserve RAG retrieval over authoritative root Markdown docs.
4. Make Qwen-VL provider configurable by environment variables.
5. Default the improved app to cloud Qwen3-VL for lower local hardware burden.
6. Keep deterministic rule gates as final authority.
7. Keep local Ollama as optional fallback.
8. Add mocked cloud-provider tests before real API testing.

## Required Environment Variables

Recommended cloud default:

```bash
QWEN_VL_PROVIDER=dashscope
QWEN_VL_MODEL=qwen3-vl-plus
QWEN_VL_API_KEY=your_api_key
QWEN_VL_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

SiliconFlow-compatible mode:

```bash
QWEN_VL_PROVIDER=siliconflow
QWEN_VL_MODEL=provider_model_name
QWEN_VL_API_KEY=your_api_key
QWEN_VL_BASE_URL=https://api.siliconflow.cn/v1
```

Local Ollama mode:

```bash
QWEN_VL_PROVIDER=ollama
QWEN_VL_MODEL=qwen3-vl:8b
QWEN_VL_BASE_URL=http://localhost:11434/v1
```

## Non-Negotiable Safety Rules

- Do not claim certified moisture measurement.
- Do not expose calibrated moisture percentage unless calibration evidence exists.
- Do not let the VLM overrule hard FAO/BIS safety gates.
- Downgrade or require review when hazard, high moisture, visible mould, stones, or high foreign matter appear.
- Keep raw uploads, proxy evidence, RAG chunks, model output, and final rule decision auditable.

