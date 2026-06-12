# Model Architecture

## Design Goal

Build a crop-specific, confidence-aware hybrid model that combines image features, flash/no-flash comparison, and handcrafted physics features.

---

## Recommended Structure

```text
6 input images
  |
  |-- shared lightweight vision encoder
  |-- flash/no-flash pair difference branch
  |-- 3-view fusion block
  |
Image embedding

Handcrafted feature vector
  |
  |-- MLP
  |
Feature embedding

Metadata embedding
  |
  |-- crop, device, temperature, humidity, lux, grid version
  |
Metadata embedding

Fusion
  |
  |-- dense layers / attention
  |
Outputs
  |-- moisture percent regression
  |-- moisture risk classification
  |-- broken grain prediction
  |-- foreign matter prediction
  |-- confidence / uncertainty head
```

---

## Recommended First Encoder

- MobileNetV3
- EfficientNet-Lite

Reason:

- suitable for mobile or cloud deployment
- fast enough for iterative development
- easier to validate than large opaque models

---

## Output Heads

### Moisture Percent Head

- regression output
- only shown to users after calibration

### Moisture Risk Head

- LOW / MODERATE / HIGH
- main product output

### Quality Heads

- broken grain percentage
- foreign matter percentage
- optional grade score

### Confidence Head

- predicts trustworthiness of the output
- used by decision logic

---

## Key Architecture Rule

Do not rely on a pure CNN-only model.

The system should combine:

- learned visual representation
- explicit physical proxy features
- metadata for domain correction
- calibration layer after model inference

