# Backend Architecture

## Purpose

Provide the storage, processing, inference, audit, and feedback backbone for the grain moisture-risk and quality system.

The backend must support:

- immutable raw sample storage
- deterministic preprocessing
- model inference
- crop-specific calibration
- full auditability
- feedback-driven improvement

---

## 1. Core Services

### Ingestion Service

Responsibilities:

- receive sample metadata
- register sample and image IDs
- validate file integrity
- push raw files to storage

### Validation Service

Responsibilities:

- run server-side quality validation
- confirm that the input is not a screenshot or unsupported content
- store validation results

### Preprocessing Worker

Responsibilities:

- detect grid and reference patch
- correct geometry
- normalize exposure and color
- align flash/no-flash pairs
- write processed artifacts

### Inference Service

Responsibilities:

- load active crop-specific model
- combine image and feature inputs
- produce raw outputs

### Calibration Service

Responsibilities:

- apply crop-specific calibration
- apply threshold mapping
- attach calibration version

### Reporting Service

Responsibilities:

- generate user-facing response
- store prediction report
- include confidence and action guidance

### Feedback Service

Responsibilities:

- store meter-confirmation values
- store human review
- trigger relabel or audit workflows

---

## 2. Core Data Entities

- users
- farms
- devices
- samples
- sample_images
- sample_metadata
- validation_reports
- preprocessing_artifacts
- feature_vectors
- moisture_measurements
- predictions
- quality_reports
- calibration_versions
- model_versions
- feedback_events
- audit_logs

---

## 3. Storage Strategy

### Raw Store

Contains:

- original uploaded images
- original metadata payload

Rules:

- immutable
- versioned by upload timestamp
- never overwritten

### Processed Store

Contains:

- normalized images
- segmentation masks
- feature files
- pair delta maps

### Structured Data Store

Contains:

- sample records
- predictions
- confidence values
- meter-confirmed labels
- feedback history

---

## 4. API Surface

Suggested endpoints:

```text
POST /samples
POST /samples/{id}/images
POST /samples/{id}/metadata
POST /samples/{id}/measurements
POST /predict/moisture-risk
GET  /samples/{id}/report
POST /feedback/meter-confirmation
POST /feedback/human-review
GET  /models/active
GET  /calibration/active
GET  /metrics/validation
```

Every prediction response must include:

- model version
- calibration version
- confidence
- reject or warning reasons

---

## 5. Processing Modes

### Cloud-First Mode

- on-device validation
- upload raw sample
- cloud preprocessing
- cloud inference
- cloud calibration

### Hybrid Mode

- on-device validation
- optional on-device preprocessing preview
- cloud inference

### Offline-Limited Mode

- on-device validation
- lightweight fallback model
- sync raw data later

Recommended initial mode:

- on-device validation + cloud inference

---

## 6. Audit Requirements

For every prediction, store:

- sample ID
- crop
- model version
- calibration version
- input metadata snapshot
- prediction output
- confidence score
- rejection reasons if any
- preprocessing version

This is required for:

- debugging
- relabeling
- metric reporting
- calibration updates

---

## 7. Backend Safety Rules

- do not overwrite raw files
- do not accept screenshot content as dataset sample
- do not train on weak labels without marking label quality
- do not expose calibrated moisture percentage if calibration is absent
- always preserve prediction lineage

