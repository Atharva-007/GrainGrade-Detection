# Master Document: Finger Millet (Ragi) Grain Grading AI System

**Executive Summary:** This document suite defines a complete plan to build a mobile+cloud AI system for *finger millet* (ragi) grain grading.  We use Google’s Gemma 4 (vision+reasoning) as the AI model and Flutter for the front-end. The system will analyze grain images, detect impurities/defects, and output a grade/score according to food safety standards. The docs include product vision, AI specs, system design, data guidelines, and an execution roadmap, enabling an autonomous build via Claude CLI.

**Document Index:** Each Markdown file below addresses a key aspect of the project:

- **01_product_spec.md** – Product vision, users, features, requirements, compliance (e.g. FSSAI standards).
- **02_ai_model_spec.md** – AI model selection (Gemma 4 variants), prompt templates, chain-of-thought steps, JSON output schema.
- **03_system_architecture.md** – High-level components, deployment options (Vertex AI, Cloud Run, vLLM), and diagrams.
- **04_backend_design.md** – Backend (FastAPI) design: endpoints, services, sample code.
- **05_flutter_app.md** – Flutter app spec: UI screens, camera settings, UX flow, and API example.
- **06_dataset_guidelines.md** – Data collection & labeling: annotation schema (CVAT/COCO examples), dataset size, augmentation.
- **07_scoring_evaluation.md** – Scoring algorithm (weights/formulas), grade thresholds, and model evaluation plan.
- **08_security_compliance.md** – Licensing (Gemma 4 Apache 2.0), data privacy, and FSSAI/BIS compliance considerations.
- **09_infra_cicd.md** – Infrastructure and DevOps: CI/CD pipeline, monitoring, and rough cost estimates for cloud resources.
- **10_execution_plan.md** – Step-by-step development roadmap with milestones and deliverables.

**Sources & Assumptions:** We base the design on official sources where possible.  FSSAI’s cereal standards (millets) guide the quality limits【7†L733-L742】, NIFTEM and research literature inform grain properties【31†L25-L30】【32†L1-L4】, and the Gemma 4 documentation describes model capabilities and licensing【9†L439-L447】【41†L102-L111】. Where the handbook content is not explicit, we note assumptions (e.g. treating general millet standards as applying to ragi).

Each file is in Markdown, ready to feed into Claude CLI for an autonomous build.

---
