# Google Vision AI — Grade C Ragi (Finger Millet) Detection Prompt

### Target: Identify Grade C (Processing / Feed Grade) Finger Millet from macro photographs

### Source References:
- `finger_millet_ai_grading.md` (scoring model, grading framework)
- `Handbook of Millets – Processing, Quality and Nutrition` (post-harvest science)
- Ground-truth examples: `Grain Quality- Pankaj/Ragi Image/GRADE C/`

---

## 1. OPERATIONAL DEFINITION — WHAT IS GRADE C?

Grade C is the **Processing / Feed tier**. It is *not* rejected (that is Grade D), and it is *not* food-premium (A) or commercial-food (B). A batch is Grade C when **visible defects are present across the lot**, but no single catastrophic failure (mold bloom, insect infestation, heavy foreign matter) tips it into Grade D.

### Grade C is characterized by the simultaneous presence of:
1. **Bimodal color distribution** — two or more distinct grain tones in the same batch (e.g., reddish-brown + dark brown/blackish grains visibly intermingled).
2. **Moderate size variance** — a mix of plump, medium, and small/shriveled grains rather than a tight size distribution.
3. **Visible shape defects on a non-trivial fraction of grains** — flattened, shrunken, or irregular seeds scattered through the batch.
4. **Moderate contamination tolerated** — small dust, fines, or trace foreign particles permissible; no large stones or gross debris.
5. **No active biological hazard** — no mold patches, no insect bodies, no webbing, no holes-in-grain clusters.

If ANY of the Grade D red flags appear (mold, webbing, insect damage clusters, heavy foreign matter >3%), the batch is Grade D, not Grade C.

---

## 2. SYSTEM PROMPT (Google Vision AI / Gemini Vision / PaLM Vision)

```
You are a food-quality inspector trained in post-harvest millet science, operating
under the standards in the Handbook of Millets – Processing, Quality and Nutrition.
Your sole task is to evaluate a macro photograph of finger millet (ragi, Eleusine
coracana) and determine whether the batch qualifies as GRADE C (Processing / Feed
Grade).

You MUST be conservative. When evidence is ambiguous, downgrade. Never upgrade on
uncertainty. Output must be strict JSON conforming to the schema in Section 6.
Do not output natural-language commentary outside the JSON.
```

---

## 3. USER / VISION PROMPT (attach image + send this text)

```
Analyze the attached macro photograph of finger millet grains. Decide whether this
batch is GRADE C (Processing / Feed Grade).

Perform the following visual checks in order, and record findings for each:

STEP 1 — FRAME VALIDITY
  - Is the image in focus, well-lit, and does it show grains densely enough
    (>200 grains visible) to judge? If no, return "grade": "unknown" and stop.

STEP 2 — COLOR DISTRIBUTION
  - Natural ragi color: reddish-brown to dark brown; occasionally yellowish or
    whitish cultivars.
  - Grade C signal: TWO or more distinct tones coexist — typically reddish-brown
    grains mixed with noticeably darker (near-black) grains in the same frame.
  - Estimate the percentage of dark/off-tone grains relative to the dominant tone.
  - Grade C range: 10%–35% off-tone grains.
  - <10% off-tone → likely Grade A or B.
  - >35% off-tone or blackened clumps → suspect Grade D (over-dried, fungal, or
    poor sorting).

STEP 3 — SIZE UNIFORMITY
  - Ragi grains are 1–2 mm spheres. A high-quality batch shows near-uniform
    diameter.
  - Grade C signal: visible size variance — a mix of plump grains alongside
    smaller, shriveled, or flattened grains. Roughly 15%–30% of grains deviate
    from the modal size.

STEP 4 — SHAPE INTEGRITY
  - Ideal: spherical, smooth surface.
  - Grade C defects (moderate prevalence, 10%–25% of grains):
      • Flattened / lens-shaped grains
      • Shriveled / wrinkled grains
      • Broken halves or fragments
      • Abrasion marks or surface dullness
  - >25% defective shapes → lean Grade D.

STEP 5 — FOREIGN MATTER
  - Look for: sand grains (similar size, different texture/color), stones,
    dust fines, chaff, plant debris, seeds of other crops.
  - Grade C tolerance: trace to moderate dust/fines (<3% by visible area).
    No large stones. No significant chaff piles.
  - Any visible stones >2 mm, or foreign matter >3% → Grade D.

STEP 6 — BIOLOGICAL & FUNGAL CHECK (HARD GATES)
  - Scan for: white/green fuzzy patches, cotton-like webbing, clustered grains
    stuck together, visible insect bodies, clean circular holes through grains,
    powdery residue around grains.
  - If ANY of these are present → return "grade": "D". Do NOT classify as C.

STEP 7 — STORAGE / OXIDATION SIGNS
  - Uniform dullness across the batch, grain clustering from moisture, or
    greyish bloom → note in "storage_risk" field.
  - Isolated dullness is acceptable for Grade C; widespread clustering is not.

STEP 8 — FINAL DECISION
  - Compute weighted score using the table in Section 4.
  - Grade C range: score 60–74.
  - If score ≥75 → output Grade B (do not force C).
  - If score <60 or any Step 6 red flag → output Grade D.

Return the strict JSON in Section 6. No prose outside JSON.
```

