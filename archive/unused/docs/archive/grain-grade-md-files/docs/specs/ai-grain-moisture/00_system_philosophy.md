# System Philosophy

## Primary Principle

This system is not an image classifier that guesses moisture from random photos.

It is a controlled optical measurement workflow that estimates moisture risk from carefully captured grain images and supporting metadata.

---

## What The System Is

- a field-oriented estimation tool
- a controlled capture pipeline
- a hybrid vision + feature system
- a crop-specific model family
- a confidence-aware decision engine

---

## What The System Is Not

- a certified moisture meter
- a universal one-model-for-all-grains solution
- a system that should accept arbitrary gallery photos
- a pure CNN shortcut learner

---

## Design Pillars

1. Controlled input is more valuable than a larger model.
2. Physics-aware features are more trustworthy than blind pattern fitting.
3. Crop-specific calibration is safer than generic multi-crop guessing.
4. Rejection logic is better than false confidence.
5. Ground truth must come from measurement, not visual intuition.

---

## Product Truth

The most important user-facing promise should be:

"AI-assisted moisture-risk and grain-quality screening."

The system should only show a calibrated moisture percentage after:

- measured training labels exist
- crop-specific calibration is complete
- error metrics are validated on held-out data

---

## Safety Principle

False-safe predictions are more dangerous than false-risky predictions.

If the system is uncertain, it must:

- ask for a retake
- lower confidence
- request a moisture meter confirmation

---

## First Crop Rule

Start with finger millet / ragi only.

Do not generalize to other crops until:

- raw data exists
- measured labels exist
- crop-specific thresholds exist
- calibration is validated

