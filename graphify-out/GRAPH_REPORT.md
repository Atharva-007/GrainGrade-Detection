# Graph Report - C:\Atharva\Millets\AI Grain Grade  (2026-06-12)

## Corpus Check
- 45 files · ~96,169 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1019 nodes · 3194 edges · 77 communities detected
- Extraction: 31% EXTRACTED · 69% INFERRED · 0% AMBIGUOUS · INFERRED: 2209 edges (avg confidence: 0.54)
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
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]

## God Nodes (most connected - your core abstractions)
1. `FeedbackCollector` - 431 edges
2. `RAGEngine` - 335 edges
3. `MoistureCalibrator` - 314 edges
4. `CropRuleEngine` - 310 edges
5. `VisionRAGPipeline` - 194 edges
6. `PhysicsProxiesExtractor` - 140 edges
7. `GradingFeedbackItem` - 114 edges
8. `QualityGrade` - 111 edges
9. `MoistureRisk` - 110 edges
10. `GradingResult` - 71 edges

## Surprising Connections (you probably didn't know these)
- `runtime()` --calls--> `runtime_status()`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\backend\app\main.py → C:\Atharva\Millets\AI Grain Grade\backend\app\services.py
- `AnalysisRecord` --uses--> `FeedbackCollector`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\backend\app\services.py → C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\feedback.py
- `AnalysisRecord` --uses--> `CropRuleEngine`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\backend\app\services.py → C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\rule_engine.py
- `AppServices` --uses--> `FeedbackCollector`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\backend\app\services.py → C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\feedback.py
- `AppServices` --uses--> `GradingFeedbackItem`  [INFERRED]
  C:\Atharva\Millets\AI Grain Grade\backend\app\services.py → C:\Atharva\Millets\AI Grain Grade\src\ai_grain_grade\feedback.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (273): FeedbackCollector, JSON-backed correction storage used by the API and the Qwen prompt., MoistureCalibrator, Handles the mapping from raw physics-based moisture score to      calibrated mo, RAGEngine, CropRuleEngine, Crop-aware deterministic threshold router backed by crop rule YAML files., Pass 2: RAG-guided quality and moisture grading.         Retrieves relevant rul (+265 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (136): Enum, GradingFeedbackItem, Single operator correction captured by the Streamlit workflow., PhysicsProxiesExtractor, Fallback sample region from the detected grain spread when no printed box is fou, Convert mask areas into physical units when scale calibration is available., Summarize grain-level physical properties: size, shape, shine, and tone., Measure grain placement against the printed calibration-grid boxes.          For (+128 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (55): build_entries(), build_manifest(), emit_training_artifacts(), label_from_path(), main(), ManifestEntry, normalize_crop_name(), parse_args() (+47 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (36): analyzeImage(), fetchCrops(), fetchHealth(), fetchRuntime(), parseJson(), submitFeedback(), _now(), _number() (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (47): _as_bool(), _as_float(), _as_list(), _build_rule_set_from_yaml(), _clamp_score_to_grade(), _clip_score(), CropMetricRule, CropRuleSet (+39 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (37): Chunk, _embed_query(), format_retrieved(), index_exists(), _load_chunks(), _load_index(), _local_retrieval_docs(), Lightweight RAG over the ragi grading knowledge base.  Corpus (built by `build_r (+29 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (24): Append a fine-tune-ready correction record as JSONL., Return whether enough corrections exist for an external review job., runtime(), ensure_runtime_dirs(), Central project paths for runtime code and tests., Create writable runtime directories used by the app., AppServices, _coerce_float() (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (40): RagiRuleEngine, Applies hard ragi thresholds after VLM interpretation., Vision-RAG Pipeline for Ragi Quality Grading ==================================, Compute overall confidence (0-100) from model, image, and evidence consistency., Fallback grading when LLM inference fails., Produce a short operator-facing summary of the strongest signals., Build non-generic reasons for deterministic proxy-only holds., Compute a more meaningful quality score for proxy-only decisions. (+32 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (10): _norm_path(), RAG engine for ragi grading knowledge retrieval.  This version indexes the autho, Chunk and index the knowledge-base Markdown corpus., Retrieve top-k chunks using lexical scoring., Retrieve top-k chunks using weighted lexical scoring with source priors., Load an existing chunk index from disk., Persist the current chunk list to disk., Tests for RAG Engine and its Integration with VisionRAGPipeline. (+2 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (13): Measure the spacing between grid lines in pixels using a rectified sheet., Detect the neutral reference strip near the sheet edge., Detect the blue-bordered grain field that constrains the calibrated sample area., Return points ordered as top-left, top-right, bottom-right, bottom-left., Estimate a scale calibration from the printed grid sheet.          The extractor, Sheet 1 prints a 100 mm x 100 mm blue active grain zone.         When visible, t, Detect the printed blue active-zone rectangle on Sheet 1, or the large         b, Locate Sheet 2's white grid inside the blue field. (+5 more)

### Community 10 - "Community 10"
Cohesion: 0.21
Nodes (17): BaseModel, AnalysisCreateRequest, AnalysisCreateResponse, AnalysisJobResponse, AnalysisSubmitRequest, AnalysisSubmitResponse, AnalyzeResponse, ApiError (+9 more)

### Community 11 - "Community 11"
Cohesion: 0.19
Nodes (5): flatten_feature_dict(), Feedback storage utilities for cloud Qwen grading runs., Flatten nested numeric image feature dictionaries for similarity lookup., feedback(), test_feedback_similarity_filters_by_crop()

### Community 12 - "Community 12"
Cohesion: 0.31
Nodes (10): chunk_markdown(), chunk_pdf(), create_genai_client(), embed_documents(), get_api_key(), main(), Build the RAG index for the ragi grading knowledge base.  Run this once (and any, Split a markdown file by H1/H2 sections, then by size cap. (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.24
Nodes (9): _detect_required_aruco_markers(), flatten_perspective(), _get_aruco_detector(), process_image_batch(), Physics Proxies Extraction for Ragi Moisture & Quality Assessment =============, Rectify an A4 v3.2 calibration-sheet photo to a top-down view.      Expected she, Process multiple images and return proxy features for each.     Useful for batc, Build an ArUco detector across OpenCV API variants.      OpenCV 4.7+ exposes cv2 (+1 more)

### Community 14 - "Community 14"
Cohesion: 0.4
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 0.4
Nodes (2): Convert raw score (0-100) to calibrated moisture percentage., Returns True as this class provides a calibration mapping.

### Community 16 - "Community 16"
Cohesion: 0.5
Nodes (1): AI Grain Grade package.

### Community 17 - "Community 17"
Cohesion: 0.5
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (1): Streamlit launcher for the packaged AI Grain Grade app.

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Format retrieved chunks for prompt use.          When reverse=True, the most r

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): Applies hard ragi thresholds after VLM interpretation.

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): Normalize crop labels used by UI, datasets, and rule files.

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): One typed metric from a crop grading YAML file.

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Typed crop rule set loaded from docs/rag/crop_knowledge/grading_rules.

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (1): Parse the repository's compact YAML rule files without adding PyYAML.

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Crop-aware deterministic threshold router backed by crop rule YAML files.

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): Return A/B/C maximum moisture thresholds for the selected crop.

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (1): Normalize crop labels used by UI, datasets, and rule files.

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (1): One typed metric from a crop grading YAML file.

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (1): Typed crop rule set loaded from docs/rag/crop_knowledge/grading_rules.

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (1): Parse the repository's compact YAML rule files without adding PyYAML.

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (1): Crop-aware deterministic threshold router backed by crop rule YAML files.

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (1): Return A/B/C maximum moisture thresholds for the selected crop.

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (1): Flatten nested numeric image feature dictionaries for similarity lookup.

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): JSON-backed correction storage used by the API and the Qwen prompt.

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): Return whether enough corrections exist for an external review job.

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): Create writable runtime directories used by the app.

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): Applies hard ragi thresholds after VLM interpretation.

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): Normalize crop labels used by UI, datasets, and rule files.

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): One typed metric from a crop grading YAML file.

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): Typed crop rule set loaded from docs/rag/crop_knowledge/grading_rules.

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): Parse the repository's compact YAML rule files without adding PyYAML.

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): Crop-aware deterministic threshold router backed by crop rule YAML files.

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (1): Return A/B/C maximum moisture thresholds for the selected crop.

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (1): Flatten nested numeric image feature dictionaries for similarity lookup.

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): JSON-backed correction storage used by Streamlit and the Qwen prompt.

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): Return whether enough corrections exist for an external review job.

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Return whether enough corrections exist for an external review job.

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Parse the repository's compact YAML rule files without adding PyYAML.

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): Crop-aware deterministic threshold router backed by crop rule YAML files.

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): Single operator correction captured by the Streamlit workflow.

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): Flatten nested numeric image feature dictionaries for similarity lookup.

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (1): JSON-backed correction storage used by Streamlit and the Qwen prompt.

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): Return whether enough corrections exist for an external review job.

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): Create writable runtime directories used by the app.

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): Load an existing chunk index from disk.

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): Persist the current chunk list to disk.

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): Detect whether the on-disk index predates the current chunk schema.

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): Discover the canonical Markdown sources for retrieval.

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (1): Chunk and index the knowledge-base Markdown corpus.

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): Retrieve top-k chunks using lexical scoring.

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (1): Retrieve top-k chunks using weighted lexical scoring with source priors.

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (1): Format retrieved chunks for prompt use.          When reverse=True, the most rel

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (1): Conservative operator-assist thresholds from the RAG rule anchor.

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (1): Applies hard ragi thresholds after VLM interpretation.

## Knowledge Gaps
- **127 isolated node(s):** `Streamlit launcher for the packaged AI Grain Grade app.`, `Small Supabase REST/Storage client using the existing httpx dependency.`, `Build the RAG index for the ragi grading knowledge base.  Run this once (and any`, `Split a markdown file by H1/H2 sections, then by size cap.`, `Lightweight RAG over the ragi grading knowledge base.  Corpus (built by `build_r` (+122 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (2 nodes): `Streamlit launcher for the packaged AI Grain Grade app.`, `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (2 nodes): `App()`, `App.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `StatusPill.tsx`, `StatusPill()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `UploadPanel.tsx`, `UploadPanel()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `.format_context()`, `Format retrieved chunks for prompt use.          When reverse=True, the most r`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `index.ts`, `jsonResponse()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `vite.config.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `main.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `types.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `vite-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `list_models.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `run_app.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `Applies hard ragi thresholds after VLM interpretation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `Normalize crop labels used by UI, datasets, and rule files.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `One typed metric from a crop grading YAML file.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Typed crop rule set loaded from docs/rag/crop_knowledge/grading_rules.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `Parse the repository's compact YAML rule files without adding PyYAML.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Crop-aware deterministic threshold router backed by crop rule YAML files.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `Return A/B/C maximum moisture thresholds for the selected crop.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `Normalize crop labels used by UI, datasets, and rule files.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `One typed metric from a crop grading YAML file.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `Typed crop rule set loaded from docs/rag/crop_knowledge/grading_rules.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `Parse the repository's compact YAML rule files without adding PyYAML.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `Crop-aware deterministic threshold router backed by crop rule YAML files.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `Return A/B/C maximum moisture thresholds for the selected crop.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `Flatten nested numeric image feature dictionaries for similarity lookup.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `JSON-backed correction storage used by the API and the Qwen prompt.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `Return whether enough corrections exist for an external review job.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `Create writable runtime directories used by the app.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `Applies hard ragi thresholds after VLM interpretation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `Normalize crop labels used by UI, datasets, and rule files.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `One typed metric from a crop grading YAML file.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `Typed crop rule set loaded from docs/rag/crop_knowledge/grading_rules.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `Parse the repository's compact YAML rule files without adding PyYAML.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Crop-aware deterministic threshold router backed by crop rule YAML files.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `Return A/B/C maximum moisture thresholds for the selected crop.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `Flatten nested numeric image feature dictionaries for similarity lookup.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `JSON-backed correction storage used by Streamlit and the Qwen prompt.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `Return whether enough corrections exist for an external review job.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Return whether enough corrections exist for an external review job.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Parse the repository's compact YAML rule files without adding PyYAML.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `Crop-aware deterministic threshold router backed by crop rule YAML files.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `Single operator correction captured by the Streamlit workflow.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `Flatten nested numeric image feature dictionaries for similarity lookup.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `JSON-backed correction storage used by Streamlit and the Qwen prompt.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `Return whether enough corrections exist for an external review job.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `Create writable runtime directories used by the app.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `Load an existing chunk index from disk.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `Persist the current chunk list to disk.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `Detect whether the on-disk index predates the current chunk schema.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `Discover the canonical Markdown sources for retrieval.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `Chunk and index the knowledge-base Markdown corpus.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `Retrieve top-k chunks using lexical scoring.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `Retrieve top-k chunks using weighted lexical scoring with source priors.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `Format retrieved chunks for prompt use.          When reverse=True, the most rel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `Conservative operator-assist thresholds from the RAG rule anchor.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `Applies hard ragi thresholds after VLM interpretation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FeedbackCollector` connect `Community 0` to `Community 1`, `Community 2`, `Community 6`, `Community 7`, `Community 11`?**
  _High betweenness centrality (0.239) - this node is a cross-community bridge._
- **Why does `VisionRAGPipeline` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 15`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Why does `CropRuleEngine` connect `Community 0` to `Community 1`, `Community 2`, `Community 4`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Are the 420 inferred relationships involving `FeedbackCollector` (e.g. with `AnalysisRecord` and `AppServices`) actually correct?**
  _`FeedbackCollector` has 420 INFERRED edges - model-reasoned connections that need verification._
- **Are the 313 inferred relationships involving `RAGEngine` (e.g. with `QualityGrade` and `MoistureRisk`) actually correct?**
  _`RAGEngine` has 313 INFERRED edges - model-reasoned connections that need verification._
- **Are the 309 inferred relationships involving `MoistureCalibrator` (e.g. with `QualityGrade` and `MoistureRisk`) actually correct?**
  _`MoistureCalibrator` has 309 INFERRED edges - model-reasoned connections that need verification._
- **Are the 298 inferred relationships involving `CropRuleEngine` (e.g. with `AnalysisRecord` and `AppServices`) actually correct?**
  _`CropRuleEngine` has 298 INFERRED edges - model-reasoned connections that need verification._