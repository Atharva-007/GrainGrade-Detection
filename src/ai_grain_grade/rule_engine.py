"""
Deterministic FAO/BIS-aligned threshold rules for ragi grading.

The model can describe the image, but this engine owns the final threshold
decision for moisture, foreign matter, visible hazards, and defect load.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
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


def normalize_crop_name(crop_type: Any) -> str:
    """Normalize crop labels used by UI, datasets, and rule files."""
    text = str(crop_type or "").strip().lower().replace("-", " ").replace("_", " ")
    text = " ".join(text.split())
    if not text or text == "auto":
        return ""
    if text in {
        "ragi",
        "finger millet",
        "finger millets",
        "fingermillet",
        "fingermillets",
        "ragi / fingermillets",
        "ragi/fingermillets",
        "ragi/fingermillet",
    }:
        return "finger_millets"
    if text in {"bajari", "bajri", "bajara", "bajra", "pearl millet", "pearlmillet"}:
        return "bajra"
    if text in {"rice", "paddy", "dhan"}:
        return "rice"
    return text.replace(" ", "_")


@dataclass(frozen=True)
class CropMetricRule:
    """One typed metric from a crop grading YAML file."""

    name: str
    direction: str
    grade_a: float
    grade_b: float
    grade_c: float

    def grade_for_value(self, value: float) -> str:
        if self.direction == "min":
            if value < self.grade_c:
                return "REJECT"
            if value < self.grade_b:
                return "C"
            if value < self.grade_a:
                return "B"
            return "A"
        if value > self.grade_c:
            return "REJECT"
        if value > self.grade_b:
            return "C"
        if value > self.grade_a:
            return "B"
        return "A"

    def summary(self) -> str:
        op = ">=" if self.direction == "min" else "<="
        return (
            f"{self.name}: A {op} {self.grade_a:g}, "
            f"B {op} {self.grade_b:g}, C {op} {self.grade_c:g}"
        )


@dataclass(frozen=True)
class CropRuleSet:
    """Typed crop rule set loaded from docs/rag/crop_knowledge/grading_rules."""

    crop: str
    metrics: Dict[str, CropMetricRule]
    grade_a_score: int = 90
    grade_b_score: int = 75
    grade_c_score: int = 60

    def describe(self, limit: int = 14) -> List[str]:
        return [rule.summary() for rule in list(self.metrics.values())[:limit]]


def _extract_rule_blocks(text: str) -> Dict[str, Dict[str, float]]:
    """Parse the repository's compact YAML rule files without adding PyYAML."""
    metrics: Dict[str, Dict[str, float]] = {}
    current_metric = ""
    in_grading_engine = False
    for raw_line in text.splitlines():
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if indent == 0:
            in_grading_engine = line == "grading_engine:"
            current_metric = ""
            continue

        if not in_grading_engine:
            continue

        metric_match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*):\s*$", line)
        if metric_match and indent <= 2 and not line.startswith("grade_"):
            current_metric = metric_match.group(1)
            metrics.setdefault(current_metric, {})
            continue

        grade_match = re.match(
            r"grade_([abcABC]):\s*\{\s*(max|min)\s*:\s*(-?\d+(?:\.\d+)?)\s*\}",
            line,
        )
        if grade_match and current_metric:
            grade = grade_match.group(1).lower()
            bound = grade_match.group(2).lower()
            value = float(grade_match.group(3))
            metrics.setdefault(current_metric, {})[f"grade_{grade}_{bound}"] = value
    return metrics


def _extract_score_blocks(text: str) -> Dict[str, int]:
    scores: Dict[str, int] = {}
    in_grade_decision = False
    for raw_line in text.splitlines():
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if indent == 0:
            in_grade_decision = line == "grade_decision:"
            continue
        if not in_grade_decision:
            continue
        match = re.match(r"(grade_[abcABC]_score):\s*(\d+)\s*$", line)
        if match:
            scores[match.group(1).lower()] = int(match.group(2))
    return scores