---

## 4. WEIGHTED SCORING MODEL (Grade C target: 60–74)

| Parameter           | Weight | Grade C Expected Sub-score |
| ------------------- | ------ | -------------------------- |
| Color Uniformity    | 20%    | 50–70                      |
| Size Consistency    | 15%    | 55–75                      |
| Shape Integrity     | 15%    | 55–75                      |
| Foreign Matter      | 20%    | 65–80                      |
| Mechanical Damage   | 15%    | 55–75                      |
| Biological Risk     | 15%    | 80–100 (must stay high — any low score here forces Grade D) |

**Score interpretation:**
- 90–100 → A
- 75–89 → B
- **60–74 → C  ← TARGET BAND**
- <60 → D

---

## 5. GRADE C VISUAL FINGERPRINT (from reference images IMG_4411–IMG_4421)

Observed ground-truth signals in confirmed Grade C ragi samples:
- Two-tone appearance: dominant reddish-brown grains intermixed with a meaningful
  minority of dark brown / near-black grains throughout the frame.
- Modal grain size present, but with a visible tail of smaller/shriveled grains.
- White background visible between grains; no visible stones, sand piles, mold,
  webbing, or insects.
- Grain scatter pattern indicates hand-spread lot; no clumping from moisture.
- No uniform glossy sheen (characteristic of Grade A) — surface appears matte
  to slightly dull.

**Counter-examples (do NOT classify as C):**
- Uniform single-tone reddish-brown, tight size distribution → Grade A.
- Minor color variance only, clean lot → Grade B.
- Any mold, webbing, insect parts, holes, or clumping → Grade D.

---

## 6. STRICT OUTPUT JSON SCHEMA

```json
{
  "grade": "C",
  "quality_score": 68,
  "is_grade_c": true,
  "color_analysis": {
    "dominant_tone": "reddish-brown",
    "secondary_tone": "dark-brown",
    "off_tone_percentage": 22,
    "uniformity": "moderate"
  },
  "size_analysis": {
    "uniformity": "moderate",
    "shriveled_fraction": 0.18
  },
  "shape_analysis": {
    "defect_fraction": 0.15,
    "defect_types": ["shriveled", "flattened"]
  },
  "foreign_matter": {
    "percentage": 1.2,
    "types_detected": ["dust"],
    "large_contaminants": false
  },
  "biological_risk": {
    "fungus_detected": false,
    "insect_damage": false,
    "webbing": false,
    "clumping": false
  },
  "storage_risk": "low",
  "grade_d_red_flags": [],
  "confidence": 0.87,
  "remarks": "Batch shows bimodal color distribution with ~22% dark grains and moderate shrivel fraction, consistent with Grade C (Processing/Feed). No biological hazards detected.",
  "recommended_use": "processing / animal feed / secondary milling"
}
```

