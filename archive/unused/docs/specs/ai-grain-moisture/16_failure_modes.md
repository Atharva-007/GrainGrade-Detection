# Failure Modes

## Hard Reject Cases

- screenshot instead of camera image
- unreadable image
- missing calibration grid
- missing reference patch
- severe blur
- severe underexposure
- severe overexposure
- heavy overlap
- mixed crop sample
- flash/no-flash pair mismatch

---

## Soft Warning Cases

- moderate glare
- low contrast
- incomplete metadata
- unsupported device profile
- sample near decision threshold
- out-of-distribution appearance

---

## Dangerous Failures

- risky grain predicted as safe
- moldy grain accepted as usable
- dark crop color misread as moisture
- screenshots included in training data

---

## Policy

The system should minimize false-safe results even if it means more retakes or meter confirmations.

