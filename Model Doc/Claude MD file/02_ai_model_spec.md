# AI Model Specification (Gemma 4)

## Model Variants & License

We use Google’s **Gemma 4** family for vision+reasoning. All models are open-source under **Apache 2.0**【9†L439-L447】 (commercial-friendly). Key variants:

- **E2B (2B effective):** Tiny model for on-device/edge. Low GPU usage, but less reasoning power.
- **E4B (4B effective):** Small model for mobile and low-latency tasks. Good for quick inference on-device.
- **26B (MoE):** Medium model (mix-of-experts, effectively 3.8B active) balancing quality and speed. Good first choice for server inference.
- **31B (Dense):** Large model for highest accuracy (requires heavy GPUs or Cloud TPUs).
  
| Gemma Variant | Parameters | Best Use Case                           |
|-------------|-----------|---------------------------------------|
| E2B (2B)    | 2B (Eff)  | On-device rapid inference, prototyping |
| E4B (4B)    | 4B (Eff)  | Mobile-edge inference, fast queries    |
| 26B MoE     | 26B (Eff 3.8B) | High-performance inference (cloud)   |
| 31B Dense   | 31B       | Maximum accuracy; fine-tuning tasks    |

*(All Gemma 4 models are Apache 2.0 licensed【9†L439-L447】.)*

## Prompt Design (System + User)

We use a **chain-of-thought** style prompt to guide Gemma 4. For example:

**System Prompt:**  

```
You are an agricultural grain quality inspector specialized in finger millet (ragi). 
Analyze the given image and perform a detailed quality assessment. 
Check the following in order:
1. **Color uniformity:** Identify grain color consistency. 
2. **Grain size/shape:** Detect broken or shriveled grains. 
3. **Foreign matter:** Spot any stones, dust, or other impurities. 
4. **Biological defects:** Find mold spots or insect damage on grains.
Compute the percentage of each defect category. Then assign a grade (A/B/C/D) and a quality score (0–100) based on weighted criteria. 
Output only JSON as per the format below.
```

**User Prompt (Example):**  

```
[IMAGE: finger millet grains on white background]
Perform the analysis as instructed.
```

## Chain-of-Thought Steps

1. **Preprocess image** (normalize, enhance contrast if needed).
2. **Detect grain regions** vs. background.
3. **Evaluate color distribution** of grains (look for off-color or mold).
4. **Count and segment anomalies:** e.g. stones, dust, broken pieces, weevil holes.
5. **Compute defect percentages** (e.g. % foreign matter, % damaged grains).
6. **Apply scoring algorithm** (weighted sum: see scoring doc).
7. **Assign grade** A/B/C/D by score thresholds.
8. **Compose structured JSON** with all required fields (including confidence).

## Output JSON Schema

Gemma should return a JSON object. Example schema:

```json
{
  "grade": "A",
  "quality_score": 92.5,
  "color_uniformity": "high",
  "foreign_matter_pct": 0.5,
  "broken_grains_pct": 0.2,
  "insect_damage_pct": 0.0,
  "fungus_detected": false,
  "confidence": 0.96,
  "remarks": "Premium-quality ragi; no issues detected."
}
```

- *grade*: A/B/C/D  
- *quality_score*: 0–100 scale  
- *<defect>_pct*: percentage of that defect in the batch  
- *confidence*: model confidence (0–1)  
- *remarks*: short human-readable note.

---
