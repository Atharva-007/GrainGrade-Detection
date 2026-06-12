# Google Vision AI — Grade A Ragi (Finger Millet) Detection Prompt

### Target: Identify Grade A (Premium Food Grade) Finger Millet from macro photographs

### Source References:
- `finger_millet_ai_grading.md` (scoring model, grading framework)
- `Handbook of Millets – Processing, Quality and Nutrition`
- Ground-truth examples: `Grain Quality- Pankaj/Ragi Image/GRADE A/`

---

## 1. OPERATIONAL DEFINITION — WHAT IS GRADE A?

Grade A is the **Premium Food Grade** tier. It represents lots suitable for
direct human consumption with no processing concerns, no safety flags, and
a visually "textbook" appearance.

### Grade A is characterized by the simultaneous presence of:
1. **High color uniformity** — a single dominant tone (reddish-brown, dark brown,
   yellowish, or whitish depending on cultivar) with **<5% off-tone grains**.
2. **Tight size distribution** — grains cluster around a single modal diameter
   (1–2 mm); <5% deviate meaningfully.
3. **Full, spherical shape** — grains are plump, rounded, with smooth surface.
   <5% show shrivel, flattening, or fragmentation.
4. **Near-zero foreign matter** — <1% dust/fines by visible area; no stones,
   chaff, or debris.
5. **Zero biological hazard signals** — no mold, webbing, holes, clumping,
   insect bodies, or fungal bloom anywhere in the frame.
6. **Good storage state** — no widespread dullness, no oxidative greying,
   no moisture-clumping.

Grade A is the benchmark. If ANY criterion drops materially, demote to B.

---

## 2. KEY DIFFERENTIATORS — GRADE A vs. GRADE B

| Signal                   | Grade A                | Grade B                        |
| ------------------------ | ---------------------- | ------------------------------ |
| Off-tone grain fraction  | <5%                    | 5–10%                          |
| Size deviation           | <5%                    | 5–15%                          |
| Shape defects            | <5%                    | 5–10%                          |
| Foreign matter           | <1%                    | 1–3%                           |
| Surface finish           | Matte-clean, consistent| Mostly matte, slight variance  |
| Score band               | 90–100                 | 75–89                          |

Any condition crossing into the B column → NOT Grade A.

---

## 3. GRADE A VISUAL FINGERPRINT (from reference images IMG_4383, IMG_4491)

Observed ground-truth signals in confirmed Grade A ragi samples:
- **Single dominant tone** — reddish-brown, consistent across the entire frame.
  No visible "two-tone" appearance.
- **Tight spherical grains** — visually plump, rounded, near-identical in size.
- **Matte-clean surface** — grains are neither overly glossy (over-polished) nor
  dull (aged/oxidized).
- **Negligible dark-grain minority** — any darker grains are so few they do not
  form visible pockets or bands.
- **No visible contaminants** — background is clean, no stones, dust piles,
  chaff, or pest debris.
- **No biological flags** — no white/green bloom, no clumping, no holes, no
  webbing, no insect bodies.

**Counter-examples (do NOT classify as A):**
- Visibly mixed color tones (reddish + distinct dark/near-black pockets) → B or C.
- Dull, greyish bloom across the batch → storage issue, demote to B or below.
- Trace dust/fines >1% → B territory.
- Any hazard signal → C with reject_recommended=true.

---

## 4. FRAME-LEVEL CHECKLIST (binary gates)

Answer each question; ALL must be "yes" for Grade A:

- [ ] Is the dominant color uniform across the entire visible batch?
- [ ] Are <5% of grains visibly off-tone (darker or lighter than the mode)?
- [ ] Are grains tightly clustered in size (modal 1–2 mm with little variance)?
- [ ] Are grains plump / spherical, with <5% shriveled or flattened?
- [ ] Is foreign matter essentially absent (<1% of visible area)?
- [ ] Are there ZERO biological hazards (mold, webbing, insects, holes)?
- [ ] Is the surface finish consistent — neither dull nor patchy?

If any box is "no" → grade is B (if minor issue) or C (if major / hazardous).

---

## 5. WEIGHTED SUB-SCORES EXPECTED FOR GRADE A

| Parameter           | Weight | Grade A Expected Sub-score |
| ------------------- | ------ | -------------------------- |
| Color Uniformity    | 20%    | 90–100                     |
| Size Consistency    | 15%    | 90–100                     |
| Shape Integrity     | 15%    | 90–100                     |
| Foreign Matter      | 20%    | 95–100                     |
| Mechanical Damage   | 15%    | 90–100                     |
| Biological Risk     | 15%    | 100                        |

Aggregate score for Grade A: **90–100**.

---

## 6. DECISION RULE

```
IF (all frame-validity checks pass) AND
   (off_tone <5% AND size_dev <5% AND defects <5% AND
    foreign_matter <1% AND no biological hazards AND
    no widespread dullness)
   → Grade A  ✓

ELIF (minor violations in 1–2 criteria, still no hazards)
   → Grade B

ELSE
   → Grade C (with reject_recommended if hazards)
```

---

## 7. FINAL INSTRUCTION TO THE MODEL

> Grade A is a strict standard. Resist the temptation to award Grade A unless
> the evidence is overwhelming. If you can identify even one pocket of visibly
> darker or shriveled grains, the lot is Grade B or below, not A. Prioritize
> conservative grading — a misclassified Grade B as A is a downstream QC failure.

---

# END OF DOCUMENT
