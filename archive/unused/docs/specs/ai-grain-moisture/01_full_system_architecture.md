# Full System Architecture

## Purpose

Define the complete technical architecture for a camera-assisted grain moisture-risk and quality-grading platform, starting with finger millet / ragi.

This file is the main system-design view for implementers. It connects capture, preprocessing, modeling, calibration, confidence, API, storage, analytics, and deployment.

---

## 1. System Boundary

The system includes:

- mobile capture workflow
- image validation pipeline
- preprocessing and normalization
- segmentation and feature extraction
- crop-specific model inference
- calibration layer
- confidence and decision logic
- backend storage and audit trail
- operator feedback and meter-confirmation loop

The system does not include:

- laboratory moisture measurement
- certification authority workflow
- regulatory grading approval

---

## 2. End-to-End Flow

```text
Farmer / Operator
  |
  v
Mobile App
  |
  |-- crop selection
  |-- capture guidance
  |-- 6-image capture
  |-- camera locks
  |-- metadata capture
  |-- on-device validation
  |
  v
Sample Package
  |
  |-- raw images
  |-- metadata
  |-- validation report
  |
  v
Backend Ingestion
  |
  |-- file integrity checks
  |-- storage of raw assets
  |-- preprocessing pipeline
  |-- segmentation
  |-- feature extraction
  |-- model inference
  |-- calibration
  |-- confidence logic
  |
  v
Prediction Report
  |
  |-- moisture risk
  |-- optional moisture estimate
  |-- quality grade
  |-- defect percentages
  |-- confidence
  |-- retake / confirm recommendation
  |
  v
Feedback Loop
  |
  |-- meter confirmation
  |-- human review
  |-- relabeling
  |-- calibration update
```

---

## 3. Layered Architecture

### 3.1 Capture Layer

Responsibilities:

- enforce correct sample capture
- collect 6 images
- lock exposure, focus, white balance, zoom
- ensure grid and reference patch presence
- capture metadata
- block screenshots and invalid uploads

Inputs:

- selected crop
- camera feed
- optional environment sensor data

Outputs:

- raw sample image set
- capture metadata
- preliminary validation scores

---

### 3.2 Validation Layer

Responsibilities:

- reject unreadable or corrupt files
- detect screenshot/UI content
- verify image quality
- verify capture compliance
- verify flash/no-flash pair alignment

Outputs:

- valid / invalid decision
- quality score vector
- reject reasons

---

### 3.3 Preprocessing Layer

Responsibilities:

- detect calibration grid
- detect white/gray reference patch
- correct geometry and perspective
- normalize color and exposure
- align flash/no-flash pairs
- generate normalized model inputs

Outputs:

- normalized image set
- pair delta maps
- preprocessing audit metadata

---

### 3.4 Segmentation Layer

Responsibilities:

- separate grain from background
- estimate overlap
- detect broken grain regions
- detect foreign matter
- detect dust/fines

Outputs:

- grain masks
- defect masks
- overlap score
- segmentation confidence

---

### 3.5 Feature Layer

Responsibilities:

- compute handcrafted optical proxy features
- compute density, clumping, and texture summaries
- compute flash/no-flash response features
- compute defect and quality metrics

Outputs:

- feature vector
- image statistics
- quality statistics

---

### 3.6 Model Layer

Responsibilities:

- encode image set
- combine image and feature branches
- generate moisture-risk and quality outputs
- estimate uncertainty

Outputs:

- raw moisture score
- moisture risk logits
- quality outputs
- uncertainty outputs

---

### 3.7 Calibration Layer

Responsibilities:

- map raw outputs to crop-specific calibrated ranges
- apply device/crop/environment corrections when allowed
- ensure risk thresholds are crop-specific

Outputs:

- calibrated moisture estimate
- calibrated moisture-risk class
- calibration confidence
- calibration version

---

### 3.8 Decision Layer

Responsibilities:

- combine confidence signals
- choose whether to accept, warn, retake, or reject
- minimize false-safe decisions

Outputs:

- final report
- confidence score
- recommended action

---

### 3.9 Storage and Analytics Layer

Responsibilities:

- store raw assets immutably
- store processed artifacts separately
- store predictions and calibration versions
- store meter-confirmation feedback
- enable analytics and retraining

Outputs:

- dataset tables
- audit logs
- experiment history
- model monitoring reports

---

## 4. Data Contracts

### 4.1 Sample Contract

Each sample contains:

- `sample_id`
- crop and variety
- 6 image references
- validation report
- metadata
- measured moisture values, if available
- labels

### 4.2 Prediction Contract

Each prediction must contain:

- `sample_id`
- model version
- calibration version
- moisture risk
- optional moisture estimate
- confidence
- quality metrics
- reject or warning reasons

### 4.3 Feedback Contract

Feedback may contain:

- meter-confirmed moisture
- human quality review
- accepted / rejected prediction
- relabel request

---

## 5. Storage Architecture

### Raw Asset Store

Store:

- original images
- immutable metadata snapshot
- upload timestamps

### Processed Asset Store

Store:

- normalized images
- masks
- feature files
- pair delta maps

### Relational or Structured Store

Store:

- samples
- devices
- batches
- moisture readings
- model outputs
- calibration versions
- feedback
- audit logs

### Experiment Store

Store:

- training runs
- dataset versions
- metrics
- ablation results
- threshold versions

---

## 6. Inference Modes

### Mode A: On-Device Validation + Cloud Inference

Use when:

- network is available
- stronger model is hosted remotely

Benefits:

- better model size flexibility
- easier central updates

Risks:

- network dependency

### Mode B: Fully Offline Lightweight Inference

Use when:

- low-connectivity environment is common

Benefits:

- field usability

Risks:

- smaller model
- harder updates

### Recommended Initial Mode

- on-device validation
- cloud inference
- optional offline fallback for risk-only output

---

## 7. Deployment Topology

```text
Mobile App
  |
  +--> Validation SDK
  |
  +--> Upload API
          |
          +--> Object Storage
          +--> Metadata Store
          +--> Preprocessing Worker
          +--> Inference Service
          +--> Calibration Service
          +--> Report Service
          +--> Monitoring / Metrics
```

---

## 8. Security and Integrity Rules

- raw images must never be overwritten
- every prediction must record model and calibration version
- every training dataset must be versioned
- screenshots must be blocked from sample ingestion
- measured moisture labels must store source and method
- audit trail must be preserved for relabeling and debugging

---

## 9. Architecture Rules For Claude

When implementing:

1. Build validation before model inference.
2. Do not couple UI upload directly to prediction without checks.
3. Keep preprocessing deterministic and auditable.
4. Keep crop-specific calibration separate from model weights when possible.
5. Use modular services so retraining and calibration can evolve independently.
6. Preserve raw data, processed data, and predictions as separate layers.
7. Optimize for low false-safe rate rather than headline accuracy.

---

## 10. Implementation Priority

1. Capture and validation architecture
2. Metadata schema and storage
3. Preprocessing and grid/reference pipeline
4. Segmentation baseline
5. Feature extraction
6. Ragi model
7. Calibration service
8. Confidence and report service
9. Monitoring and feedback loop
10. Multi-crop expansion only after ragi is validated

