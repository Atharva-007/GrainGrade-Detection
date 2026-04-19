# Scoring Algorithm & Evaluation

## Grading Algorithm

We use a **weighted scoring model** combining multiple quality parameters:

| Parameter            | Weight |
|----------------------|--------|
| Color Uniformity     | 20%    |
| Size/Shape Consistency | 15%  |
| Foreign Matter (impurities) | 25% |
| Broken/Damaged Grains | 20%   |
| Biological Defects (mold/insect) | 20% |

*Sample calculation:*  

```
score = 20%*(color_score) 
      + 15%*(size_score)
      + 25%*(purity_score) 
      + 20%*(damage_score) 
      + 20%*(bio_score)
```

Each sub-score (0–100) is derived from percentages of defects. E.g., if foreign matter > allowed, purity_score drops. If 100% uniform color, color_score=100; if many mixed colors, color_score lowers.

## Grade Thresholds

| Final Score | Grade |
|------------|-------|
| 90 – 100   | A (Premium) |
| 75 – 89    | B (Standard) |
| 60 – 74    | C (Feed) |
| < 60       | D (Reject) |

*(Grades reflect typical commercial categories; e.g., a Reject (D) often has mold or heavy contamination.)*

## Scoring Examples

- **Example 1:** 95% uniform color, 99% purity, 1% broken, no mold → Score ≈ 94 → Grade A.
- **Example 2:** 85% color uniformity, 97% purity (2% foreign), 5% broken → Score ≈ 72 → Grade C.
  
*(Concrete formula values depend on how thresholds are mapped in code.)*

## Evaluation Metrics

For the *AI model* performance, we will measure:

- **Detection Accuracy:** Precision/Recall/F1 on detecting foreign objects vs. grains.
- **Classification Accuracy:** % of images correctly graded (A/B/C/D) vs. human labels.
- **Mean Average Precision (mAP):** For object detection tasks (as in [39], they achieved 94.8% mAP【39†L602-L611】).
- **Speed:** Inference time per image.

We aim for >=90% precision/recall on defects and >=90% grade agreement.

## Test Plan

- **Validation Set:** Hold out 20% of annotated data for testing.
- **Cross-Validation:** Optionally k-fold if data limited.
- **Real-world Test:** Field test with new grain samples and expert feedback.
- **Robustness:** Test under varied lighting and backgrounds to ensure stability.

---
