# Training Pipeline

## Goal

Train a model that generalizes across farms, sessions, and devices without confusing lighting or crop identity with moisture.

---

## Training Scope

Start with one crop:

- finger millet / ragi

Do not train a generic multi-crop model first.

---

## Sample Unit

One training sample must contain:

- 6 images
- crop label
- metadata
- measured moisture percentage
- moisture risk class
- optional quality labels

---

## Ground Truth Requirements

Accepted labels:

- calibrated meter readings with repeats
- oven-dry laboratory values

Do not train on:

- visual guesses
- screenshot examples
- unlabeled images

---

## Dataset Split Rules

Never split randomly by image.

Split by:

- farm
- batch
- capture day
- device

Recommended:

- train: 70%
- validation: 15%
- test: 15%

The same physical sample batch must not appear in both train and test.

---

## Training Strategy

### Stage 1: Data Cleaning

- validate metadata
- validate image quality
- remove screenshots and corrupt images

### Stage 2: Baseline Model

- train a crop-specific baseline for ragi
- compare image-only vs hybrid feature model

### Stage 3: Calibration

- fit crop-specific calibration on validation data
- convert raw outputs into moisture-risk bands

### Stage 4: External Test

- evaluate on unseen farms and devices

---

## Metrics To Report

Regression:

- MAE
- RMSE
- R2

Classification:

- accuracy
- precision
- recall
- F1
- confusion matrix

Reliability:

- calibration error
- false-safe rate
- rejection rate

---

## Required Ablations

- no-flash only
- flash only
- flash + no-flash
- one image vs three views
- image-only model
- hybrid model
- no-grid vs grid
- generic crop model vs ragi-specific model

