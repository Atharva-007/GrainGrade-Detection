# AI Grain Grade

AI Grain Grade is a Streamlit application for finger millet (ragi) quality grading. It combines image-derived physics proxies, a rule engine, lexical RAG over grading documents, and a cloud OpenAI-compatible Qwen3-VL endpoint.

## What This Project Does

- Accepts a grain image through the Streamlit UI.
- Extracts deterministic image signals with OpenCV.
- Retrieves authoritative grading and moisture rules from local Markdown indexes.
- Calls the configured cloud Qwen3-VL provider for vision inference.
- Applies deterministic safety and grading rules before showing the final result.
- Stores human corrections as feedback examples for reuse and audit review.

## Quick Start

1. Create and activate your Python environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a local `.env` from the template:

```powershell
Copy-Item .env.example .env
```

4. Fill in `QWEN_VL_API_KEY` in `.env`.
5. Run the app:

```powershell
python -m streamlit run app.py --server.port 8501
```

The local app URL is usually `http://localhost:8501`.

## Docker Deployment

Build the image:

```powershell
docker build -t ai-grain-grade:local .
```

Run it with your local environment file:

```powershell
docker run --rm --env-file .env -p 8501:8501 ai-grain-grade:local
```

For compose-based validation:

```powershell
docker compose up --build
```

The container serves Streamlit on `http://localhost:8501`. The Streamlit health endpoint is `http://localhost:8501/_stcore/health`.

Cloud Qwen inference is configured through runtime environment variables:

- `QWEN_VL_PROVIDER` - required provider, usually `dashscope` for the default cloud path.
- `QWEN_VL_API_KEY` - required API key for the configured provider.
- `QWEN_VL_BASE_URL` - optional OpenAI-compatible base URL override.
- `QWEN_VL_MODEL` - optional model override.
- `QWEN_VL_TIMEOUT_SECONDS` - optional request timeout override.

The Docker image includes the app code, `docs/rag/`, `data/rag/rag_index.json`, examples, and Streamlit config. It does not copy `.env`, local feedback/uploads, model-weight directories, embedding caches, or graph caches into the image. Feedback records and uploaded session images are written under `data/feedback/feedback_data`; in compose this path is backed by the `feedback_data` Docker volume.

## Main Entry Points

- `app.py` - tiny Streamlit launcher.
- `src/ai_grain_grade/streamlit_app.py` - Streamlit user interface and workflow orchestration.
- `src/ai_grain_grade/vision_rag_pipeline.py` - cloud Qwen3-VL calls, safety gate, RAG-guided grading, fallback logic.
- `src/ai_grain_grade/physics_proxies.py` - OpenCV feature extraction from grain images.
- `src/ai_grain_grade/rule_engine.py` - deterministic ragi grading thresholds.
- `src/ai_grain_grade/rag_engine.py` - Markdown chunking and lexical retrieval.
- `src/ai_grain_grade/feedback.py` - JSON feedback storage and similar-correction retrieval.

## Directory Map

```text
.
|-- app.py                         # Streamlit app entrypoint
|-- Dockerfile                     # Container image for Streamlit deployment
|-- docker-compose.yml             # Local container validation
|-- .dockerignore                  # Container build exclusions
|-- src/ai_grain_grade/            # Core Python package
|-- tests/                         # Python tests
|-- requirements.txt               # Python dependencies
|-- README.md                      # Project onboarding
|-- .env.example                   # Local environment template
|-- data/rag/                      # Local RAG indexes
|-- data/feedback/                 # Example and runtime feedback records
|-- docs/rag/                      # Runtime RAG source documents
|-- docs/                          # Product, model, architecture, and prompt docs
|-- examples/                      # Example calibration images
|-- graphify-out/                  # Code knowledge graph outputs
|-- legacy/                        # Older standalone model-doc Streamlit app
|-- scripts/                       # Local helper scripts
|-- supabase/                      # Supabase migrations and edge functions
```

## Runtime Configuration

The active app reads these Qwen variables:

- `QWEN_VL_PROVIDER` - `dashscope`, `siliconflow`, or `custom`.
- `QWEN_VL_API_KEY` - preferred API key variable.
- `DASHSCOPE_API_KEY` - DashScope fallback alias.
- `QWEN_VL_BASE_URL` - optional OpenAI-compatible base URL override.
- `QWEN_VL_MODEL` - optional model override.
- `QWEN_VL_TIMEOUT_SECONDS` - optional cloud request timeout.

Secrets belong in `.env`; `.env` and `*.env` are ignored by git.

## RAG Knowledge Sources

The local RAG index intentionally reads these Markdown files from `docs/rag/`:

- `docs/rag/FAO_BIS_RAGI_RULES.md`
- `docs/rag/AUTHORIZED_RAGI_DATA_SOURCES.md`
- `docs/rag/ARCHITECTURE.md`
- `docs/rag/UNIFIED_RAGI_QUALITY_AND_MOISTURE_SPEC.md`

The chunk index lives at `data/rag/rag_index.json`.

## Tests

Run the focused unit and integration tests with:

```powershell
python -m pytest
```

Some tests use local lexical indexes and deterministic fallbacks. Cloud provider tests mock HTTP calls and do not require a real API key.

## Generated Files

The app and tools can generate logs, caches, uploaded samples, graph caches, and temporary Streamlit files. These are ignored by git. If the root gets noisy during development, it is safe to remove ignored `*.log`, `__pycache__/`, `.pytest_cache/`, and temporary Streamlit output files.

## Project Notes

- `docs/archive/grain-grade-md-files/` preserves imported planning material and duplicate document exports.
- `legacy/model-doc-app/` is an older standalone Gemini/RAG app kept for reference.
- `graphify-out/GRAPH_REPORT.md` is useful for architecture navigation; the central nodes are `FeedbackCollector`, `PhysicsProxiesExtractor`, `RAGEngine`, and `VisionRAGPipeline`.
