# Product Specification

**Goal:** Develop a **finger millet (ragi) grain grading app** that uses AI vision to assess grain quality. The system captures images of ragi grains via a mobile app, analyzes them with Gemma 4 (vision + reasoning), and returns: Grade (A/B/C/D), Quality Score (0–100), defect breakdown, and actionable remarks.

**Users:** Small farmers, grain traders, food processors, and quality inspectors in the millet supply chain. They need a fast, portable way to check batch quality on-site without lab equipment.

**Key Features:**

- **Image Capture:** Use smartphone camera (recommended ≥1080p, macro focus) to photograph batches of ragi grains on a plain background.
- **AI Analysis:** Backend invokes Gemma 4 to analyze color, size, and identify defects/contaminants (stones, dust, broken grains, mold, weevil damage).
- **Scoring & Grading:** Compute a quality score (0–100) using weighted criteria (color uniformity, purity, damage, etc.). Assign grade A/B/C/D based on thresholds.
- **Results:** Display grade, score, defect statistics, and confidence. Optionally highlight problem areas in the image.
- **History:** Save past analyses for tracking.

**Deliverables:**

- Mobile app (Flutter) for image capture and result display.
- Cloud API (FastAPI) hosting Gemma 4 model and grading logic.
- Documentation and testing utilities.

**Constraints:**

- **Performance:** Inference latency <2s per image; run on mid-range devices and cloud GPUs.
- **Accuracy:** ≥90% agreement with expert grading. Balance false positives/negatives (prefer safety: downgrade on uncertainty).
- **Compliance:** Adhere to food standards. E.g., FSSAI limits millets to ≤1% extraneous matter and ≤13% moisture【7†L733-L742】. NIFTEM notes ragi flour uses *“purely graded, de-stoned ragi grains”*【31†L25-L30】, implying our AI must reliably detect stones/impurities.
- **Usability:** Simple UI, minimal steps. Operable offline or low-bandwidth (support image upload in background).

**Success Metrics:**

- Accuracy ≥90% on blind test set.
- API availability 99%+ uptime.
- Mobile app usable on Android/iOS.
- User satisfaction in field trials (e.g., faster than manual checking).

---
