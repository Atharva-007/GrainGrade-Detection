# Graph Report - C:\Atharva\Millets\AI Grain Grade  (2026-06-04)

## Corpus Check
- 22 files · ~72,755 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 426 nodes · 1175 edges · 14 communities detected
- Extraction: 50% EXTRACTED · 50% INFERRED · 0% AMBIGUOUS · INFERRED: 586 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]

## God Nodes (most connected - your core abstractions)
1. `FeedbackCollector` - 101 edges
2. `VisionRAGPipeline` - 100 edges
3. `PhysicsProxiesExtractor` - 93 edges
4. `RAGEngine` - 68 edges
5. `QualityGrade` - 56 edges
6. `MoistureRisk` - 55 edges
7. `GradingFeedbackItem` - 52 edges
8. `RagiRuleEngine` - 49 edges
9. `MoistureCalibrator` - 47 edges
10. `GradingResult` - 36 edges

## Surprising Connections (you probably didn't know these)
- `PhysicsProxiesExtractor` --calls--> `extractor()`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\physics_proxies.py → C:\Atharva\Millets\AI Grain Grade\tests\test_suite.py
- `VisionRAGPipeline` --calls--> `pipeline()`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\vision_rag_pipeline.py → C:\Atharva\Millets\AI Grain Grade\tests\test_suite.py
- `retrieve_with_mode()` --calls--> `retrieve_rag_context()`  [INFERRED]
  C:\Users\athar\Downloads\Model Doc\legacy\model-doc-app\app\rag.py → C:\Users\athar\Downloads\Model Doc\legacy\model-doc-app\app\streamlit_grading_app.py
- `format_retrieved()` --calls--> `retrieve_rag_context()`  [INFERRED]
  C:\Users\athar\Downloads\Model Doc\legacy\model-doc-app\app\rag.py → C:\Users\athar\Downloads\Model Doc\legacy\model-doc-app\app\streamlit_grading_app.py
