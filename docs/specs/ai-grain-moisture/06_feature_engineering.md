# Feature Engineering

## Purpose

Extract physically meaningful signals that correlate with moisture risk and grain quality.

These features should help the model resist shortcuts based on lighting, crop color, or device style.

---

## Feature Groups

### 1. Reflectance and Shine

- specular highlight ratio
- flash/no-flash highlight delta
- saturated pixel fraction
- highlight clustering

Interpretation:

- wet or surface-moist grains may appear shinier
- smooth grains can also reflect strongly
- shine must be interpreted together with texture and calibration

### 2. Texture

- local binary patterns
- GLCM contrast
- entropy
- edge density
- roughness score

Interpretation:

- dry grains may appear more textured
- wet grains may appear smoother or darker
- texture is highly crop-specific

### 3. Color

- LAB means and variances
- HSV saturation and value
- darkening relative to reference patch
- color uniformity

Interpretation:

- some wet grains darken
- some naturally dark crops such as ragi are already dark
- cross-crop color comparison is unsafe

### 4. Clumping and Density

- connected component size
- visible density per grid cell
- overlap ratio
- void distribution
- clump count

Interpretation:

- clumping may indicate moisture
- clumping may also come from dust, sample handling, or pile shape

### 5. Quality and Defect Features

- broken grain ratio
- foreign matter ratio
- dust/fines score
- uniformity score
- visible mold/discoloration flag

---

## Feature Safety Rules

- never trust a single feature alone
- calibrate features per crop
- prefer feature stability across views
- compare no-flash and flash behavior instead of relying on one image