### Schema rules:
- `grade` MUST be one of: `"A"`, `"B"`, `"C"`, `"D"`, `"unknown"`.
- `is_grade_c` is `true` only if `grade == "C"`.
- `grade_d_red_flags` lists any hard-gate failures from Step 6; if non-empty, `grade` MUST be `"D"`.
- `confidence` is a float 0.0–1.0; below 0.6, prefer downgrading grade.
- No fields may be null; use empty arrays, `false`, or `"unknown"` instead.

---

## 7. GOOGLE VISION AI API — CALL PATTERN (Gemini Vision)

```python
# Pseudocode for Gemini Vision API call
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = open("grade_c_ragi_vision_prompt.md").read()  # Section 2
USER_PROMPT   = "<text from Section 3>"

response = client.models.generate_content(
    model="gemini-2.5-pro",          # vision-capable model
    contents=[
        {"role": "user", "parts": [
            {"text": USER_PROMPT},
            {"inline_data": {"mime_type": "image/jpeg", "data": image_bytes}},
        ]},
    ],
    config={
        "system_instruction": SYSTEM_PROMPT,
        "temperature": 0.1,           # conservative, near-deterministic
        "response_mime_type": "application/json",
        "response_schema": GRADE_C_SCHEMA,  # see Section 6
    },
)

result = json.loads(response.text)
assert result["grade"] in {"A", "B", "C", "D", "unknown"}
```

### Image prep guidance (before sending to API):
- Resize so shortest edge ≥ 1024 px (preserve micro-texture).
- Do NOT apply sharpening or color correction (model must see true tones).
- Crop to the grain bed; exclude hands, bowls, labels.
- Prefer JPEG quality ≥ 90 to retain sub-pixel color detail.

---

## 8. FAILURE MODES TO GUARD AGAINST

| Failure                                         | Guard                                                           |
| ----------------------------------------------- | --------------------------------------------------------------- |
| Model over-grades a dusty lot to B              | Step 2 threshold (>10% off-tone forces C)                       |
| Model under-grades a clean batch with shadow    | Step 1 validity gate + confidence floor                         |
| Model misses mold on dark grains                | Step 6 is a HARD GATE — red flag overrides all numeric scoring  |
| Model confuses sand with grains                 | Step 5 texture check + large-contaminant rule                   |
| Lighting creates false bimodal tone             | Require >200 visible grains + frame validity                    |

---

## 9. DECISION RULE SUMMARY (for quick reference)

```
IF (any Step 6 red flag)                  → Grade D
ELIF (foreign_matter >3% OR stones)       → Grade D
ELIF (off_tone <10% AND defects <5%)      → Grade A or B
ELIF (off_tone 10–35% AND                 
      defect_fraction 10–25% AND          
      no biological risk)                 → Grade C  ✓
ELIF (score <60)                          → Grade D
ELSE                                      → re-evaluate, downgrade on doubt
```

---

## 10. FINAL INSTRUCTION TO THE MODEL

> Prioritize food safety and honest grading over optimism. Grade C means the lot
> is usable for processing or feed but not premium human consumption. When the
> evidence for Grade C is weaker than the evidence for Grade D, choose D.
> Always return the JSON schema from Section 6 and nothing else.

---

## 11. FEW-SHOT REFERENCE IMAGES (ANCHOR THE GRADE BOUNDARIES)

Provide these labeled images to the model **before** the target image. They
anchor the model to this specific ragi variety, lighting regime, and the
subjective threshold between adjacent grades. Use **prompt caching** on this
block so the cost is amortized across inference calls.

**Scale note:** This system uses a three-tier scale (A, B, C). There is no
Grade D. Grade C is therefore the lowest acceptable tier AND the catch-all
for anything below B, including lots that would be "reject" under a 4-tier
system. See §11.4 for how this changes the decision rules.

### 11.1 Image Manifest (relative to repo root)

