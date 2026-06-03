# Segmentation Pipeline

## Purpose

Separate the grain region from the background and estimate the visibility of individual grains, broken grains, and foreign matter.

---

## Segmentation Goals

- isolate grain from calibration sheet
- estimate visible grain coverage
- estimate overlap and clumping
- detect broken grain regions
- detect foreign matter and dust/fines

---

## Recommended Pipeline

### 1. Valid Region Definition

Use the calibration grid and reference patch to define the usable scene area.

### 2. Background Separation

Segment grain from:

- white sheet
- gray patch
- grid lines
- shadows
- empty background

### 3. Grain Mass Detection

Detect the total grain region and derive:

- total area
- edge boundary
- density distribution

### 4. Object-Level or Patch-Level Analysis

For larger grains, object-level segmentation may work well.

For ragi:

- grains are small
- object-level separation may be unstable
- patch-level density, texture, and defect estimation may be more robust

### 5. Overlap Detection

Estimate:

- pile thickness
- connected-component merging
- occlusion-heavy zones

If overlap is too high, reject or lower confidence.

### 6. Defect Segmentation

Segment candidate regions for:

- broken grains
- foreign matter
- dust/fines
- discoloration or visible mold

---

## Output

Example segmentation output:

```json
{
  "grain_mask_area": 0.63,
  "overlap_score": 0.41,
  "broken_region_fraction": 0.07,
  "foreign_matter_fraction": 0.01,
  "segmentation_confidence": 0.83
}
```

