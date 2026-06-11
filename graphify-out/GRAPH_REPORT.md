# Graph Report - C:\Atharva\Millets\AI Grain Grade  (2026-06-11)

## Corpus Check
- 25 files · ~89,100 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 644 nodes · 2006 edges · 36 communities detected
- Extraction: 38% EXTRACTED · 62% INFERRED · 0% AMBIGUOUS · INFERRED: 1237 edges (avg confidence: 0.54)
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
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]

## God Nodes (most connected - your core abstractions)
1. `FeedbackCollector` - 221 edges
2. `VisionRAGPipeline` - 169 edges
3. `RAGEngine` - 137 edges
4. `PhysicsProxiesExtractor` - 134 edges
5. `MoistureCalibrator` - 116 edges
6. `QualityGrade` - 106 edges
7. `MoistureRisk` - 105 edges
8. `GradingFeedbackItem` - 102 edges
9. `CropRuleEngine` - 88 edges
10. `GradingResult` - 66 edges

## Surprising Connections (you probably didn't know these)
- `index_exists()` --calls--> `retrieve_rag_context()`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\legacy\model-doc-app\app\rag.py → C:\Atharva\Millets\AI Grain Grade\legacy\model-doc-app\app\streamlit_grading_app.py
- `test_calibration()` --calls--> `PhysicsProxiesExtractor`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\scripts\verify_calibration.py → C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\physics_proxies.py
- `test_calibration()` --calls--> `VisionRAGPipeline`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\scripts\verify_calibration.py → C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\vision_rag_pipeline.py
- `GradingFeedbackItem` --uses--> `TestPhysicsProxies`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\feedback.py → C:\Atharva\Millets\AI Grain Grade\tests\test_suite.py
- `GradingFeedbackItem` --calls--> `test_feedback_similarity_filters_by_crop()`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\feedback.py → C:\Atharva\Millets\AI Grain Grade\tests\test_crop_pipeline_and_manifest.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (117): FeedbackCollector, JSON-backed correction storage used by Streamlit and the Qwen prompt., MoistureCalibrator, Handles the mapping from raw physics-based moisture score to      calibrated mo, RAGEngine, Retrieve top-k chunks using weighted lexical scoring with source priors., Format retrieved chunks for prompt use.          When reverse=True, the most r, CropRuleEngine (+109 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (109): Enum, GradingFeedbackItem, Single operator correction captured by the Streamlit workflow., PhysicsProxiesExtractor, Lightweight OpenCV-based feature extraction for ragi grain analysis.     Design, Args:             grain_mask_threshold: Binary threshold for grain region detec, init_local_stack(), Streamlit UI for Ragi Quality Grading System - "Millets Now" ================== (+101 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (20): Retrieve top-k chunks using lexical scoring., str, _fake_physics_proxies(), test_call_qwen_vision_crop_route_success_is_not_fallback(), test_call_qwen_vision_routes_with_crop_fallback_metadata(), test_crop_prompt_includes_crop_context_in_rag_prompt(), test_fallback_grading_uses_crop_yaml_rule_path(), test_infer_carries_crop_metadata_into_result() (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (36): Convert raw score (0-100) to calibrated moisture percentage., Returns True as this class provides a calibration mapping., _blend_masked_overlay(), _build_auto_batch_metadata(), _build_grain_detection_overlay(), _component_boxes_and_clump_mask(), _confidence_tier(), _cuda_device_count() (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (19): Fallback sample region from the detected grain spread when no printed box is fou, Convert mask areas into physical units when scale calibration is available., Summarize grain-level physical properties: size, shape, shine, and tone., Measure grain placement against the printed calibration-grid boxes.          For, Conservative grain region segmentation using color-based thresholding.         R, Compute Shannon entropy of surface texture (Laplacian magnitude)., Extract CIE-LAB color features to detect moisture absorption.                  M, Connected-components analysis to detect capillary clumping.                  W (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (37): Chunk, _embed_query(), format_retrieved(), index_exists(), _load_chunks(), _load_index(), _local_retrieval_docs(), Lightweight RAG over the ragi grading knowledge base.  Corpus (built by `build_r (+29 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (24): _as_bool(), _as_float(), _as_list(), _build_rule_set_from_yaml(), CropMetricRule, CropRuleSet, _extract_rule_blocks(), _extract_score_blocks() (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (14): Feedback storage utilities for cloud Qwen grading runs., Moisture Calibration for Ragi Grain Analysis ==================================, ensure_runtime_dirs(), Central project paths for runtime code and tests., Create writable runtime directories used by the app., _norm_path(), RAG engine for ragi grading knowledge retrieval.  This version indexes the autho, Discover the canonical Markdown sources for retrieval. (+6 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (13): Measure the spacing between grid lines in pixels using a rectified sheet., Detect the neutral reference strip near the sheet edge., Detect the blue-bordered grain field that constrains the calibrated sample area., Return points ordered as top-left, top-right, bottom-right, bottom-left., Estimate a scale calibration from the printed grid sheet.          The extractor, Sheet 1 prints a 100 mm x 100 mm blue active grain zone.         When visible, t, Detect the printed blue active-zone rectangle on Sheet 1, or the large         b, Locate Sheet 2's white grid inside the blue field. (+5 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (27): build_entries(), build_manifest(), emit_training_artifacts(), label_from_path(), main(), ManifestEntry, normalize_crop_name(), parse_args() (+19 more)

### Community 10 - "Community 10"
Cohesion: 0.19
Nodes (4): flatten_feature_dict(), Return whether enough corrections exist for an external review job., Flatten nested numeric image feature dictionaries for similarity lookup., test_feedback_similarity_filters_by_crop()

### Community 11 - "Community 11"
Cohesion: 0.31
Nodes (10): chunk_markdown(), chunk_pdf(), create_genai_client(), embed_documents(), get_api_key(), main(), Build the RAG index for the ragi grading knowledge base.  Run this once (and any, Split a markdown file by H1/H2 sections, then by size cap. (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.24
Nodes (9): _detect_required_aruco_markers(), flatten_perspective(), _get_aruco_detector(), process_image_batch(), Physics Proxies Extraction for Ragi Moisture & Quality Assessment =============, Rectify an A4 v3.2 calibration-sheet photo to a top-down view.      Expected she, Process multiple images and return proxy features for each.     Useful for batc, Build an ArUco detector across OpenCV API variants.      OpenCV 4.7+ exposes cv2 (+1 more)

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (1): Streamlit launcher for the packaged AI Grain Grade app.

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (1): AI Grain Grade package.

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (1): Return whether enough corrections exist for an external review job.

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): Parse the repository's compact YAML rule files without adding PyYAML.

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (1): Crop-aware deterministic threshold router backed by crop rule YAML files.

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (1): Single operator correction captured by the Streamlit workflow.

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Flatten nested numeric image feature dictionaries for similarity lookup.

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): JSON-backed correction storage used by Streamlit and the Qwen prompt.

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (1): Return whether enough corrections exist for an external review job.

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Create writable runtime directories used by the app.

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Load an existing chunk index from disk.

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Persist the current chunk list to disk.

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Detect whether the on-disk index predates the current chunk schema.

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Discover the canonical Markdown sources for retrieval.

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Chunk and index the knowledge-base Markdown corpus.

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Retrieve top-k chunks using lexical scoring.

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): Retrieve top-k chunks using weighted lexical scoring with source priors.

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): Format retrieved chunks for prompt use.          When reverse=True, the most rel

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Conservative operator-assist thresholds from the RAG rule anchor.

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Applies hard ragi thresholds after VLM interpretation.

## Knowledge Gaps
- **96 isolated node(s):** `Streamlit launcher for the packaged AI Grain Grade app.`, `Build the RAG index for the ragi grading knowledge base.  Run this once (and any`, `Split a markdown file by H1/H2 sections, then by size cap.`, `Lightweight RAG over the ragi grading knowledge base.  Corpus (built by `build_r`, `Return top-k chunks plus the retrieval mode used.` (+91 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 13`** (2 nodes): `Streamlit launcher for the packaged AI Grain Grade app.`, `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (2 nodes): `__init__.py`, `AI Grain Grade package.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (2 nodes): `index.ts`, `jsonResponse()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `list_models.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `run_app.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `Return whether enough corrections exist for an external review job.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `Parse the repository's compact YAML rule files without adding PyYAML.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `Crop-aware deterministic threshold router backed by crop rule YAML files.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `Single operator correction captured by the Streamlit workflow.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `Flatten nested numeric image feature dictionaries for similarity lookup.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `JSON-backed correction storage used by Streamlit and the Qwen prompt.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `Return whether enough corrections exist for an external review job.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `Create writable runtime directories used by the app.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Load an existing chunk index from disk.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `Persist the current chunk list to disk.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Detect whether the on-disk index predates the current chunk schema.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `Discover the canonical Markdown sources for retrieval.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `Chunk and index the knowledge-base Markdown corpus.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Retrieve top-k chunks using lexical scoring.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `Retrieve top-k chunks using weighted lexical scoring with source priors.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `Format retrieved chunks for prompt use.          When reverse=True, the most rel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `Conservative operator-assist thresholds from the RAG rule anchor.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Applies hard ragi thresholds after VLM interpretation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FeedbackCollector` connect `Community 0` to `Community 1`, `Community 3`, `Community 4`, `Community 7`, `Community 10`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Why does `PhysicsProxiesExtractor` connect `Community 1` to `Community 8`, `Community 12`, `Community 4`?**
  _High betweenness centrality (0.195) - this node is a cross-community bridge._
- **Why does `VisionRAGPipeline` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 10`?**
  _High betweenness centrality (0.179) - this node is a cross-community bridge._
- **Are the 211 inferred relationships involving `FeedbackCollector` (e.g. with `Streamlit UI for Ragi Quality Grading System - "Millets Now" ==================` and `Initialize the physics extractor and configured cloud Qwen runtime.`) actually correct?**
  _`FeedbackCollector` has 211 INFERRED edges - model-reasoned connections that need verification._
- **Are the 120 inferred relationships involving `VisionRAGPipeline` (e.g. with `Streamlit UI for Ragi Quality Grading System - "Millets Now" ==================` and `Initialize the physics extractor and configured cloud Qwen runtime.`) actually correct?**
  _`VisionRAGPipeline` has 120 INFERRED edges - model-reasoned connections that need verification._
- **Are the 115 inferred relationships involving `RAGEngine` (e.g. with `QualityGrade` and `MoistureRisk`) actually correct?**
  _`RAGEngine` has 115 INFERRED edges - model-reasoned connections that need verification._
- **Are the 95 inferred relationships involving `PhysicsProxiesExtractor` (e.g. with `Streamlit UI for Ragi Quality Grading System - "Millets Now" ==================` and `Initialize the physics extractor and configured cloud Qwen runtime.`) actually correct?**
  _`PhysicsProxiesExtractor` has 95 INFERRED edges - model-reasoned connections that need verification._