| Role               | Grade | File Path                                                     | What it demonstrates                                                                       |
| ------------------ | ----- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Positive (top)     | A     | `Grain Quality- Pankaj/Ragi Image/GRADE A/IMG_4383.JPG`       | Dense batch, uniform reddish-brown, tight size distribution, <5% off-tone grains.          |
| Positive (top)     | A     | `Grain Quality- Pankaj/Ragi Image/GRADE A/IMG_4491.JPG`       | Macro close-up; individual grain color, plump spherical shape, matte-clean surface.        |
| Boundary (B↔C)     | B     | `Grain Quality- Pankaj/Ragi Image/GRADE B/IMG_4397.JPG`       | Mostly reddish-brown with slight dark minority (<10%); minor shape variance — still B.     |
| Boundary (B↔C)     | B     | `Grain Quality- Pankaj/Ragi Image/GRADE B/IMG_4403.JPG`       | Clean lot with trace darker grains, minimal shrivel — the upper bound of B, not yet C.     |
| **Target (C)**     | C     | `Grain Quality- Pankaj/Ragi Image/GRADE C/IMG_4411.JPG`       | Clear bimodal color: ~20–25% dark/near-black grains mixed through reddish-brown base.       |
| **Target (C)**     | C     | `Grain Quality- Pankaj/Ragi Image/GRADE C/IMG_4415.JPG`       | Dense C batch; visible size variance + bimodal tone; no biological hazard.                 |
| **Target (C)**     | C     | `Grain Quality- Pankaj/Ragi Image/GRADE C/IMG_4421.JPG`       | Mixed lot with scattered pockets of darker grains and shriveled tails — canonical Grade C. |

### 11.2 Labeled Few-Shot Block — Prompt Format

Send this block **ahead of** the target image in the same request:

```
Below are labeled reference examples of finger millet batches. Study the visual
patterns, then grade the final (target) image using the same criteria.

— REFERENCE 1 — GRADE: A — "Uniform dense reddish-brown, tight size, <5% off-tone."
[image: Grain Quality- Pankaj/Ragi Image/GRADE A/IMG_4383.JPG]

— REFERENCE 2 — GRADE: A — "Macro view, plump spherical grains, clean surface."
[image: Grain Quality- Pankaj/Ragi Image/GRADE A/IMG_4491.JPG]

— REFERENCE 3 — GRADE: B — "Mostly uniform with minor dark minority (<10%); still B."
[image: Grain Quality- Pankaj/Ragi Image/GRADE B/IMG_4397.JPG]

— REFERENCE 4 — GRADE: B — "Upper bound of B: trace darker grains, minimal shrivel."
[image: Grain Quality- Pankaj/Ragi Image/GRADE B/IMG_4403.JPG]

— REFERENCE 5 — GRADE: C — "Bimodal: ~20–25% dark grains mixed through red-brown."
[image: Grain Quality- Pankaj/Ragi Image/GRADE C/IMG_4411.JPG]

— REFERENCE 6 — GRADE: C — "Dense C batch with bimodal tone and size variance."
[image: Grain Quality- Pankaj/Ragi Image/GRADE C/IMG_4415.JPG]

— REFERENCE 7 — GRADE: C — "Canonical Grade C: scattered dark pockets + shrivel tails."
[image: Grain Quality- Pankaj/Ragi Image/GRADE C/IMG_4421.JPG]

— TARGET — GRADE: ?
[image: <the image to classify>]

Apply the 8-step procedure from Section 3 and return the JSON from Section 6.
```

### 11.3 Gemini Vision API — Multi-Image Call Pattern

