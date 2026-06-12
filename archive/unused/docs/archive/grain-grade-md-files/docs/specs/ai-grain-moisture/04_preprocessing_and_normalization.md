# Preprocessing and Normalization

## Goal

Normalize raw captures so the model sees consistent geometry, color, and lighting behavior rather than phone-specific artifacts.

---

## Inputs

Each sample should contain:

- 3 no-flash images
- 3 flash images
- calibration grid
- white/gray reference patch
- metadata

---

## Processing Steps

### 1. Decode and Verify

- load raw image
- verify dimensions
- verify that the image passed validation

### 2. Grid Detection

- detect grid intersections
- estimate scale in pixels per cm
- estimate perspective distortion

### 3. Perspective Correction

- compute homography
- warp image into a normalized top-down coordinate system

### 4. Reference Patch Normalization

Use the white/gray patch to normalize:

- white balance
- color temperature
- exposure offset
- saturation drift

### 5. Color Space Conversion

Generate:

- RGB for audit
- LAB for stable color features
- HSV for brightness and saturation features
- grayscale for texture features

### 6. Flash / No-Flash Alignment

- align each flash image to its paired no-flash image
- reject if pair movement exceeds threshold

### 7. Pair Difference Maps

Compute:

- brightness delta
- highlight delta
- reflection delta
- texture delta

### 8. Region Crop

- crop the stable sample area
- remove obvious margins outside valid region
- keep audit-safe padding for review

### 9. Resize

- resize to model input size, for example 512 px
- preserve aspect ratio where needed

### 10. Store Artifacts

Store:

- raw image
- normalized image
- geometric transform
- quality scores
- pair alignment score

---

## Important Rule

Do not overwrite raw files. Raw capture must remain available for later audit, relabeling, or model debugging.

