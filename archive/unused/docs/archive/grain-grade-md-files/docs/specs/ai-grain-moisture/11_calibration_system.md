# Calibration System

## Purpose

Map model outputs and optical proxy scores to crop-specific moisture-risk estimates and optional calibrated moisture percentage.

---

## Why Calibration Is Required

Different phones change:

- brightness
- sharpness
- color temperature
- flash intensity
- HDR behavior

Different crops also differ in:

- natural color
- roughness
- reflectance
- safe storage threshold

Without calibration, the model may learn device or crop artifacts instead of moisture.

---

## Per-Crop Calibration Rule

Maintain separate calibration for each crop.

First required calibration:

- finger millet / ragi

Do not reuse ragi calibration for:

- rice
- wheat
- maize
- pulses
- other millets

---

## Calibration Inputs

- crop type
- measured moisture percentage
- model raw score
- flash/no-flash features
- metadata
- device profile
- environmental context

---

## Calibration Methods

Recommended options:

- isotonic regression
- Platt scaling for classification confidence
- linear correction: `final = a * prediction + b`
- crop-specific boosted calibration head

---

## Starting Ragi Risk Bands

- LOW / SAFE: `<= 11.5%`
- MODERATE: `> 11.5% and <= 13.0%`
- HIGH / RISKY: `> 13.0%`
- CRITICAL: `>= 15.0%`

These are provisional and must be validated using measured ragi data.

---

## Recalibration Triggers

- new crop added
- new phone camera family added
- capture protocol changed
- grid/reference card changed
- model architecture changed
- field error increases

