# Dataset Collection

## Current Dataset Reality

The folder `Grain moisture details chat chatgpt` is not a valid training dataset.

Problems found:

- mostly screenshots instead of raw camera images
- no measured moisture labels
- no device metadata
- no lighting metadata
- no temperature/humidity metadata
- one unreadable file

This repository needs a real measured dataset before model claims are possible.

---

## Required Sample Contents

Each valid sample must include:

- 6 raw images
- crop label
- batch identifier
- measured moisture percentage
- repeated moisture readings
- device model
- flash/no-flash status
- calibration grid version
- reference patch version
- capture distance
- ambient temperature
- ambient humidity
- optional lux value

---

## Ground Truth Quality Levels

- A: oven-dry lab result
- B: calibrated moisture meter with repeats
- C: weak meter or incomplete protocol
- D: visual estimate only

Only A and B should be used for production training and calibration.

---

## Minimum Targets

For ragi:

- prototype: 500-1,000 measured samples
- strong model: 5,000-10,000 measured samples
- production: multi-region, multi-season, multi-device dataset

---

## Split Policy

Use train/validation/test split by:

- farm
- batch
- date
- device

Do not split randomly by image.

