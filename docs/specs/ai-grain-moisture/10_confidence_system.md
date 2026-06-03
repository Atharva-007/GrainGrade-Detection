# Confidence System

## Purpose

Decide whether the prediction is trustworthy enough to show, or whether the user should retake the sample or confirm with a meter.

---

## Inputs To Confidence

- model probability
- image quality score
- flash/no-flash consistency
- cross-view consistency
- calibration confidence
- metadata completeness
- similarity to training distribution

---

## Example Formula

```text
confidence =
  0.25 model_confidence
+ 0.20 image_quality
+ 0.20 cross_view_consistency
+ 0.15 calibration_confidence
+ 0.10 metadata_completeness
+ 0.10 in_distribution_score
```

---

## Decision Thresholds

- `>= 85`: trusted output
- `70-84`: usable but approximate
- `50-69`: low-confidence warning
- `< 50`: reject output

---

## Safety Rule

If moisture risk is HIGH but confidence is low, the system should still warn the user and recommend meter confirmation.

The system should optimize for low false-safe rate.

