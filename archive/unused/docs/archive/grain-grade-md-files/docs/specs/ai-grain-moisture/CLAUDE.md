# Claude Implementation Guide

This repository is designed to be implemented by an AI coding agent such as Claude or Codex.

## Highest-Priority Rules

1. Do not train on screenshots.
2. Do not treat visual appearance as ground truth moisture.
3. Start with finger millet / ragi only.
4. Enforce 6-image capture per sample.
5. Require calibration grid and white/gray reference patch.
6. Require measured moisture labels for training.
7. Keep raw images immutable.
8. Reject low-quality inputs before inference.
9. Keep moisture risk separate from quality grade.
10. Do not expose moisture percentage without calibration.

## Suggested Build Order

1. dataset validator
2. metadata schema
3. mobile capture validation
4. grid/reference detector
5. preprocessing pipeline
6. segmentation baseline
7. feature extractor
8. baseline ragi model
9. calibration layer
10. evaluation dashboard
11. backend API
12. mobile app integration

## What Claude Should Never Do

- invent measured moisture labels
- silently accept gallery screenshots
- merge all grain crops into one first-pass model
- claim validated accuracy without metrics
- overwrite raw data during preprocessing

## Required Reporting

Every training or evaluation run should report:

- crop
- dataset counts
- split method
- MAE
- RMSE
- precision
- recall
- F1
- calibration error
- false-safe rate
- rejection rate

