# Capture Protocol

## Purpose

Capture repeatable, calibration-ready grain images that can support moisture-risk estimation and quality grading.

---

## Required Capture Set

Each physical sample must be captured as 6 images:

1. Top view, no flash
2. Top view, flash
3. Slight angle, no flash
4. Slight angle, flash
5. Lighting variation view, no flash
6. Lighting variation view, flash

The phone or sample must not move between flash/no-flash pairs.

---

## Camera Geometry

- distance from sample: 20-25 cm
- top view angle: near 90 degrees
- angled view: 15-25 degrees
- zoom: fixed
- focus: locked

The app should provide an overlay frame so the user can keep the same crop and distance for all images.

---

## Calibration Requirements

Every valid image must include:

- printed calibration grid with known spacing, ideally 1 cm
- neutral white or gray reference patch
- visible grain region

Preferred background:

- matte white or matte neutral sheet with printed calibration grid

Do not use:

- reflective trays
- patterned cloth
- shiny plastic
- dark surfaces similar to ragi color

---

## Camera Lock Rules

Before capture, lock:

- exposure
- white balance
- focus
- zoom
- resolution mode

These must remain stable across the full 6-image set.

---

## Sample Preparation Rules

- use a single crop type per sample
- spread grains so most are visible
- avoid thick piles and heavy overlap
- avoid mixed dust, mud, or wet clumps unless intentionally labeling defect cases
- keep the sample still across flash/no-flash pairs

---

## Lighting Rules

- daylight or evenly lit diffuse light is preferred
- avoid hard shadows
- avoid mixed yellow/blue lighting
- flash/no-flash pair must be captured from the same position

The flash image is not optional. It helps estimate reflection and surface wetness proxies.

---

## Hard Reject Conditions

Reject the capture if:

- image is blurry
- image is too dark
- image is overexposed
- calibration grid is missing
- reference patch is missing
- too few grains are visible
- grain overlap is excessive
- crop type appears mixed
- flash/no-flash pair is misaligned
- screenshot or app UI is detected instead of a raw camera image

---

## Capture UX Guidance

The mobile app should show:

- crop selection
- grid placement guide
- "move closer" or "move farther"
- "hold steady"
- "too dark"
- "too much glare"
- "retake flash pair"
- "sample too crowded"

