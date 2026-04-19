# Google Vision AI — Grade B Ragi (Finger Millet) Detection Prompt

### Target: Identify Grade B (Commercial Food Grade) Finger Millet from macro photographs

### Source References:
- `finger_millet_ai_grading.md` (scoring model, grading framework)
- `Handbook of Millets – Processing, Quality and Nutrition`
- Ground-truth examples: `Grain Quality- Pankaj/Ragi Image/GRADE B/`

---

## 1. OPERATIONAL DEFINITION — WHAT IS GRADE B?

Grade B is the **Commercial Food Grade** tier — suitable for human consumption
and mainstream retail channels, but with **minor, non-hazardous variation**
that prevents it from being Grade A (premium).

### Grade B is characterized by the simultaneous presence of:
1. **Mostly uniform color** with a minor off-tone minority — **5–10% of grains
   visibly darker or lighter** than the dominant tone. Not yet bimodal.
2. **Slight size variance** — 5–15% of grains deviate from the modal size;
   no widespread shrivel.
3. **Minor shape defects** — 5–10% of grains show flattening, shrivel, or
   minor surface damage.
4. **Trace foreign matter** — 1–3% dust/fines visible; no stones, chaff, or
   large debris.
5. **Zero biological hazards** — no mold, webbing, insect damage, holes,
   or moisture clumping. (If any hazard is present, demote straight to C.)
6. **Acceptable surface** — grains matte with occasional minor dullness,
   but no widespread greying or oxidative bloom.

Grade B sits **between** the strictness of A and the tolerated defects of C.

---

## 2. KEY DIFFERENTIATORS — GRADE B vs. A and vs. C

| Signal                   | Grade A         | **Grade B**        | Grade C                    |
| ------------------------ | --------------- | ------------------ | -------------------------- |
| Off-tone grain fraction  | <5%             | **5–10%**          | 10–35%                     |
| Size deviation           | <5%             | **5–15%**          | 15–30%                     |
| Shape defects            | <5%             | **5–10%**          | 10–25%                     |
| Foreign matter           | <1%             | **1–3%**           | up to ~3%, but often higher|
| Color pattern            | Single tone     | **Mostly single**  | Clearly bimodal            |
| Biological hazards       | None            | **None (hard gate)**| Forces reject              |
| Score band               | 90–100          | **75–89**          | <75                        |

Grade B's signature is "clean-but-not-perfect." If color distribution looks
bimodal (two distinct tones intermingling), it is already C.

---

## 3. GRADE B VISUAL FINGERPRINT (from reference images IMG_4397, IMG_4403)

Observed ground-truth signals in confirmed Grade B ragi samples:
- **Dominant tone is clearly one color** (reddish-brown in these samples), but
  a **small dark minority (5–10%) is scattered through the batch** — not
  clustered into visible pockets.
- **Size distribution mostly tight**, with a small tail of slightly smaller
  or less-plump grains.
- **Surface is matte** with occasional individual dull grains; no widespread
  greying.
- **White background visible between grains**; no stones, dust piles, or chaff.
- **No biological signs** — no mold patches, no webbing, no clumping, no
  insect bodies.

**Counter-examples (do NOT classify as B):**
- Batches that are "textbook uniform" with <5% off-tone → Grade A (upgrade).
- Batches where dark grains form visible pockets or exceed ~10% → Grade C.
- Any mold / webbing / insect damage / heavy foreign matter → Grade C with
  reject_recommended=true.

---

## 4. FRAME-LEVEL CHECKLIST (binary gates)

Grade B requires:
- [ ] Dominant color is clearly one tone
- [ ] Off-tone grain fraction is in the 5–10% band (not <5%, not >10%)
- [ ] No visible bimodal clustering of dark grains
- [ ] Size distribution mostly tight, with <15% deviation
- [ ] Shape defects (shrivel, flat) are present but <10% of grains
- [ ] Foreign matter ≤3%, no stones/chaff
- [ ] ZERO biological hazards (this is a hard gate — any hazard → C)

If all boxes check → Grade B. If off-tone <5% and all other signals are clean
→ Grade A (do not force B). If off-tone >10% or bimodal → Grade C.

---

## 5. WEIGHTED SUB-SCORES EXPECTED FOR GRADE B

| Parameter           | Weight | Grade B Expected Sub-score |
| ------------------- | ------ | -------------------------- |
| Color Uniformity    | 20%    | 75–89                      |
| Size Consistency    | 15%    | 75–89                      |
| Shape Integrity     | 15%    | 75–89                      |
| Foreign Matter      | 20%    | 80–95                      |
| Mechanical Damage   | 15%    | 75–89                      |
| Biological Risk     | 15%    | 95–100 (any drop here → C) |

Aggregate score for Grade B: **75–89**.

---

## 6. DECISION RULE

```
IF (all hazards absent) AND
   (off_tone in [5%, 10%] AND size_dev <15% AND defects <10% AND
    foreign_matter <3% AND not bimodal)
   → Grade B  ✓

ELIF (off_tone <5% AND defects <5% AND clean)
   → Grade A  (upgrade)

ELIF (off_tone >10% OR bimodal OR any hazard OR foreign_matter >3%)
   → Grade C  (with reject_recommended if hazards)

ELSE
   → re-evaluate, downgrade on doubt
```

---

## 7. FINAL INSTRUCTION TO THE MODEL

> Grade B is the most commonly-misclassified tier because it sits between A
> and C. The test is: "Is there ONE clear dominant tone, OR two distinct
> tones?" If one clear tone with a minor off-tone scatter → B. If two tones
> visibly coexist → C. Never award B if any biological hazard is present —
> hazards always force C regardless of numeric score.

---

# END OF DOCUMENT
