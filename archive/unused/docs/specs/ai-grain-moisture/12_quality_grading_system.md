# Quality Grading System

## Purpose

Estimate grain quality independently from moisture risk.

Moisture and quality are related, but they are not the same output.

---

## Visual Components

- broken grain percentage
- foreign matter percentage
- uniformity
- color consistency
- dust/fines
- visible mold or discoloration

---

## Example Grade Logic

This must be crop- and standard-aware.

Example:

- Grade A: low foreign matter, low breakage, strong uniformity
- Grade B: moderate defects but acceptable quality
- Grade C: high defect or contamination risk

---

## Output Example

```json
{
  "quality_grade": "B",
  "quality_score": 76,
  "broken_grain_percent": 3.2,
  "foreign_matter_percent": 0.8,
  "uniformity_score": 81,
  "mold_visible": false
}
```

---

## Important Rule

Do not claim regulatory certification unless the grading logic is validated against official grading procedures.

