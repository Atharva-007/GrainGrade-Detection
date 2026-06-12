# AI Grain Moisture and Quality Detection

## Purpose

This repository defines a camera-assisted system for:

- moisture risk estimation
- grain quality grading
- broken grain detection
- foreign matter detection

The first production crop is:

- finger millet / ragi

This is not a certified moisture meter. It is a controlled optical estimation system that must be calibrated against measured moisture values.

---

## Current Reality

The folder `Grain moisture details chat chatgpt` was audited before writing this spec set.

Findings:

- it contains 101 files
- 100 are readable images
- 1 file is unreadable: `IMG_4611.PNG`
- most images are screenshots of a ChatGPT conversation
- they are not valid training or evaluation samples
- there are no measured moisture labels in that folder

This means the current image folder is useful for idea generation, but it is not a valid grain moisture dataset.

---

## What The System Should Output

- moisture risk: LOW / MODERATE / HIGH
- optional calibrated moisture percentage
- confidence score
- image quality status
- broken grain percentage
- foreign matter percentage
- quality grade
- retake or meter-confirmation recommendation

---

## Core Truth

RGB images do not directly measure internal moisture.

The camera only observes proxy signals such as:

- surface reflection
- color change
- texture
- clumping
- visible mold or spoilage

Therefore, this project must be built as:

- a validation-first pipeline
- a crop-specific model family
- a calibrated moisture-risk estimator

---

## Document Structure

- `00_system_philosophy.md`
- `02_capture_protocol.md`
- `03_image_validation.md`
- `04_preprocessing_and_normalization.md`
- `05_segmentation_pipeline.md`
- `06_feature_engineering.md`
- `07_model_architecture.md`
- `08_training_pipeline.md`
- `09_inference_pipeline.md`
- `10_confidence_system.md`
- `11_calibration_system.md`
- `12_quality_grading_system.md`
- `13_mobile_app_design.md`
- `14_backend_architecture.md`
- `15_dataset_collection.md`
- `16_failure_modes.md`
- `17_advanced_research.md`
- `18_limits_and_truth.md`
- `19_roadmap.md`
- `AI_GRAIN_MOISTURE_MASTER_SPEC.md`
- `CLAUDE.md`

Use the master spec as the complete source of truth and the split docs as implementation-focused reference files.

Key architecture docs:

- `01_full_system_architecture.md`
- `14_backend_architecture.md`
- `13_mobile_app_design.md`

---

## Build Order

1. Data collection and metadata schema
2. Capture validation
3. Calibration grid and reference patch detection
4. Preprocessing and normalization
5. Segmentation baseline
6. Physics feature extraction
7. Crop-specific ragi model
8. Calibration module
9. Evaluation pipeline
10. Mobile app and backend deployment

---

## Accuracy Claims Policy

Do not claim accuracy until validation exists.

Allowed now:

"Prototype design for AI-assisted grain moisture-risk and quality estimation. Accuracy pending validation against measured moisture labels."

Not allowed now:

- "80-92% accurate"
- "lab-grade moisture measurement"
- "BIS-certified moisture detector"