def _build_rule_set_from_yaml(path: Path, crop_name: str) -> Optional[CropRuleSet]:
    if not path.exists():
        return None
    blocks = _extract_rule_blocks(path.read_text(encoding="utf-8"))
    if not blocks:
        return None

    metrics: Dict[str, CropMetricRule] = {}
    for metric, values in blocks.items():
        direction = "max" if "grade_a_max" in values else "min"
        suffix = direction
        required = [f"grade_a_{suffix}", f"grade_b_{suffix}", f"grade_c_{suffix}"]
        if not all(key in values for key in required):
            continue
        metrics[metric] = CropMetricRule(
            name=metric,
            direction=direction,
            grade_a=float(values[required[0]]),
            grade_b=float(values[required[1]]),
            grade_c=float(values[required[2]]),
        )

    if not metrics:
        return None

    scores = _extract_score_blocks(path.read_text(encoding="utf-8"))
    return CropRuleSet(
        crop=crop_name,
        metrics=metrics,
        grade_a_score=scores.get("grade_a_score", 90),
        grade_b_score=scores.get("grade_b_score", 75),
        grade_c_score=scores.get("grade_c_score", 60),
    )


class CropRuleEngine:
    """Crop-aware deterministic threshold router backed by crop rule YAML files."""

    RULE_FILE_BY_CROP = {
        "finger_millets": "fingermillet_rules.yaml",
        "bajra": "bajari_rules.yaml",
        "rice": "rice_rules.yaml",
    }

    def __init__(self, rules_dir: Optional[str | Path] = None):
        repo_root = Path(__file__).resolve().parents[2]
        self.rules_dir = Path(rules_dir) if rules_dir else (
            repo_root / "docs" / "rag" / "crop_knowledge" / "grading_rules"
        )
        self._fallback = RagiRuleEngine()
        self._rule_sets: Dict[str, Optional[CropRuleSet]] = {}

    def _rule_set_for_crop(self, crop_type: Any) -> Optional[CropRuleSet]:
        crop = normalize_crop_name(crop_type)
        if not crop:
            return None
        if crop in self._rule_sets:
            return self._rule_sets[crop]
        filename = self.RULE_FILE_BY_CROP.get(crop)
        rule_set = (
            _build_rule_set_from_yaml(self.rules_dir / filename, crop)
            if filename
            else None
        )
        self._rule_sets[crop] = rule_set
        return rule_set

    def describe_crop_rules(self, crop_type: Any) -> List[str]:
        rule_set = self._rule_set_for_crop(crop_type)
        if not rule_set:
            return []
        return rule_set.describe()

    def _response_float(
        self,
        response_json: Dict[str, Any],
        keys: Iterable[str],
        default: Optional[float] = None,
    ) -> Optional[float]:
        for key in keys:
            if key in response_json and response_json.get(key) is not None:
                return _as_float(response_json.get(key), default if default is not None else 0.0)
        return default

    def _metric_value(
        self,
        metric: str,
        response_json: Dict[str, Any],
        physics_proxies: Dict[str, Any],
        moisture_percent: Optional[float],
    ) -> float:
        uniformity = _as_float(physics_proxies.get("uniformity_score"), 70.0)
        if metric == "moisture":
            return _as_float(moisture_percent, 0.0)
        if metric == "broken_grains":
            return self._response_float(
                response_json,
                ("broken_grains_percent", "broken_grain_percent"),
                0.0,
            ) or 0.0
        if metric == "damaged_grains":
            return self._response_float(
                response_json,
                ("damaged_grains_percent", "damaged_grain_percent"),
                0.0,
            ) or 0.0
        if metric == "chalky_grains":
            return self._response_float(
                response_json,
                ("chalky_grains_percent", "chalky_grain_percent", "off_tone_fraction"),
                0.0,
            ) or 0.0
        if metric == "foreign_matter":
            return self._response_float(
                response_json,
                ("foreign_matter_percent", "foreign_matter"),
                0.0,
            ) or 0.0
        if metric == "organic_extraneous_matter":
            return self._response_float(
                response_json,
                ("organic_extraneous_matter_percent", "organic_extraneous_matter"),
                self._response_float(response_json, ("foreign_matter_percent",), 0.0),
            ) or 0.0
        if metric == "inorganic_extraneous_matter":
            return self._response_float(
                response_json,
                ("inorganic_extraneous_matter_percent", "inorganic_extraneous_matter"),
                0.0,
            ) or 0.0
        if metric == "other_edible_grains":
            return self._response_float(
                response_json,
                ("other_edible_grains_percent", "other_edible_grains"),
                0.0,
            ) or 0.0
        if metric == "immature_grains":
            return self._response_float(
                response_json,
                ("immature_grains_percent", "immature_grains"),
                0.0,
            ) or 0.0
        if metric == "weevilled_grains":
            visible_defects = " ".join(_as_list(response_json.get("visible_defects"))).lower()
            default = 5.0 if any(term in visible_defects for term in ("weevil", "insect")) else 0.0
            return self._response_float(
                response_json,
                ("weevilled_grains_percent", "weevilled_grains"),
                default,
            ) or 0.0
        if metric == "color_uniformity":
            return self._response_float(
                response_json,
                ("color_uniformity_score",),
                self._response_float(response_json, ("off_tone_fraction",), None),
            ) if "color_uniformity_score" in response_json else (
                100.0 - _as_float(response_json.get("off_tone_fraction"), 100.0 - uniformity)
            )
        if metric == "size_uniformity":
            return self._response_float(
                response_json,
                ("size_uniformity_score",),
                100.0 - _as_float(response_json.get("size_deviation"), 100.0 - uniformity),
            ) or 0.0
        if metric == "shape_uniformity":
            return self._response_float(
                response_json,
                ("shape_uniformity_score",),
                100.0 - _as_float(response_json.get("shape_defect_fraction"), 100.0 - uniformity),
            ) or 0.0
        if metric == "surface_defects":
            return self._response_float(
                response_json,
                ("surface_defects_percent", "surface_defects", "shape_defect_fraction"),
                0.0,
            ) or 0.0
        return self._response_float(response_json, (f"{metric}_percent", metric), 0.0) or 0.0

    def _evaluate_crop_rules(
        self,
        rule_set: CropRuleSet,
        response_json: Dict[str, Any],
        physics_proxies: Dict[str, Any],
        moisture_risk: Any = None,
        moisture_percent: Optional[float] = None,
    ) -> RuleDecision:
        llm_grade = _grade_value(response_json.get("quality_grade", "B"))
        mold_visible = _as_bool(response_json.get("mold_visible", False))
        visible_defects = [item.lower() for item in _as_list(response_json.get("visible_defects"))]
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

        values: Dict[str, float] = {}
        metric_grades: Dict[str, str] = {}
        hard_reasons: List[str] = []
        grade_c_reasons: List[str] = []
        b_reasons: List[str] = []
        rule_hits: List[str] = []

        if visible_hazard:
            hard_reasons.append("Hard reject gate: visible mould, insect, stone, or deleterious material")
            rule_hits.extend(["hazard_gate", f"{rule_set.crop}_hazard_gate"])

        moisture_label = str(getattr(moisture_risk, "value", moisture_risk or "")).upper()
        for metric, rule in rule_set.metrics.items():
            value = self._metric_value(metric, response_json, physics_proxies, moisture_percent)
            values[metric] = value
            metric_grade = rule.grade_for_value(value)
            metric_grades[metric] = metric_grade

            if metric == "moisture" and not moisture_percent:
                if moisture_label == "CRITICAL":
                    metric_grade = "REJECT"
                elif moisture_label == "HIGH":
                    metric_grade = "C"
                elif moisture_label == "MODERATE":
                    metric_grade = "B"
                metric_grades[metric] = metric_grade

            if metric_grade == "REJECT":
                comparator = "below" if rule.direction == "min" else "exceeds"
                hard_reasons.append(
                    f"{metric.replace('_', ' ').title()} {value:.2f}% {comparator} Grade C threshold {rule.grade_c:.2f}"
                )
                rule_hits.extend([f"{metric}_reject", f"{rule_set.crop}_{metric}_reject"])
            elif metric_grade == "C":
                grade_c_reasons.append(f"{metric.replace('_', ' ').title()} is in Grade C range")
                rule_hits.extend([f"{metric}_c", f"{rule_set.crop}_{metric}_c"])
            elif metric_grade == "B":
                b_reasons.append(f"{metric.replace('_', ' ').title()} blocks Grade A")
                rule_hits.extend([f"{metric}_b", f"{rule_set.crop}_{metric}_b"])

        if moisture_label == "CRITICAL" and "moisture" not in rule_set.metrics:
            hard_reasons.append("Critical proxy moisture risk")
            rule_hits.append("moisture_reject")

        broken = values.get("broken_grains", _as_float(response_json.get("broken_grain_percent"), 0.0))
        foreign = values.get(
            "foreign_matter",
            values.get("organic_extraneous_matter", 0.0)
            + values.get("inorganic_extraneous_matter", 0.0),
        )
        uniformity_values = [
            values[key]
            for key in ("color_uniformity", "size_uniformity", "shape_uniformity")
            if key in values
        ]
        uniformity = (
            sum(uniformity_values) / len(uniformity_values)
            if uniformity_values
            else _as_float(physics_proxies.get("uniformity_score"), 70.0)
        )

        if hard_reasons:
            return RuleDecision(
                grade="C",
                score=25,
                reject=True,
                reject_reasons=list(dict.fromkeys(hard_reasons)),
                broken_grain=broken,
                foreign_matter=foreign,
                uniformity=min(uniformity, 35.0),
                mold_visible=mold_visible or visible_hazard,
                rule_hits=list(dict.fromkeys(rule_hits)),
            )

        if grade_c_reasons:
            return RuleDecision(
                grade="C",
                score=rule_set.grade_c_score,
                reject=bool("moisture_c" in rule_hits),
                reject_reasons=list(dict.fromkeys(grade_c_reasons)),
                broken_grain=broken,
                foreign_matter=foreign,
                uniformity=min(uniformity, 60.0),
                mold_visible=False,
                rule_hits=list(dict.fromkeys(rule_hits)),
            )

        clumping = _as_float(physics_proxies.get("clumping", {}).get("density"), 0.0)
        darkness = _as_float(physics_proxies.get("lab_features", {}).get("color_darkness_index"), 0.0)
        roughness = _as_float(physics_proxies.get("roughness_score"), 50.0)
        grain_coverage = _as_float(physics_proxies.get("grain_mask_coverage"), 0.5)
        proxy_grade_a_ok = (
            clumping < 0.12
            and darkness < 45
            and uniformity >= 72
            and roughness >= 20
            and grain_coverage >= 0.15
        )
        if llm_grade == "A" and proxy_grade_a_ok and not b_reasons:
            return RuleDecision(
                grade="A",
                score=rule_set.grade_a_score,
                reject=False,
                reject_reasons=[],
                broken_grain=broken,
                foreign_matter=foreign,
                uniformity=max(uniformity, 90.0),
                mold_visible=False,
                rule_hits=[f"{rule_set.crop}_grade_a_all_gates_pass"],
            )

        if llm_grade != "A":
            b_reasons.append("Lot is usable but not premium")
            rule_hits.append("visual_b")

        return RuleDecision(
            grade="B",
            score=rule_set.grade_b_score,
            reject=False,
            reject_reasons=[],
            broken_grain=broken,
            foreign_matter=foreign,
            uniformity=float(max(55.0, min(uniformity, 85.0))),
            mold_visible=False,
            rule_hits=list(dict.fromkeys(rule_hits or b_reasons)),
        )

    def evaluate(
        self,
        response_json: Dict[str, Any],
        physics_proxies: Dict[str, Any],
        moisture_risk: Any = None,
        moisture_percent: Optional[float] = None,
        moisture_calibrated: bool = True,
        crop_type: Any = None,
    ) -> RuleDecision:
        rule_set = self._rule_set_for_crop(crop_type)
        if rule_set:
            return self._evaluate_crop_rules(
                rule_set=rule_set,
                response_json=response_json,
                physics_proxies=physics_proxies,
                moisture_risk=moisture_risk,
                moisture_percent=moisture_percent,
            )
        return self._fallback.evaluate(
            response_json=response_json,
            physics_proxies=physics_proxies,
            moisture_risk=moisture_risk,
            moisture_percent=moisture_percent,
            moisture_calibrated=moisture_calibrated,
        )
