# Grain Grade Product Specification

## Product Goal

Build a fast ragi lot grading tool that helps farmers, traders, processors, and quality operators inspect finger millet from a photo.

The system outputs:

- quality grade: `A`, `B`, or `C`
- quality score: `0-100`
- moisture risk: `LOW`, `MODERATE`, `HIGH`, or `CRITICAL`
- reject or hold recommendation
- defect estimates
- confidence
- operator-facing summary
- audit evidence

## Product Boundary

This is:

- an AI-assisted grain quality screening tool
- a storage and procurement decision support tool
- a conservative visual inspection workflow

This is not:

- a certified moisture meter
- a BIS certification engine
- a lab replacement
- a generic all-crop classifier

## Users

Primary users:

- farmers checking whether a lot needs drying or cleaning
- traders checking visible quality before purchase
- processors checking incoming ragi lots
- field operators collecting feedback and labels

## Input

V1 input:

- one clear ragi lot image
- optional calibration sheet/grid
- auto-generated batch metadata

Future production input:

- six images per physical sample
- flash/no-flash pairs
- locked exposure, focus, white balance, and zoom
- measured moisture readings when available

## Output Contract

The app must preserve this final response shape:

```json
{
  "quality_grade": "B",
  "quality_score": 78,
  "reject_recommended": false,
  "reject_reasons": [],
  "broken_grain_percent": 3.2,
  "foreign_matter_percent": 0.8,
  "uniformity_score": 81.0,
  "mold_visible": false,
  "moisture_risk": "MODERATE",
  "moisture_estimate_calibrated": true,
  "moisture_percent_estimate": 12.6,
  "overall_confidence": 78,
  "model_version": "dashscope/qwen3-vl-plus",
  "rag_chunks_used": 4,
  "operator_summary": "Release with caution. Moisture risk is moderate.",
  "manual_review_required": false,
  "signal_highlights": ["Moisture risk: MODERATE"]
}
```

If moisture calibration is absent, the system may compute an internal provisional percent but must mark `moisture_estimate_calibrated = false`.

## Grade Policy

### Grade A

Use only for premium lots:

- very uniform grain color
- off-tone fraction below 5 percent
- size and shape defects below 5 percent
- foreign matter below 1 percent
- no visible biological hazards
- no strong dullness, clumping, or moisture-heavy signals

### Grade B

Use for commercial lots:

- minor color or size variation
- low foreign matter
- no visible hazard
- no strong Grade C signal

### Grade C

Use for poor, processing-grade, or catch-all lots:

- bimodal or mixed tones
- high off-tone fraction
- visible damage or shrivelling
- high dullness or clumping
- high moisture risk
- any lot that is not safe to call A or B

### Reject Recommended

Set `reject_recommended = true` when:

- visible mould/fungus appears
- insects, webbing, stones, glass, metal, mud lumps, or deleterious material appear
- foreign matter exceeds the configured outer threshold
- moisture risk is `CRITICAL`
- high moisture combines with low quality

Legacy Grade D must be represented as Grade C plus `reject_recommended = true`.

## Moisture Policy

Moisture is a separate axis from quality grade.

Risk bands:

- `LOW`: dry/stable-looking
- `MODERATE`: usable but may need caution
- `HIGH`: drying or meter confirmation recommended
- `CRITICAL`: hold/reject/dry immediately before storage

The app can warn on moisture risk from visual proxies, but must not claim lab-grade moisture measurement.

## User Flow

1. Operator uploads a lot image.
2. App checks resolution, blur, and luminance.
3. App extracts OpenCV physics proxies.
4. App retrieves rule anchors and similar corrections.
5. App calls cloud Qwen3-VL for visual evidence.
6. App repairs JSON if needed.
7. Deterministic rules produce final grade and reject decision.
8. App shows result, evidence, overlay, and action.
9. Operator submits correction if wrong.

## Performance Target

Target cloud path:

- local proxy extraction: under 1 second for normal images
- RAG retrieval: under 300 ms in lexical mode
- cloud Qwen3-VL response: provider/network dependent, target 1-4 seconds
- end-to-end target: under 5 seconds for a normal single image

Fast path:

- if proxy evidence is already clearly bad, skip VLM and return deterministic result quickly.

## Acceptance Criteria

- Existing tests still pass.
- App can run with `QWEN_VL_PROVIDER=dashscope`.
- App can still run with `QWEN_VL_PROVIDER=ollama`.
- Cloud API failures fall back to deterministic proxy/rule grading.
- Final result schema stays stable.
- The app never exposes unsupported certification claims.

