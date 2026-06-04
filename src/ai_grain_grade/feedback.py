"""Feedback storage utilities for cloud Qwen grading runs."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from numbers import Real
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

DEFAULT_FEEDBACK_DIR = Path(__file__).resolve().parents[2] / "data" / "feedback" / "feedback_data"


@dataclass
class GradingFeedbackItem:
    """Single operator correction captured by the Streamlit workflow."""

    sample_id: str
    image_path: str
    farm_id: str
    predicted_grade: str
    true_grade: str
    predicted_moisture_risk: str
    true_moisture_risk: str
    image_features: Dict[str, Any]
    confidence: float
    timestamp: str
    device_model: str
    batch_id: str = ""
    notes: str = ""


def flatten_feature_dict(data: Dict[str, Any], prefix: str = "") -> Dict[str, float]:
    """Flatten nested numeric image feature dictionaries for similarity lookup."""
    flat: Dict[str, float] = {}
    for key, value in (data or {}).items():
        joined = f"{prefix}_{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_feature_dict(value, joined))
        elif isinstance(value, Real) and not isinstance(value, bool):
            flat[joined] = float(value)
    return flat


class FeedbackCollector:
    """JSON-backed correction storage used by Streamlit and the Qwen prompt."""

    def __init__(self, storage_path: str | Path = DEFAULT_FEEDBACK_DIR):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def submit_feedback(self, feedback_item: GradingFeedbackItem) -> bool:
        try:
            timestamp = datetime.now(timezone.utc).timestamp()
            filename = self.storage_path / f"{feedback_item.sample_id}_{timestamp}.json"
            filename.write_text(
                json.dumps(asdict(feedback_item), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Feedback stored: %s", filename)
            return True
        except Exception as exc:
            logger.error("Failed to store feedback: %s", exc)
            return False

    def get_pending_count(self) -> int:
        return len(list(self.storage_path.glob("*.json")))

    def load_all_feedback(self) -> List[GradingFeedbackItem]:
        items: List[GradingFeedbackItem] = []
        for filepath in self.storage_path.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                items.append(GradingFeedbackItem(**data))
            except Exception as exc:
                logger.warning("Failed to load %s: %s", filepath, exc)
        return items

    def retrieve_similar_feedback(
        self,
        image_features: Dict[str, Any],
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        items = self.load_all_feedback()
        if not items:
            return []

        target = flatten_feature_dict(image_features)
        feature_keys = [
            "texture_entropy",
            "lab_features_color_darkness_index",
            "clumping_density",
            "roughness_score",
            "uniformity_score",
        ]
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for item in items:
            flat = flatten_feature_dict(item.image_features)
            distance = 0.0
            used = 0
            for key in feature_keys:
                if key not in target and key not in flat:
                    continue
                distance += abs(target.get(key, 0.0) - flat.get(key, 0.0))
                used += 1
            if used == 0:
                continue
            grade_changed = item.predicted_grade != item.true_grade
            moisture_changed = item.predicted_moisture_risk != item.true_moisture_risk
            score = distance / used
            scored.append(
                (
                    score,
                    {
                        "sample_id": item.sample_id,
                        "farm_id": item.farm_id,
                        "batch_id": item.batch_id,
                        "predicted_grade": item.predicted_grade,
                        "true_grade": item.true_grade,
                        "predicted_moisture_risk": item.predicted_moisture_risk,
                        "true_moisture_risk": item.true_moisture_risk,
                        "confidence": item.confidence,
                        "notes": item.notes,
                        "distance": round(score, 4),
                        "grade_changed": grade_changed,
                        "moisture_changed": moisture_changed,
                    },
                )
            )
        scored.sort(
            key=lambda pair: (
                pair[0],
                -int(pair[1]["grade_changed"]),
                -int(pair[1]["moisture_changed"]),
            )
        )
        return [item for _, item in scored[:limit]]

    def summarize_feedback_patterns(self, limit: int = 5) -> List[str]:
        transitions: Dict[str, int] = {}
        for item in self.load_all_feedback():
            key = f"{item.predicted_grade}->{item.true_grade}"
            transitions[key] = transitions.get(key, 0) + 1
        ranked = sorted(transitions.items(), key=lambda pair: pair[1], reverse=True)
        return [f"{transition} occurred {count} time(s)" for transition, count in ranked[:limit]]

    def check_review_threshold(self, threshold: int = 500) -> bool:
        """Return whether enough corrections exist for an external review job."""
        pending = self.get_pending_count()
        logger.info("Pending feedback: %d/%d", pending, threshold)
        return pending >= threshold
