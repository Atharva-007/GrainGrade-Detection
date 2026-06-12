# Inference Pipeline

## Input

One sample consists of:

- 6 images
- crop selection
- metadata

---

## Processing Flow

1. validate files
2. validate that input is raw camera content, not screenshot UI
3. detect grid and reference patch
4. normalize geometry and color
5. align flash/no-flash pairs
6. segment grain region
7. extract features
8. run crop-specific model
9. calibrate output
10. compute confidence
11. apply reject or retake policy

---

## Output Policy

If confidence is high:

- show moisture risk
- show quality metrics
- show estimated moisture percentage if calibrated

If confidence is medium:

- show moisture risk
- label estimate as approximate
- recommend caution

If confidence is low:

- do not show a confident percentage
- recommend retake or meter confirmation

---

## Example Output

```json
{
  "crop": "finger_millet",
  "moisture_risk": "MODERATE",
  "moisture_percent_estimate": 12.6,
  "confidence": 78,
  "quality_grade": "B",
  "broken_grain_percent": 3.1,
  "foreign_matter_percent": 0.8,
  "action": "dry_or_confirm_with_meter"
}
```

