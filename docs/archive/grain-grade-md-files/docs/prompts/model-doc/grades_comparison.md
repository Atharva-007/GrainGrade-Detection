# Grade A / B / C — Side-by-Side Decision Matrix (Finger Millet)

This is the authoritative comparison table. When the model is uncertain
between two grades, apply this matrix row-by-row.

---

## 1. THRESHOLD MATRIX

| Signal                         | Grade A (Premium)   | Grade B (Commercial)      | Grade C (Processing / Catch-all) |
| ------------------------------ | ------------------- | ------------------------- | --------------------------------- |
| Off-tone grain fraction        | <5%                 | 5–10%                     | 10–35% (or bimodal)               |
| Color pattern                  | Single tone         | Single tone + minor scatter| Bimodal (two distinct tones)      |
| Size deviation                 | <5%                 | 5–15%                     | 15–30%                            |
| Shape defect fraction          | <5%                 | 5–10%                     | 10–25%                            |
| Foreign matter (% area)        | <1%                 | 1–3%                      | up to 3% (>3% → reject)           |
| Large contaminants (stones)    | Absent              | Absent                    | Must be absent (if present → reject) |
| Biological hazards             | Absent              | Absent                    | ANY hazard → reject_recommended   |
| Storage dullness               | None                | Minor / isolated          | Tolerated; widespread → reject    |
| Aggregate score                | 90–100              | 75–89                     | <75                               |
| Recommended use                | Direct human food   | Retail / general food     | Processing / feed / secondary     |

---

## 2. THE THREE TELL-TALE QUESTIONS

When classifying a batch, answer these in order. The first "yes" determines
the grade.

1. **Are there ANY biological hazards or stones?**
   - Yes → **Grade C** with `reject_recommended=true`. Stop.
2. **Does the image show two clearly distinct color tones intermingling?**
   - Yes → **Grade C**. Stop.
3. **Is the off-tone grain fraction <5% AND shape/size defects <5% AND foreign matter <1%?**
   - Yes → **Grade A**. Stop.
   - No (but no hazards, not bimodal) → **Grade B**.

---

## 3. FAILURE MODES TO GUARD AGAINST

| Mistake                           | Guard                                                       |
| --------------------------------- | ----------------------------------------------------------- |
| Over-grading B as A               | Demand off-tone <5% AND defects <5%; both, not either       |
| Under-grading A as B              | Check for confounding shadow before penalizing for off-tone |
| Missing bimodal → C signal        | Explicitly ask "is the color distribution bimodal?"         |
| Missing a hazard (mold on dark grains) | Always run the biological-hazard hard gate FIRST        |
| Confusing sand/dust with grain    | Texture + color contrast check                              |
| Wrong grade from bad lighting     | Require >200 grains visible + focus validity first          |

---

## 4. COMPARISON TO HANDBOOK STANDARDS

Per *Handbook of Millets – Processing, Quality and Nutrition*:
- Grade A aligns with the handbook's "premium food use" — uniform, clean,
  no post-harvest damage signs.
- Grade B aligns with "commercial-grade food use" — minor variance from
  optimal drying, sorting, and handling.
- Grade C subsumes the handbook's "processing / feed grade" AND "reject"
  categories, since this deployment uses a 3-tier scale. Hazardous lots
  stay at Grade C with `reject_recommended=true`.

---

## 5. EXAMPLES — WHICH IMAGE IS WHICH?

| Reference file                                        | Grade | Why it's that grade                              |
| ----------------------------------------------------- | ----- | ------------------------------------------------ |
| `Ragi Image/GRADE A/IMG_4383.JPG`                     | A     | Uniform reddish-brown, <5% off-tone, tight size  |
| `Ragi Image/GRADE A/IMG_4491.JPG`                     | A     | Macro — plump spherical, clean surface           |
| `Ragi Image/GRADE B/IMG_4397.JPG`                     | B     | Mostly uniform; ~8% dark minority scattered      |
| `Ragi Image/GRADE B/IMG_4403.JPG`                     | B     | Upper-bound B; trace darker grains, clean        |
| `Ragi Image/GRADE C/IMG_4411.JPG`                     | C     | Bimodal: ~20–25% dark grains mixed in            |
| `Ragi Image/GRADE C/IMG_4415.JPG`                     | C     | Dense C; bimodal tone + size variance            |
| `Ragi Image/GRADE C/IMG_4421.JPG`                     | C     | Scattered dark pockets + shriveled tails         |

---

# END OF DOCUMENT
