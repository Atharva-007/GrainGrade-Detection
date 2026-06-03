# 🔬 Physics of Moisture in Grains (Fundamental Layer)

## 🎯 Purpose

This document defines the **physical principles** behind moisture estimation using RGB images.

This is the **scientific foundation** of the entire system.

---

# 🧠 1. Core Concept

Moisture is a **latent physical property**:
- It cannot be directly observed using RGB cameras
- It must be inferred through **optical and structural proxies**

---

## 🔑 Key Principle

> Moisture changes how light interacts with grain surfaces.

---

# 🌈 2. Light Interaction Model

When light hits a grain, it splits into:

## 2.1 Diffuse Reflection

- Scattered in multiple directions
- Dominates rough surfaces

## 2.2 Specular Reflection

- Mirror-like reflection
- Strong directional highlight

---

## Mathematical Representation

\[
I_{total} = I_{diffuse} + I_{specular}
\]

---

# 💧 3. Effect of Moisture on Light Behavior

## 3.1 Surface Smoothing

Water fills micro-roughness → surface becomes smoother

| Property | Dry Grain | Wet Grain |
|----------|----------|----------|
| Surface roughness | High | Low |
| Reflection type | Diffuse | Specular |
| Shine | Low | High |

---

## 3.2 Refractive Index Change

Water increases refractive index → more reflection

---

## 3.3 Absorption Behavior

Wet grains:
- absorb more light
- appear slightly darker

\[
I_{out} = I_{in} \cdot e^{-k \cdot moisture}
\]

---

# 🧪 4. Texture and Microstructure Changes

## Dry Grains

- Irregular microstructure
- High-frequency texture
- Rough surface

---

## Wet Grains

- Smoothed surface
- Lower frequency variation
- Reduced micro-contrast

---

## Observable Effect

| Feature | Dry | Wet |
|--------|-----|-----|
| Texture variance | High | Low |
| Edge sharpness | High | Low |
| Micro contrast | High | Low |

---

# 🧲 5. Inter-Particle Physics (Clumping)

## Mechanism

Moisture introduces:
- capillary forces
- surface tension

---

## Result

- Grains stick together
- Reduced separation

---

## Observable Signals

| Feature | Dry | Wet |
|--------|-----|-----|
| Separation | High | Low |
| Clusters | Small | Large |
| Component count | High | Low |

---

# 📐 6. Density and Packing Behavior

## Dry Grain

- Loose packing
- Individual grains clearly visible

---

## Wet Grain

- Compact packing
- Overlapping and clustering

---

## Observable Metric

- grains per grid cell
- spatial distribution variance

---

# 🎨 7. Color Space Effects

Moisture affects:

- brightness (L channel ↓)
- saturation ↓
- slight darkening

---

## Recommended Color Spaces

- LAB (preferred)
- HSV (secondary)

---

# 📊 8. Entropy and Information Theory

## Definition

\[
H = -\sum p(x)\log p(x)
\]

---

## Interpretation

| State | Entropy |
|------|--------|
| Dry | High |
| Wet | Low |

---

## Reason

- Dry → irregular patterns  
- Wet → smoother patterns  

---

# 🔍 9. Observable Proxy Signals

We do NOT measure moisture directly.

We measure:

| Proxy | Meaning |
|------|--------|
| Specular ratio | surface wetness |
| Texture variance | roughness |
| Entropy | structural complexity |
| Clumping | cohesion |
| Density | packing |
| Color shift | absorption |

---

# 🔗 10. Mapping Chain

```text
Moisture
 → Physical changes
 → Optical changes
 → Image features
 → Model prediction