- `index_exists()` --calls--> `retrieve_rag_context()`  [INFERRED]
  C:\Users\athar\Downloads\Model Doc\legacy\model-doc-app\app\rag.py → C:\Users\athar\Downloads\Model Doc\legacy\model-doc-app\app\streamlit_grading_app.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (54): MoistureCalibrator, Handles the mapping from raw physics-based moisture score to      calibrated mo, Convert raw score (0-100) to calibrated moisture percentage., Returns True as this class provides a calibration mapping., _norm_path(), RAGEngine, RAG engine for ragi grading knowledge retrieval.  This version indexes the autho, Discover the canonical Markdown sources for retrieval. (+46 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (58): Enum, FeedbackCollector, flatten_feature_dict(), GradingFeedbackItem, Feedback storage utilities for cloud Qwen grading runs., Return whether enough corrections exist for an external review job., Single operator correction captured by the Streamlit workflow., Flatten nested numeric image feature dictionaries for similarity lookup. (+50 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (33): PhysicsProxiesExtractor, Measure the spacing between grid lines in pixels using a rectified sheet., Detect the neutral reference strip near the sheet edge., Detect the blue-bordered grain field that constrains the calibrated sample area., Fallback sample region from the detected grain spread when no printed box is fou, Convert mask areas into physical units when scale calibration is available., Summarize grain-level physical properties: size, shape, shine, and tone., Measure grain placement against the printed calibration-grid boxes.          For (+25 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (43): ensure_runtime_dirs(), Central project paths for runtime code and tests., Create writable runtime directories used by the app., _blend_masked_overlay(), _build_grain_detection_overlay(), _component_boxes_and_clump_mask(), _cuda_device_count(), _decision_state() (+35 more)

### Community 4 - "Community 4"
Cohesion: 0.1
Nodes (12): _FakeResponse, test_dashscope_provider_defaults_to_qwen3_vl_model(), test_dashscope_provider_uses_openai_compatible_vision_payload(), test_text_repair_uses_configured_cloud_provider(), _write_test_image(), Test that VisionRAGPipeline correctly uses the RAGEngine for context., test_pipeline_uses_rag_engine(), Test complete pipeline: image → proxies → RAG → result. (+4 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (32): index_exists(), _as_bool(), _as_float(), _as_list(), _grade_value(), RagiRuleThresholds, Deterministic FAO/BIS-aligned threshold rules for ragi grading.  The model can d, Conservative operator-assist thresholds from the RAG rule anchor. (+24 more)

### Community 6 - "Community 6"
Cohesion: 0.23
Nodes (14): Chunk, _embed_query(), format_retrieved(), _load_chunks(), _load_index(), _local_retrieval_docs(), Lightweight RAG over the ragi grading knowledge base.  Corpus (built by `build_r, Return top-k chunks plus the retrieval mode used. (+6 more)

### Community 7 - "Community 7"
Cohesion: 0.31
Nodes (10): chunk_markdown(), chunk_pdf(), create_genai_client(), embed_documents(), get_api_key(), main(), Build the RAG index for the ragi grading knowledge base.  Run this once (and any, Split a markdown file by H1/H2 sections, then by size cap. (+2 more)

### Community 8 - "Community 8"
Cohesion: 0.24
Nodes (9): _detect_required_aruco_markers(), flatten_perspective(), _get_aruco_detector(), process_image_batch(), Physics Proxies Extraction for Ragi Moisture & Quality Assessment =============, Rectify an A4 v3.2 calibration-sheet photo to a top-down view.      Expected she, Process multiple images and return proxy features for each.     Useful for batc, Build an ArUco detector across OpenCV API variants.      OpenCV 4.7+ exposes cv2 (+1 more)

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (1): Streamlit launcher for the packaged AI Grain Grade app.

### Community 10 - "Community 10"
Cohesion: 1.0
Nodes (1): AI Grain Grade package.

### Community 11 - "Community 11"
Cohesion: 1.0
Nodes (0):

### Community 12 - "Community 12"
Cohesion: 1.0
Nodes (0):

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (0):

## Knowledge Gaps
- **68 isolated node(s):** `Streamlit launcher for the packaged AI Grain Grade app.`, `Build the RAG index for the ragi grading knowledge base.  Run this once (and any`, `Split a markdown file by H1/H2 sections, then by size cap.`, `Lightweight RAG over the ragi grading knowledge base.  Corpus (built by `build_r`, `Return top-k chunks plus the retrieval mode used.` (+63 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 9`** (2 nodes): `Streamlit launcher for the packaged AI Grain Grade app.`, `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 10`** (2 nodes): `__init__.py`, `AI Grain Grade package.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 11`** (2 nodes): `index.ts`, `jsonResponse()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 12`** (1 nodes): `list_models.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (1 nodes): `run_app.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PhysicsProxiesExtractor` connect `Community 2` to `Community 8`, `Community 1`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.282) - this node is a cross-community bridge._
- **Why does `VisionRAGPipeline` connect `Community 4` to `Community 0`, `Community 1`, `Community 3`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Why does `FeedbackCollector` connect `Community 1` to `Community 0`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Are the 92 inferred relationships involving `FeedbackCollector` (e.g. with `Streamlit UI for Ragi Quality Grading System - "Millets Now" ==================` and `Initialize the physics extractor and configured cloud Qwen runtime.`) actually correct?**
  _`FeedbackCollector` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Are the 63 inferred relationships involving `VisionRAGPipeline` (e.g. with `Streamlit UI for Ragi Quality Grading System - "Millets Now" ==================` and `Initialize the physics extractor and configured cloud Qwen runtime.`) actually correct?**
  _`VisionRAGPipeline` has 63 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `PhysicsProxiesExtractor` (e.g. with `Streamlit UI for Ragi Quality Grading System - "Millets Now" ==================` and `Initialize the physics extractor and configured cloud Qwen runtime.`) actually correct?**
  _`PhysicsProxiesExtractor` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 46 inferred relationships involving `RAGEngine` (e.g. with `QualityGrade` and `MoistureRisk`) actually correct?**
  _`RAGEngine` has 46 INFERRED edges - model-reasoned connections that need verification._
