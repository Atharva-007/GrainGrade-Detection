"""
Deterministic FAO/BIS-aligned threshold rules for ragi grading.

The model can describe the image, but this engine owns the final threshold
decision for moisture, foreign matter, visible hazards, and defect load.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


GRADE_ORDER = {"C": 0, "B": 1, "A": 2}
NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


@dataclass(frozen=True)
class RagiRuleThresholds:
    """Conservative operator-assist thresholds from the RAG rule anchor."""

    moisture_a_max: float = 12.0
    moisture_b_max: float = 13.0
    moisture_c_max: float = 14.0

    foreign_a_max: float = 0.10
    foreign_b_max: float = 0.75
    foreign_c_max: float = 1.0

    other_grain_a_max: float = 1.0
    other_grain_b_max: float = 2.0
    other_grain_c_max: float = 4.0

    damaged_a_max: float = 3.1
    damaged_b_max: float = 6.3
    damaged_c_max: float = 9.5

    off_tone_a_max: float = 5.0
    off_tone_c_min: float = 10.0
    size_dev_a_max: float = 5.0
    size_dev_c_min: float = 15.0
    shape_defect_a_max: float = 5.0
    shape_defect_c_min: float = 10.0
    broken_c_min: float = 5.0


@dataclass
class RuleDecision:
    grade: str
    score: int
    reject: bool
    reject_reasons: List[str] = field(default_factory=list)
    broken_grain: float = 0.0
    foreign_matter: float = 0.0
    uniformity: float = 70.0
    mold_visible: bool = False
    rule_hits: List[str] = field(default_factory=list)


def _as_float(value: Any, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    match = NUMBER_RE.search(str(value))
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return default
    return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    return text in {"true", "yes", "y", "1", "present", "visible", "detected"}


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    return [str(value)]


def _grade_value(value: Any) -> str:
    text = str(value or "B").strip().upper()
    if text in GRADE_ORDER:
        return text
    if "GRADE A" in text:
        return "A"
    if "GRADE C" in text:
        return "C"
    return "B"


class RagiRuleEngine:
    """Applies hard ragi thresholds after VLM interpretation."""

    def __init__(self, thresholds: Optional[RagiRuleThresholds] = None):
        self.thresholds = thresholds or RagiRuleThresholds()

    def evaluate(
        self,
        response_json: Dict[str, Any],
        physics_proxies: Dict[str, Any],
        moisture_risk: Any = None,
        moisture_percent: Optional[float] = None,
        moisture_calibrated: bool = True,
    ) -> RuleDecision:
        t = self.thresholds

        llm_grade = _grade_value(response_json.get("quality_grade", "B"))
        off_tone = _as_float(response_json.get("off_tone_fraction"), 8.0)
        size_dev = _as_float(response_json.get("size_deviation"), 8.0)
        shape_defect = _as_float(response_json.get("shape_defect_fraction"), 8.0)
        broken_grain = _as_float(response_json.get("broken_grain_percent"), 2.0)
        foreign_matter = _as_float(response_json.get("foreign_matter_percent"), 0.5)
        other_grains = _as_float(response_json.get("other_edible_grains_percent"), 0.0)
        bimodal_color = _as_bool(response_json.get("bimodal_color_detected", False))
        mold_visible = _as_bool(response_json.get("mold_visible", False))
        visible_defects = [item.lower() for item in _as_list(response_json.get("visible_defects"))]

        darkness = _as_float(
            physics_proxies.get("lab_features", {}).get("color_darkness_index"),
            0.0,
        )
        clumping = _as_float(physics_proxies.get("clumping", {}).get("density"), 0.0)
        uniformity = _as_float(physics_proxies.get("uniformity_score"), 70.0)
        roughness = _as_float(physics_proxies.get("roughness_score"), 50.0)
        grain_coverage = _as_float(physics_proxies.get("grain_mask_coverage"), 0.5)

        moisture_label = str(getattr(moisture_risk, "value", moisture_risk or "")).upper()
        calibrated_moisture = _as_float(moisture_percent, -1.0)
        damaged_like = max(broken_grain, shape_defect)

        hazard_terms = (
            "mold",
            "mould",
            "fungus",
            "fungal",
            "insect",
            "weevil",
            "webbing",
            "stone",
            "glass",
            "metal",
            "deleterious",
            "obnoxious",
        )
        visible_hazard = mold_visible or any(
            any(term in defect for term in hazard_terms) for defect in visible_defects
        )

        hard_reasons: List[str] = []
        rule_hits: List[str] = []

        if visible_hazard:
            hard_reasons.append("Hard reject gate: visible mould, insect, stone, or deleterious material")
            rule_hits.append("hazard_gate")
        if foreign_matter > t.foreign_c_max:
            hard_reasons.append(f"Foreign matter {foreign_matter:.2f}% exceeds {t.foreign_c_max:.2f}%")
            rule_hits.append("foreign_matter_reject")
        if other_grains > t.other_grain_c_max:
            hard_reasons.append(f"Other edible grains {other_grains:.2f}% exceeds {t.other_grain_c_max:.2f}%")
            rule_hits.append("other_grains_reject")
        if damaged_like > t.damaged_c_max:
            hard_reasons.append(f"Defect load {damaged_like:.2f}% exceeds {t.damaged_c_max:.2f}%")
            rule_hits.append("damaged_reject")
        if calibrated_moisture > t.moisture_c_max:
            hard_reasons.append(f"Moisture {calibrated_moisture:.1f}% exceeds {t.moisture_c_max:.1f}%")
            rule_hits.append("moisture_reject")
        elif moisture_label == "CRITICAL":
            hard_reasons.append("Critical proxy moisture risk")
            rule_hits.append("moisture_reject")

        if hard_reasons:
            return RuleDecision(
                grade="C",
                score=25,
                reject=True,
                reject_reasons=hard_reasons,
                broken_grain=broken_grain,
                foreign_matter=foreign_matter,
                uniformity=min(uniformity, 35.0),
                mold_visible=mold_visible or visible_hazard,
                rule_hits=rule_hits,
            )

        proxy_quality_risk = (
            clumping > 0.32
            or darkness > 62
            or uniformity < 52
            or grain_coverage < 0.12
        )
        proxy_downgrade = (
            clumping > 0.18
            or darkness > 50
            or uniformity < 68
            or roughness < 25
        )
        proxy_grade_a_ok = (
            clumping < 0.12
            and darkness < 45
            and uniformity >= 72
            and roughness >= 20
            and grain_coverage >= 0.15
        )

        moisture_blocks_a = (
            moisture_label in {"MODERATE", "HIGH", "CRITICAL"}
            or calibrated_moisture > t.moisture_a_max
        )
        moisture_forces_c = (
            moisture_label == "HIGH"
            or calibrated_moisture > t.moisture_b_max
        )

        grade_c_reasons: List[str] = []
        if moisture_forces_c:
            grade_c_reasons.append("Moisture is above Grade B range")
            rule_hits.append("moisture_c")
        if foreign_matter > t.foreign_b_max:
            grade_c_reasons.append("Foreign matter is in Grade C range")
            rule_hits.append("foreign_matter_c")
        if other_grains > t.other_grain_b_max:
            grade_c_reasons.append("Other edible grains are in Grade C range")
            rule_hits.append("other_grains_c")
        if damaged_like > t.damaged_b_max:
            grade_c_reasons.append("Defect load is in Grade C range")
            rule_hits.append("damaged_c")
        if (
            off_tone > t.off_tone_c_min
            or size_dev > t.size_dev_c_min
            or shape_defect > t.shape_defect_c_min
            or broken_grain > t.broken_c_min
            or bimodal_color
            or proxy_quality_risk
            or (llm_grade == "C" and proxy_downgrade)
        ):
            grade_c_reasons.append("Visual defect thresholds indicate Grade C")
            rule_hits.append("visual_c")

        if grade_c_reasons:
            reject = bool(proxy_quality_risk or foreign_matter > t.foreign_b_max or moisture_forces_c)
            return RuleDecision(
                grade="C",
                score=55 if not reject else 45,
                reject=reject,
                reject_reasons=list(dict.fromkeys(grade_c_reasons)),
                broken_grain=broken_grain,
                foreign_matter=foreign_matter,
                uniformity=min(uniformity, 55.0),
                mold_visible=False,
                rule_hits=list(dict.fromkeys(rule_hits)),
            )

        grade_a_ok = (
            llm_grade == "A"
            and not moisture_blocks_a
            and off_tone < t.off_tone_a_max
            and size_dev < t.size_dev_a_max
            and shape_defect < t.shape_defect_a_max
            and broken_grain <= t.damaged_a_max
            and foreign_matter <= t.foreign_a_max
            and other_grains <= t.other_grain_a_max
            and not bimodal_color
            and proxy_grade_a_ok
        )
        if grade_a_ok:
            return RuleDecision(
                grade="A",
                score=90,
                reject=False,
                reject_reasons=[],
                broken_grain=broken_grain,
                foreign_matter=foreign_matter,
                uniformity=max(uniformity, 90.0),
                mold_visible=False,
                rule_hits=["grade_a_all_gates_pass"],
            )

        b_reasons: List[str] = []
        if moisture_blocks_a:
            b_reasons.append("Moisture blocks Grade A")
            rule_hits.append("moisture_b")
        if foreign_matter > t.foreign_a_max:
            b_reasons.append("Foreign matter above premium range")
            rule_hits.append("foreign_matter_b")
        if damaged_like > t.damaged_a_max:
            b_reasons.append("Defect load above premium range")
            rule_hits.append("damaged_b")
        if proxy_downgrade or llm_grade != "A":
            b_reasons.append("Lot is usable but not premium")
            rule_hits.append("visual_b")

        return RuleDecision(
            grade="B",
            score=75,
            reject=False,
            reject_reasons=[],
            broken_grain=broken_grain,
            foreign_matter=foreign_matter,
            uniformity=float(max(55.0, min(uniformity, 85.0))),
            mold_visible=False,
            rule_hits=list(dict.fromkeys(rule_hits or b_reasons)),
        )