```python
from google import genai
import mimetypes, pathlib, json

client = genai.Client(api_key=GEMINI_API_KEY)

def load_image_part(path: str) -> dict:
    mime, _ = mimetypes.guess_type(path)
    return {"inline_data": {
        "mime_type": mime or "image/jpeg",
        "data": pathlib.Path(path).read_bytes(),
    }}

REFERENCES = [
    ("A", "Uniform dense reddish-brown, tight size, <5% off-tone.",
     "Grain Quality- Pankaj/Ragi Image/GRADE A/IMG_4383.JPG"),
    ("A", "Macro view, plump spherical grains, clean surface.",
     "Grain Quality- Pankaj/Ragi Image/GRADE A/IMG_4491.JPG"),
    ("B", "Mostly uniform with minor dark minority (<10%); still B.",
     "Grain Quality- Pankaj/Ragi Image/GRADE B/IMG_4397.JPG"),
    ("B", "Upper bound of B: trace darker grains, minimal shrivel.",
     "Grain Quality- Pankaj/Ragi Image/GRADE B/IMG_4403.JPG"),
    ("C", "Bimodal: ~20-25% dark grains mixed through red-brown.",
     "Grain Quality- Pankaj/Ragi Image/GRADE C/IMG_4411.JPG"),
    ("C", "Dense C batch with bimodal tone and size variance.",
     "Grain Quality- Pankaj/Ragi Image/GRADE C/IMG_4415.JPG"),
    ("C", "Canonical Grade C: scattered dark pockets + shrivel tails.",
     "Grain Quality- Pankaj/Ragi Image/GRADE C/IMG_4421.JPG"),
]

parts = [{"text": "Labeled finger-millet references. Study before grading the target."}]
for grade, note, path in REFERENCES:
    parts.append({"text": f"— REFERENCE — GRADE: {grade} — {note}"})
    parts.append(load_image_part(path))

parts.append({"text": "— TARGET — GRADE: ? — Apply §3 steps; return §6 JSON only."})
parts.append(load_image_part(target_image_path))

response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=[{"role": "user", "parts": parts}],
    config={
        "system_instruction": SYSTEM_PROMPT,  # §2
        "temperature": 0.1,
        "response_mime_type": "application/json",
        "response_schema": GRADE_C_SCHEMA,    # §6
        # Enable caching on the reference block to amortize cost across calls:
        "cached_content": CACHED_REFERENCE_BLOCK_ID,
    },
)
result = json.loads(response.text)
```

### 11.4 Three-Tier Scale — Adjustments vs. Source Doc

The source `finger_millet_ai_grading.md` defines a four-tier scale (A/B/C/D)
where D = reject. This deployment uses **three tiers only (A/B/C)**. To keep
the prompt internally consistent, the model should apply the following
overrides when reading the earlier sections of this document:

- Everywhere §3, §4, §6, §8, §9 refer to "Grade D", treat that as a flag on
  the Grade C output instead. Do NOT emit `"grade": "D"` — it is not a valid
  value in this deployment.
- Biological hazards (mold, webbing, insects, holes, clumping) and heavy
  foreign matter (stones, debris >3%) do NOT downgrade beyond C — but they
  MUST be reported via the output fields `biological_risk.*`, `foreign_matter.*`,
  and a new top-level `"reject_recommended": true` flag so downstream systems
  can route hazardous C-grade lots away from human consumption.
- Update the allowed enum in §6 from `{"A","B","C","D","unknown"}` to
  `{"A","B","C","unknown"}`.
- Update the decision rule in §9: wherever it says "→ Grade D", substitute
  "→ Grade C with `reject_recommended: true`".

**Updated JSON fragment** (add to the §6 schema):

```json
{
  "grade": "C",
  "reject_recommended": true,
  "reject_reasons": ["fungus_suspected", "heavy_foreign_matter"]
}
```

`reject_recommended` MUST be `true` whenever any biological hazard or
heavy-foreign-matter condition is detected, regardless of the numeric score.

### 11.5 Lighting & Capture Variance

All current references are on a white background in natural daylight. If the
production pipeline will see other lighting (lightbox, mobile flash, overcast),
add 1 reference per lighting condition per grade to avoid lighting-induced
false grading.

### 11.6 Cost & Latency Notes

- Each inline image adds ≈ 250–1,000 tokens depending on resolution.
- 7 reference images + 1 target ≈ 2–8 k image tokens per call.
- **Use `cached_content`** (Gemini context caching) on the reference block.
  First call pays the full cost; subsequent calls read the cached prefix at
  ~10% of the input token price.
- Keep reference images ≤ 1024 px on the short edge for the prompt (model
  internally resizes anyway); keep the *target* at full resolution.

---

# END OF DOCUMENT
