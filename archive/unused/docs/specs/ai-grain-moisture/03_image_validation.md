# Image Validation

## Purpose

Prevent invalid captures from reaching preprocessing, model inference, calibration, or dataset storage.

---

## Validation Stages

### Stage 1: File Integrity

- file can be decoded
- image dimensions are above minimum threshold
- format is supported
- file is not obviously corrupted

### Stage 2: Raw Camera Check

Reject non-camera content such as:

- phone screenshots
- chat UI
- status bars
- icons and text overlays
- edited collages

### Stage 3: Quality Check

- blur score
- brightness score
- contrast score
- clipping check
- noise level

### Stage 4: Capture Compliance Check

- grid visible
- reference patch visible
- crop coverage sufficient
- flash/no-flash pair aligned
- same sample region visible

### Stage 5: Content Check

- correct crop type likely
- no mixed grains unless labeled as mixed
- overlap within tolerance
- mold, severe spoilage, or contamination flagged

---

## Suggested Metrics

- blur: variance of Laplacian or equivalent edge score
- brightness: mean luma range
- contrast: histogram spread or standard deviation
- glare: saturated highlight fraction
- overlap: connected-component crowding or density estimate
- screenshot likelihood: text/UI detector

---

## Reject Logic

Hard reject if:

- unreadable file
- screenshot detected
- grid missing
- reference patch missing
- major blur
- severe underexposure
- severe overexposure
- pair misalignment

Soft reject or retake warning if:

- moderate glare
- moderate shadow
- slightly low contrast
- incomplete metadata

---

## Validation Output

Example JSON:

```json
{
  "valid": false,
  "reasons": [
    "grid_missing",
    "flash_pair_misaligned"
  ],
  "quality_scores": {
    "blur": 0.42,
    "brightness": 0.81,
    "contrast": 0.56
  }
}
```

