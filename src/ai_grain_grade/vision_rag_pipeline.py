"""
Vision-RAG Pipeline for Ragi Quality Grading
==============================================

Two-pass inference engine:
  Pass 1: Safety-Gate Detection (Bounding boxes for hazards: mold, stones, insects)
  Pass 2: RAG-Guided Grading (Retrieve relevant BIS rules, output deterministic Grade)

Integrates:
  - Vector DB (Supabase/Pinecone) with .md grading rules
  - Qwen3-VL/Qwen-VL cloud OpenAI-compatible API for vision understanding
  - Local RAG chunking and retrieval over authoritative rules
  - Deterministic grading logic based on UNIFIED_RAGI_QUALITY_AND_MOISTURE_SPEC.md

Author: Copilot
Date: 2026-04-29
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Tuple, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import httpx
import numpy as np
from datetime import datetime
from pathlib import Path
from PIL import Image

# Our modules
from .paths import FEEDBACK_DIR, RAG_INDEX_PATH
from .rag_engine import RAGEngine
from .moisture_calibration import MoistureCalibrator
from .feedback import FeedbackCollector
from .rule_engine import RagiRuleEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


LEGACY_SILICONFLOW_MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"
DEFAULT_DASHSCOPE_MODEL = "qwen3-vl-plus"
DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
CLOUD_QWEN_PROVIDERS = {"dashscope", "siliconflow", "custom"}


class QualityGrade(str, Enum):
    """Canonical three-tier quality grading."""
    A = "A"
    B = "B"
    C = "C"


class MoistureRisk(str, Enum):
    """Moisture risk classification."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SafetyGateFinding:
    """Result of Pass 1: Safety Gate Detection."""
    hazard_detected: bool
    hazard_type: Optional[str]  # mold, stone, insect, webbing, foreign_matter
    confidence: float
    bounding_boxes: List[Dict[str, float]]  # {x, y, w, h} in normalized coords


@dataclass
class GradingResult:
    """Final grading output from Pass 2."""
    quality_grade: QualityGrade
    quality_score: int  # 0-100
    reject_recommended: bool
    reject_reasons: List[str]
    
    # Quality breakdown
    broken_grain_percent: float
    foreign_matter_percent: float
    uniformity_score: float
    mold_visible: bool
    
    # Moisture
    moisture_risk: MoistureRisk
    moisture_estimate_calibrated: bool
    moisture_percent_estimate: Optional[float]
    
    # Confidence
    overall_confidence: int  # 0-100
    pass1_confidence: int
    pass2_confidence: int
    
    # Audit metadata
    timestamp: str
    model_version: str
    rag_chunks_used: int
    operator_summary: str = ""
    manual_review_required: bool = False
    signal_highlights: List[str] = field(default_factory=list)


class VisionRAGPipeline:
    """
    End-to-end Vision + RAG pipeline for deterministic ragi grading.
    """

    def __init__(
        self,
        siliconflow_api_key: str = "",
        qwen_model: str = LEGACY_SILICONFLOW_MODEL,
        vector_db_type: str = "local",
        vector_db_url: Optional[str] = None,
        vector_db_key: Optional[str] = None,
        feedback_storage_path: Optional[str] = None,
        rag_retrieval_mode: str = "lexical",
        qwen_provider: Optional[str] = None,
        qwen_base_url: Optional[str] = None,
        qwen_api_key: Optional[str] = None,
        qwen_timeout_seconds: Optional[float] = None,
    ):
        """
        Args:
            siliconflow_api_key: Backward-compatible API key for SiliconFlow inference
            qwen_model: Model identifier
            vector_db_type: 'supabase', 'pinecone', or 'local' (JSON fallback)
            rag_retrieval_mode: 'lexical' for the lightweight local scorer.
            qwen_provider: 'dashscope', 'siliconflow', or 'custom'.
            qwen_base_url: OpenAI-compatible base URL for cloud providers.
            qwen_api_key: Cloud provider API key. Falls back to env vars.
            qwen_timeout_seconds: HTTP timeout for non-streaming cloud calls.
        """
        provider = (qwen_provider or os.getenv("QWEN_VL_PROVIDER") or "").strip().lower()
        if not provider:
            provider = "dashscope"
        if provider not in CLOUD_QWEN_PROVIDERS:
            logger.warning("Unknown Qwen provider %r; using custom OpenAI-compatible mode", provider)
            provider = "custom"

        env_model = os.getenv("QWEN_VL_MODEL")
        if env_model:
            qwen_model = env_model
        elif provider == "dashscope" and qwen_model == LEGACY_SILICONFLOW_MODEL:
            qwen_model = DEFAULT_DASHSCOPE_MODEL

        self.qwen_provider = provider
        self.qwen_model = qwen_model
        self.vector_db_type = vector_db_type
        self.vector_db_url = vector_db_url
        self.vector_db_key = vector_db_key
        self._last_message_meta: Dict[str, Any] = {}
        self._last_image_payload_meta: Dict[str, Any] = {}

        if provider == "dashscope":
            self.qwen_base_url = (
                qwen_base_url
                or _first_env(
                    "QWEN_VL_BASE_URL",
                    "DASHSCOPE_BASE_URL",
                    default=DEFAULT_DASHSCOPE_BASE_URL,
                )
            )
            self.qwen_api_key = (
                qwen_api_key
                or _first_env("QWEN_VL_API_KEY", "DASHSCOPE_API_KEY")
            )
        elif provider == "siliconflow":
            self.qwen_base_url = (
                qwen_base_url
                or _first_env(
                    "QWEN_VL_BASE_URL",
                    "SILICONFLOW_BASE_URL",
                    default=DEFAULT_SILICONFLOW_BASE_URL,
                )
            )
            self.qwen_api_key = (
                qwen_api_key
                or siliconflow_api_key
                or _first_env("QWEN_VL_API_KEY", "SILICONFLOW_API_KEY")
            )
        else:
            self.qwen_base_url = qwen_base_url or os.getenv("QWEN_VL_BASE_URL", "")
            self.qwen_api_key = qwen_api_key or os.getenv("QWEN_VL_API_KEY", "")

        self.qwen_timeout_seconds = float(
            qwen_timeout_seconds
            if qwen_timeout_seconds is not None
            else _env_float("QWEN_VL_TIMEOUT_SECONDS", 75.0)
        )
        self.siliconflow_key = self.qwen_api_key
        self.siliconflow_endpoint = (
            self.qwen_base_url if provider == "siliconflow" else DEFAULT_SILICONFLOW_BASE_URL
        )

        # Initialize Moisture Calibrator
        self.moisture_calibrator = MoistureCalibrator()
        self.rule_engine = RagiRuleEngine()

        # Initialize RAG Engine
        self.rag_engine = RAGEngine(
            index_path=str(RAG_INDEX_PATH),
            retrieval_mode=rag_retrieval_mode,
        )
        self.feedback_collector = FeedbackCollector(
            storage_path=str(feedback_storage_path or FEEDBACK_DIR)
        )
        
        # Initial indexing if empty or outdated
        if not self.rag_engine.chunks or self.rag_engine.needs_rebuild():
            self._init_rag_knowledge_base()

        logger.info("✓ Vision-RAG Pipeline initialized (%s/%s)", self.qwen_provider, self.qwen_model)

    def _init_rag_knowledge_base(self):
        """Load grading and moisture rules from the repository Markdown corpus."""
        self.rag_engine.index_documents()
        logger.info(f"✓ RAG knowledge base indexed with {len(self.rag_engine.chunks)} chunks")

    def warm_up_retrieval(self):
        """Warm the local lexical rule retriever before the user starts analysis."""
        try:
            self.rag_engine.retrieve(
                "FAO BIS ragi moisture foreign matter damaged grains thresholds",
                k=1,
            )
        except Exception as e:
            logger.warning("RAG warm-up skipped: %s", e)

    def _provider_label(self) -> str:
        return f"{self.qwen_provider}/{self.qwen_model}"

    def _chat_completions_endpoint(self) -> str:
        base = (self.qwen_base_url or "").rstrip("/")
        if not base:
            raise ValueError("Qwen cloud base URL is not configured")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    def _cloud_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.qwen_api_key:
            headers["Authorization"] = f"Bearer {self.qwen_api_key}"
        return headers

    def _extract_message_text(self, message: Dict[str, Any]) -> str:
        content = message.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(str(item.get("text", "")))
                elif isinstance(item, str):
                    text_parts.append(item)
            content = "\n".join(part for part in text_parts if part)
        if isinstance(content, str) and content.strip():
            return content
        return str(
            message.get("reasoning_content", "")
            or message.get("reasoning", "")
            or message.get("thinking", "")
        ).strip()

    def _openai_payload_options(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.qwen_provider in {"dashscope", "custom"}:
            payload["response_format"] = {"type": "json_object"}
        elif self.qwen_provider == "siliconflow":
            payload.update(
                {
                    "seed": 7,
                    "reasoning_effort": "none",
                    "reasoning": {"effort": "none"},
                }
            )
        return payload

    def infer(self, image_path: str, physics_proxies: Dict[str, Any]) -> GradingResult:
        """
        Two-pass inference pipeline.
        
        Args:
            image_path: Path to grain image
            physics_proxies: Dict from physics_proxies.extract_all_proxies()
            
        Returns:
            Complete GradingResult
        """
        timestamp = datetime.utcnow().isoformat()

        # PASS 1: Safety Gate Detection
        logger.info("PASS 1: Safety Gate Detection...")
        safety_finding = self._pass1_safety_gate(image_path)

        if safety_finding.hazard_detected:
            logger.warning(f"⚠ Safety hazard detected: {safety_finding.hazard_type}")
            # Immediate Grade C + reject
            return GradingResult(
                quality_grade=QualityGrade.C,
                quality_score=25,
                reject_recommended=True,
                reject_reasons=[f"Safety hazard detected: {safety_finding.hazard_type}"],
                broken_grain_percent=0.0,
                foreign_matter_percent=5.0,
                uniformity_score=30,
                mold_visible=(safety_finding.hazard_type == "mold"),
                moisture_risk=MoistureRisk.CRITICAL,
                moisture_estimate_calibrated=False,
                moisture_percent_estimate=None,
                overall_confidence=int(safety_finding.confidence * 100),
                pass1_confidence=int(safety_finding.confidence * 100),
                pass2_confidence=0,
                timestamp=timestamp,
                model_version="qwen2.5-vl-7b-v1",
                rag_chunks_used=0,
                operator_summary=f"Hold this lot. Safety gate flagged {safety_finding.hazard_type}.",
                manual_review_required=True,
                signal_highlights=[f"Safety gate detected {safety_finding.hazard_type}"],
            )

        # PASS 2: RAG-Guided Quality & Moisture Grading
        logger.info("PASS 2: RAG-Guided Grading...")
        grading_result = self._pass2_rag_grading(
            image_path, physics_proxies, timestamp
        )

        return grading_result

    def estimate_moisture_risk(
        self,
        physics_proxies: Dict[str, Any],
    ) -> Tuple[MoistureRisk, float, bool]:
        """Public read-only wrapper used by Streamlit to render proxy results before VLM inference."""
        return self._estimate_moisture_risk(physics_proxies)

    async def infer_async(
        self,
        image_path: str,
        physics_proxies: Dict[str, Any],
        stream_callback: Optional[Callable[[str], Any]] = None,
    ) -> GradingResult:
        """
        Async inference entrypoint for Streamlit.

        Streamlit still runs the script top-to-bottom; the cloud HTTP work is
        moved to a worker thread so the UI wrapper can remain async-friendly.
        """
        return await asyncio.to_thread(self.infer, image_path, physics_proxies)

    def _pass1_safety_gate(self, image_path: str) -> SafetyGateFinding:
        """
        Pass 1: Vision-based hazard detection.
        Uses Qwen-VL to identify: mold, stones, insects, webbing, excessive foreign matter.
        """
        try:
            # Prepare prompt for safety detection
            safety_prompt = """Analyze this ragi (finger millet) grain sample image for safety hazards.

Specifically look for:
1. Mold or fungal growth (white/gray patches, webbing)
2. Visible stones or rocks
3. Insect damage or presence
4. Foreign matter (sticks, chaff, debris)
5. Excessive grain clumping (indicates moisture/disease)

Respond in JSON format:
{
  "hazard_found": true/false,
  "hazard_type": "none" | "mold" | "stone" | "insect" | "webbing" | "foreign_matter",
  "confidence": 0.0-1.0,
  "description": "Brief explanation",
  "bounding_boxes": [{"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.2}]
}"""

            response = self._call_qwen_vision(image_path, safety_prompt, max_tokens=280)
            response_json = self._parse_json_response(response)

            hazard_detected = response_json.get("hazard_found", False)
            hazard_type = response_json.get("hazard_type", "none")
            confidence = response_json.get("confidence", 0.5)
            bboxes = response_json.get("bounding_boxes", [])

            if hazard_type == "none":
                hazard_type = None

            return SafetyGateFinding(
                hazard_detected=hazard_detected,
                hazard_type=hazard_type,
                confidence=confidence,
                bounding_boxes=bboxes,
            )

        except Exception as e:
            logger.error(f"Pass 1 failed: {e}. Assuming safe (low confidence).")
            return SafetyGateFinding(
                hazard_detected=False,
                hazard_type=None,
                confidence=0.3,  # Low confidence fallback
                bounding_boxes=[],
            )

    def _pass2_rag_grading(
        self, image_path: str, physics_proxies: Dict[str, Any], timestamp: str
    ) -> GradingResult:
        """
        Pass 2: RAG-guided quality and moisture grading.
        Retrieves relevant rules from vector DB, sends to Qwen-VL with context.
        """
        try:
            # 1. Retrieve relevant RAG chunks
            rag_context = self._retrieve_rag_context(physics_proxies)
            feedback_context = self._retrieve_feedback_context(physics_proxies)

            # 2. Build comprehensive grading prompt
            grading_prompt = self._build_grading_prompt(
                physics_proxies, rag_context, feedback_context
            )

            # 3. Call Qwen-VL with image and prompt
            response = self._call_qwen_vision(
                image_path,
                grading_prompt,
                max_tokens=260,
                physics_proxies=physics_proxies,
            )
            response_json = self._parse_json_response(response)
            if not response_json:
                repair_source = (
                    str(self._last_message_meta.get("content") or "").strip()
                    or str(self._last_message_meta.get("reasoning") or "").strip()
                    or str(response).strip()
                )
                response_json = self._repair_grading_json(repair_source, physics_proxies)
                if not response_json:
                    response_json = self._extract_grading_hints_from_text(
                        repair_source, physics_proxies
                    )

            # 4. Compute moisture risk and calibrated percentage from physics proxies
            moisture_risk, moisture_percent, is_calib = self._estimate_moisture_risk(physics_proxies)

            # 5. Parse response and apply deterministic threshold rules
            grade = self._apply_grading_logic(
                response_json,
                physics_proxies,
                moisture_risk=moisture_risk,
                moisture_percent=moisture_percent,
                moisture_calibrated=is_calib,
            )

            # 6. Compute confidence score
            overall_conf = self._compute_confidence(
                response_json, physics_proxies, rag_context
            )
            reject_reasons = list(grade["reject_reasons"])
            reject_recommended = bool(grade["reject"])
            if moisture_risk == MoistureRisk.CRITICAL:
                reject_recommended = True
                reject_reasons.append("Critical moisture risk; dry immediately before storage")
            elif moisture_risk == MoistureRisk.HIGH and grade["grade"] == QualityGrade.C:
                reject_recommended = True
                reject_reasons.append("High moisture plus low-quality evidence; hold before storage")

            signal_highlights = self._summarize_signals(physics_proxies, moisture_risk)
            operator_summary = self._build_operator_summary(
                grade["grade"],
                moisture_risk,
                reject_recommended,
                overall_conf,
                reject_reasons,
            )
            manual_review_required = (
                reject_recommended
                or overall_conf < 65
                or moisture_risk in {MoistureRisk.HIGH, MoistureRisk.CRITICAL}
            )

            return GradingResult(
                quality_grade=grade["grade"],
                quality_score=grade["score"],
                reject_recommended=reject_recommended,
                reject_reasons=list(dict.fromkeys(reject_reasons)),
                broken_grain_percent=grade.get("broken_grain", 0.0),
                foreign_matter_percent=grade.get("foreign_matter", 0.0),
                uniformity_score=grade.get("uniformity", 70.0),
                mold_visible=grade.get("mold_visible", False),
                moisture_risk=moisture_risk,
                moisture_estimate_calibrated=is_calib,
                moisture_percent_estimate=moisture_percent,
                overall_confidence=overall_conf,
                pass1_confidence=100,  # Passed safety gate
                pass2_confidence=min(100, int(response_json.get("model_confidence", 70))),
                timestamp=timestamp,
                model_version=self._provider_label(),
                rag_chunks_used=len(rag_context),
                operator_summary=operator_summary,
                manual_review_required=manual_review_required,
                signal_highlights=signal_highlights,
            )

        except Exception as e:
            logger.error(f"Pass 2 failed: {e}")
            # Fallback to conservative grading based on physics proxies alone
            return self._fallback_grading(physics_proxies, timestamp)

    def _build_rag_query(self, physics_proxies: Dict[str, Any]) -> str:
        """Create a retrieval query that reflects the current sample signals."""
        query_parts = [
            "FAO BIS ragi finger millet grading thresholds",
            "quality grade a b c decision matrix",
            "moisture foreign matter damaged grains procurement ranges",
            "biological hazard mold insect weevil foreign matter reject",
        ]

        clumping = physics_proxies.get("clumping", {}).get("density", 0.0)
        darkness = physics_proxies.get("lab_features", {}).get("color_darkness_index", 0.0)
        entropy = physics_proxies.get("texture_entropy", 0.0)
        uniformity = physics_proxies.get("uniformity_score", 0.0)
        roughness = physics_proxies.get("roughness_score", 0.0)
        physical = physics_proxies.get("physical_properties", {}) or {}

        if clumping > 0.18 or darkness > 48 or entropy < 3.0:
            query_parts.append("moisture risk clumping darkness calibration")
        if uniformity < 70:
            query_parts.append("bimodal color off-tone grade c")
        if roughness < 30:
            query_parts.append("storage dullness smooth surface downgrade")
        if physical.get("size_class") in {"small", "large", "mixed"}:
            query_parts.append("grain size variation broken shrivelled immature damaged grains")
        if physical.get("reflectiveness_class") in {"dull", "high_shine"}:
            query_parts.append("surface reflectance shine dullness moisture optical proxy")
        if physics_proxies.get("grain_mask_coverage", 0.0) < 0.15:
            query_parts.append("image validation reject retake low coverage")

        return " ".join(query_parts)

    def _retrieve_rag_context(self, physics_proxies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve authoritative chunks relevant to the sample's proxy profile."""
        query = self._build_rag_query(physics_proxies)
        return self.rag_engine.retrieve(query, k=4)

    def _retrieve_feedback_context(self, physics_proxies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch similar human corrections so feedback helps before the next retrain."""
        return self.feedback_collector.retrieve_similar_feedback(
            physics_proxies,
            limit=3,
        )

    def _build_grading_prompt(
        self,
        physics_proxies: Dict[str, Any],
        rag_context: List[Dict[str, Any]],
        feedback_context: List[Dict[str, Any]],
    ) -> str:
        """Build comprehensive grading prompt with physics context and RAG rules."""
        context_str = self._compress_rag_context(rag_context)
        feedback_str = self._feedback_examples_to_text(feedback_context)

        prompt = f"""Grade this finger millet batch. Return ONLY one JSON object with no prose.

Rules:
- Apply FAO/BIS-aligned ragi thresholds from the retrieved rule anchors.
- Hazard, mold, or foreign matter above 1.0% => Grade C/reject.
- Moisture, foreign matter, and damaged grain thresholds override the image model.
- Grade A only if the lot is very uniform, clean, and physics signals are dry/stable.
- If the batch looks mixed, bimodal, or moisture-heavy, prefer Grade C.
- Grade B is only for usable commercial lots without strong hazard or moisture signals.

Rule anchors:
{context_str}

Similar corrections:
{feedback_str}

Signals:
- darkness_index={physics_proxies['lab_features']['color_darkness_index']:.1f}
- clumping_density={physics_proxies['clumping']['density']:.3f}
- uniformity_score={physics_proxies['uniformity_score']:.1f}
- texture_entropy={physics_proxies['texture_entropy']:.2f}
- roughness_score={physics_proxies['roughness_score']:.1f}
- mask_coverage={physics_proxies['grain_mask_coverage']:.2%}

JSON schema:
{{
  "quality_grade": "A|B|C",
  "quality_score": 0-100,
  "off_tone_fraction": 0-100,
  "size_deviation": 0-100,
  "shape_defect_fraction": 0-100,
  "broken_grain_percent": 0-100,
  "foreign_matter_percent": 0-100,
  "other_edible_grains_percent": 0-100,
  "bimodal_color_detected": true,
  "mold_visible": false,
  "visible_defects": ["short labels"],
  "model_confidence": 0-100,
  "brief_reason": "one sentence"
}}"""

        return prompt

    def _feedback_examples_to_text(self, feedback_context: List[Dict[str, Any]]) -> str:
        if not feedback_context:
            return "- No similar corrected samples are available yet."

        lines = []
        for item in feedback_context:
            correction_note = (
                item["notes"].strip()
                if item.get("notes")
                else "No operator note provided."
            )
            lines.append(
                (
                    f"- Sample {item['sample_id']}: model predicted {item['predicted_grade']} "
                    f"but human corrected to {item['true_grade']} "
                    f"(moisture {item['predicted_moisture_risk']} -> {item['true_moisture_risk']}, "
                    f"distance {item['distance']}). Note: {correction_note}"
                )
            )
        return "\n".join(lines)

    def _compress_rag_context(self, rag_context: List[Dict[str, Any]], max_chars: int = 900) -> str:
        """Condense retrieved rules so cloud model output budget is spent on JSON."""
        if not rag_context:
            return "- No retrieved rules available."

        lines: List[str] = []
        used = 0
        for chunk in rag_context:
            title = str(chunk.get("title", "Rule")).strip()
            content = " ".join(str(chunk.get("content", "")).split())
            if not content:
                continue
            snippet = content[:180].rstrip(" ,.;:")
            line = f"- {title}: {snippet}"
            used += len(line)
            if used > max_chars and lines:
                break
            lines.append(line)
        return "\n".join(lines) if lines else "- No retrieved rules available."

    def _call_text_model(self, prompt: str, max_tokens: int = 180) -> str:
        """Run a compact text-only repair pass against the same model endpoint."""
        try:
            endpoint = self._chat_completions_endpoint()
            headers = self._cloud_headers()

            payload = {
                "model": self.qwen_model,
                "messages": [
                    {"role": "system", "content": "Return only strict JSON. No reasoning."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            }
            payload = self._openai_payload_options(payload)

            with httpx.Client(timeout=self.qwen_timeout_seconds) as client:
                response = client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()

            message = response.json()["choices"][0]["message"]
            return self._extract_message_text(message)
        except Exception as e:
            logger.error(f"Text repair call failed: {e}")
            return ""

    def _prepare_image_payload(
        self,
        image_path: str,
        physics_proxies: Optional[Dict[str, Any]] = None,
        max_side: int = 1280,
        jpeg_quality: int = 95,
    ) -> Tuple[str, str]:
        """
        Crop to the calibrated sample field and preserve high image quality.
        """
        import base64
        import io

        image = Image.open(image_path).convert("RGB")
        original_size = image.size
        crop_source = "full"
        sample_field = (physics_proxies or {}).get("sample_field", {}) if physics_proxies else {}
        bbox = sample_field.get("bbox") if isinstance(sample_field, dict) else None
        if bbox and len(bbox) == 4:
            x, y, w, h = [int(v) for v in bbox]
            pad = int(max(w, h) * 0.08)
            left = max(0, x - pad)
            top = max(0, y - pad)
            right = min(image.width, x + w + pad)
            bottom = min(image.height, y + h + pad)
            if right > left and bottom > top:
                image = image.crop((left, top, right, bottom))
                crop_source = str(sample_field.get("source", "sample-field"))

        if max(image.size) > max_side:
            image.thumbnail((max_side, max_side))

        buffer = io.BytesIO()
        image.save(
            buffer,
            format="JPEG",
            quality=jpeg_quality,
            optimize=True,
            subsampling=0,
        )
        self._last_image_payload_meta = {
            "original_size": original_size,
            "sent_size": image.size,
            "crop_source": crop_source,
            "jpeg_quality": jpeg_quality,
        }
        payload = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return payload, "image/jpeg"

    async def _emit_stream_update(
        self,
        stream_callback: Callable[[str], Any],
        text: str,
    ) -> None:
        """Invoke a Streamlit placeholder callback without assuming it is sync or async."""
        result = stream_callback(text)
        if inspect.isawaitable(result):
            await result
        await asyncio.sleep(0)

    async def _emit_grading_result_update(
        self,
        stream_callback: Optional[Callable[[str], Any]],
        grading_result: GradingResult,
        status: str,
        detail: Optional[str] = None,
    ) -> None:
        """Send a final structured decision snapshot to Streamlit's live JSON block."""
        if stream_callback is None:
            return
        payload: Dict[str, Any] = {
            "status": status,
            "grade": grading_result.quality_grade.value,
            "quality_score": grading_result.quality_score,
            "moisture_risk": grading_result.moisture_risk.value,
            "moisture_percent": grading_result.moisture_percent_estimate,
            "confidence": grading_result.overall_confidence,
            "reject_recommended": grading_result.reject_recommended,
            "reject_reasons": grading_result.reject_reasons,
            "model_version": grading_result.model_version,
            "decision_summary": grading_result.operator_summary,
            "signals": grading_result.signal_highlights,
        }
        if detail:
            payload["detail"] = detail
        await self._emit_stream_update(stream_callback, json.dumps(payload, indent=2))

    def _call_qwen_vision(
        self,
        image_path: str,
        prompt: str,
        max_tokens: int = 500,
        physics_proxies: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Call Qwen-VL through the configured cloud OpenAI-compatible provider.
        """
        try:
            image_data, image_type = self._prepare_image_payload(
                image_path,
                physics_proxies=physics_proxies,
            )

            # Prepare API request
            endpoint = self._chat_completions_endpoint()
            headers = self._cloud_headers()

            payload = {
                "model": self.qwen_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "/no_think Return only the final JSON object. Do not include <think>, markdown, notes, or prose.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_type};base64,{image_data}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,  # Low temperature for deterministic output
                "top_p": 0.8,
                "stream": False,
            }
            payload = self._openai_payload_options(payload)
            # Call API
            with httpx.Client(timeout=self.qwen_timeout_seconds) as client:
                response = client.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

            result = response.json()
            choice = result["choices"][0]
            message = choice["message"]
            self._last_message_meta = {
                "content": message.get("content", ""),
                "reasoning": message.get("reasoning_content", "") or message.get("reasoning", ""),
                "finish_reason": choice.get("finish_reason", ""),
            }
            final_text = self._extract_message_text(message)

            logger.info("✓ Inference succeeded (%s)", self.qwen_provider)
            return final_text

        except Exception as e:
            logger.error(f"Qwen-VL API call failed ({self.qwen_provider}): {e}")
            raise

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text."""
        try:
            import re
            if isinstance(response, dict):
                return response
            text = str(response or "").strip()
            if not text:
                return {}
            text = text.replace("```json", "```").replace("```JSON", "```")
            fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
            if fenced:
                for block in fenced:
                    block = block.strip()
                    if not block:
                        continue
                    try:
                        return json.loads(block)
                    except json.JSONDecodeError:
                        pass
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in response. Returning empty dict.")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {}

    def _repair_grading_json(
        self,
        raw_text: str,
        physics_proxies: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Convert empty or reasoning-heavy model output into the compact grading schema."""
        if not raw_text:
            return {}
        repair_prompt = f"""Convert these model notes into strict JSON only.

Required keys:
quality_grade, quality_score, off_tone_fraction, size_deviation,
shape_defect_fraction, broken_grain_percent, foreign_matter_percent,
other_edible_grains_percent, bimodal_color_detected, mold_visible,
visible_defects, model_confidence, brief_reason

Use conservative values if uncertain.
Signals: darkness_index={physics_proxies['lab_features']['color_darkness_index']:.1f}, clumping_density={physics_proxies['clumping']['density']:.3f}, uniformity_score={physics_proxies['uniformity_score']:.1f}, texture_entropy={physics_proxies['texture_entropy']:.2f}

Notes:
{raw_text[:2200]}"""
        repaired = self._call_text_model(repair_prompt, max_tokens=220)
        return self._parse_json_response(repaired)

    def _extract_grading_hints_from_text(
        self,
        raw_text: str,
        physics_proxies: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Heuristic backup when the cloud model returns reasoning text without final JSON."""
        text = str(raw_text or "").lower()
        if not text:
            return {}
        if not any(ch.isalpha() for ch in text):
            return {}

        grade = "B"
        if "grade c" in text or "→ grade c" in text or "grade=c" in text:
            grade = "C"
        elif "grade a" in text or "→ grade a" in text or "grade=a" in text:
            grade = "A"

        visible_defects: List[str] = []
        for defect in ("mold", "stone", "insect", "webbing", "clumping", "shriveled", "mixed"):
            if defect in text:
                visible_defects.append(defect)

        bimodal = "bimodal" in text or "mixed batch" in text or "two clearly distinct tones" in text
        mold_visible = "mold" in text and "no mold" not in text
        foreign_matter = 4.0 if ("foreign matter >1" in text or "stones" in text or "debris" in text) else 0.5

        clumping = float(physics_proxies.get("clumping", {}).get("density", 0.0))
        darkness = float(
            physics_proxies.get("lab_features", {}).get("color_darkness_index", 0.0)
        )
        uniformity = float(physics_proxies.get("uniformity_score", 70.0))

        off_tone = 14.0 if bimodal or uniformity < 68 else 6.0
        size_dev = 16.0 if grade == "C" else 7.0
        shape_defect = 12.0 if clumping > 0.18 or darkness > 50 else 4.0

        return {
            "quality_grade": grade,
            "quality_score": 55 if grade == "C" else 75 if grade == "B" else 90,
            "off_tone_fraction": off_tone,
            "size_deviation": size_dev,
            "shape_defect_fraction": shape_defect,
            "broken_grain_percent": 6.0 if grade == "C" else 2.0,
            "foreign_matter_percent": foreign_matter,
            "other_edible_grains_percent": 0.0,
            "bimodal_color_detected": bimodal,
            "mold_visible": mold_visible,
            "visible_defects": visible_defects,
            "model_confidence": 68 if grade == "C" else 72,
            "brief_reason": "Recovered from model reasoning text after empty structured output.",
        }

    def _apply_grading_logic(
        self,
        response_json: Dict[str, Any],
        physics_proxies: Dict[str, Any],
        moisture_risk: Optional[MoistureRisk] = None,
        moisture_percent: Optional[float] = None,
        moisture_calibrated: bool = True,
    ) -> Dict[str, Any]:
        """Apply deterministic FAO/BIS-aligned threshold rules."""
        decision = self.rule_engine.evaluate(
            response_json=response_json,
            physics_proxies=physics_proxies,
            moisture_risk=moisture_risk,
            moisture_percent=moisture_percent,
            moisture_calibrated=moisture_calibrated,
        )
        return {
            "grade": QualityGrade(decision.grade),
            "score": decision.score,
            "reject": decision.reject,
            "reject_reasons": decision.reject_reasons,
            "broken_grain": decision.broken_grain,
            "foreign_matter": decision.foreign_matter,
            "uniformity": decision.uniformity,
            "mold_visible": decision.mold_visible,
            "rule_hits": decision.rule_hits,
        }

    def _estimate_moisture_risk(self, physics_proxies: Dict[str, Any]) -> Tuple[MoistureRisk, float, bool]:
        """
        Estimate moisture risk from physics proxy signals.
        Thresholds based on UNIFIED_RAGI_QUALITY_AND_MOISTURE_SPEC.md
        """

        # Extract signals
        darkness_idx = physics_proxies["lab_features"]["color_darkness_index"]
        clumping = physics_proxies["clumping"]["density"]
        entropy = physics_proxies["texture_entropy"]
        calibration = physics_proxies.get("calibration", {}) or {}
        calibrated_geometry = physics_proxies.get("calibrated_geometry", {}) or {}
        physical = physics_proxies.get("physical_properties", {}) or {}
        calibration_available = bool(calibration.get("available")) and bool(calibration.get("mm_per_pixel"))

        # Composite moisture score (0-100)
        moisture_score = 0.0
        moisture_score += min(100, darkness_idx)  # Darkness: 0-100
        moisture_score += clumping * 200.0  # Clumping: 0-100
        moisture_score += max(0, 40 - entropy) * 5  # Low entropy: 0-100
        moisture_score /= 3.0

        if calibration_available:
            fill_ratio = float(calibrated_geometry.get("grain_fill_ratio") or physics_proxies.get("grain_mask_coverage", 0.0))
            clump_mm = float(calibrated_geometry.get("clump_equiv_diameter_mm") or 0.0)
            median_mm = float(calibrated_geometry.get("median_equiv_diameter_mm") or 0.0)
            grain_density = float(calibrated_geometry.get("grain_density_per_cm2") or 0.0)

            moisture_score += float(np.clip((fill_ratio - 0.35) * 90.0, -6.0, 14.0))
            moisture_score += float(np.clip((clump_mm - 2.1) * 5.5, 0.0, 16.0))
            if grain_density > 0.0:
                moisture_score += float(np.clip((35.0 - grain_density) * 0.08, -4.0, 6.0))
            if median_mm > 0.0:
                moisture_score += float(np.clip((2.0 - abs(median_mm - 1.45)) * 2.0, -1.5, 2.5))

        reflectiveness_class = str(physical.get("reflectiveness_class") or "")
        dark_fraction = float(physical.get("dark_fraction") or 0.0)
        highlight_fraction = float(physical.get("highlight_fraction") or 0.0)
        if reflectiveness_class == "dull" and dark_fraction > 0.30:
            moisture_score += float(np.clip(dark_fraction * 12.0, 0.0, 8.0))
        if highlight_fraction > 0.25:
            moisture_score += 2.0

        # Map to calibrated moisture percentage
        moisture_percent = self.moisture_calibrator.calibrate(moisture_score)
        is_calibrated = self.moisture_calibrator.get_is_calibrated() and calibration_available

        # Map to risk categories
        if moisture_score <= 30:
            risk = MoistureRisk.LOW
        elif moisture_score <= 50:
            risk = MoistureRisk.MODERATE
        elif moisture_score <= 70:
            risk = MoistureRisk.HIGH
        else:
            risk = MoistureRisk.CRITICAL
            
        return risk, moisture_percent, is_calibrated

    def _compute_confidence(
        self,
        response_json: Dict[str, Any],
        physics_proxies: Dict[str, Any],
        rag_context: List[Dict[str, Any]],
    ) -> int:
        """Compute overall confidence (0-100) from model, image, and evidence consistency."""

        model_conf = float(response_json.get("model_confidence", 70))
        grade = str(response_json.get("quality_grade", "B")).upper()
        grain_coverage = float(physics_proxies.get("grain_mask_coverage", 0.5))
        uniformity = float(physics_proxies.get("uniformity_score", 70.0))
        clumping = float(physics_proxies.get("clumping", {}).get("density", 0.0))
        darkness = float(
            physics_proxies.get("lab_features", {}).get("color_darkness_index", 0.0)
        )
        calibration_conf = float(physics_proxies.get("calibration", {}).get("grid_confidence", 0.0))

        image_quality = np.clip((grain_coverage * 140.0) + (uniformity * 0.4), 0, 100)
        rag_support = np.clip(
            sum(chunk.get("retrieval_score", 0.0) for chunk in rag_context) * 6.5,
            0,
            100,
        )

        if grade == "A":
            proxy_consistency = 95 if clumping < 0.12 and darkness < 45 and uniformity >= 72 else 45
        elif grade == "B":
            proxy_consistency = 85 if clumping < 0.22 and uniformity >= 60 else 55
        else:
            proxy_consistency = 90 if clumping > 0.18 or darkness > 50 or uniformity < 68 else 60

        overall = (
            0.45 * model_conf
            + 0.20 * image_quality
            + 0.20 * proxy_consistency
            + 0.15 * rag_support
        )
        if calibration_conf > 0:
            overall += 0.05 * (calibration_conf * 100.0)
        return int(np.clip(overall, 0, 100))

    def _fallback_grading(
        self, physics_proxies: Dict[str, Any], timestamp: str
    ) -> GradingResult:
        """Fallback grading when LLM inference fails."""

        # Conservative rules based on physics proxies alone
        darkness = physics_proxies["lab_features"]["color_darkness_index"]
        clumping = physics_proxies["clumping"]["density"]
        uniformity = physics_proxies.get("uniformity_score", 70.0)
        roughness = physics_proxies.get("roughness_score", 50.0)

        if darkness > 60 or clumping > 0.3 or uniformity < 55:
            grade = QualityGrade.C
            score = 40
        elif darkness < 42 and clumping < 0.1 and uniformity > 78 and roughness > 20:
            grade = QualityGrade.A
            score = 82
        else:
            grade = QualityGrade.B
            score = 65

        moisture_risk, moisture_percent, is_calib = self._estimate_moisture_risk(physics_proxies)
        signal_highlights = self._summarize_signals(physics_proxies, moisture_risk)
        signal_highlights = list(
            dict.fromkeys(
                [
                    "Qwen-VL unavailable; deterministic proxy fallback used",
                    *signal_highlights,
                ]
            )
        )
        reject_reasons: List[str] = []
        reject_recommended = False
        if moisture_risk == MoistureRisk.CRITICAL:
            reject_recommended = True
            reject_reasons.append("Critical moisture risk; dry immediately before storage")
        elif moisture_risk == MoistureRisk.HIGH and grade == QualityGrade.C:
            reject_recommended = True
            reject_reasons.append("High moisture plus low-quality proxy evidence; hold before storage")
        elif grade == QualityGrade.C:
            reject_reasons.extend(
                self._build_proxy_fastpath_reasons(
                    physics_proxies=physics_proxies,
                    moisture_risk=moisture_risk,
                )
            )
        operator_summary = self._build_operator_summary(
            grade,
            moisture_risk,
            reject_recommended,
            40,
            reject_reasons,
        )

        return GradingResult(
            quality_grade=grade,
            quality_score=score,
            reject_recommended=reject_recommended,
            reject_reasons=list(dict.fromkeys(reject_reasons)),
            broken_grain_percent=2.0,
            foreign_matter_percent=1.0,
            uniformity_score=60.0,
            mold_visible=False,
            moisture_risk=moisture_risk,
            moisture_estimate_calibrated=is_calib,
            moisture_percent_estimate=moisture_percent,
            overall_confidence=40,
            pass1_confidence=100,
            pass2_confidence=30,
            timestamp=timestamp,
            model_version=f"{self.qwen_model}-fallback",
            rag_chunks_used=0,
            operator_summary=operator_summary,
            manual_review_required=True,
            signal_highlights=signal_highlights,
        )

    def _summarize_signals(
        self,
        physics_proxies: Dict[str, Any],
        moisture_risk: MoistureRisk,
    ) -> List[str]:
        """Produce a short operator-facing summary of the strongest signals."""
        darkness = float(physics_proxies.get("lab_features", {}).get("color_darkness_index", 0.0))
        clumping = float(physics_proxies.get("clumping", {}).get("density", 0.0))
        uniformity = float(physics_proxies.get("uniformity_score", 0.0))
        entropy = float(physics_proxies.get("texture_entropy", 0.0))
        physical = physics_proxies.get("physical_properties", {}) or {}
        highlights: List[str] = [f"Moisture risk: {moisture_risk.value}"]
        if clumping > 0.18:
            highlights.append(f"Clumping is elevated ({clumping:.3f})")
        if darkness > 50:
            highlights.append(f"Darkness index is high ({darkness:.1f})")
        if uniformity < 68:
            highlights.append(f"Uniformity is weak ({uniformity:.1f}/100)")
        if entropy < 3.0:
            highlights.append(f"Texture entropy is low ({entropy:.2f})")
        if physical.get("size_class") in {"small", "large", "mixed"}:
            highlights.append(
                f"Grain size is {physical.get('size_class')} "
                f"(median {float(physical.get('median_diameter_mm') or 0.0):.2f} mm)"
            )
        if physical.get("reflectiveness_class") in {"dull", "high_shine"}:
            highlights.append(
                f"Reflectiveness is {physical.get('reflectiveness_class')} "
                f"({float(physical.get('reflectiveness_index') or 0.0):.1f}/100)"
            )
        return highlights

    def _build_proxy_fastpath_reasons(
        self,
        physics_proxies: Dict[str, Any],
        moisture_risk: MoistureRisk,
    ) -> List[str]:
        """Build non-generic reasons for deterministic proxy-only holds."""
        darkness = float(
            physics_proxies.get("lab_features", {}).get("color_darkness_index", 0.0)
        )
        clumping = float(physics_proxies.get("clumping", {}).get("density", 0.0))
        uniformity = float(physics_proxies.get("uniformity_score", 70.0))
        entropy = float(physics_proxies.get("texture_entropy", 10.0))

        reasons: List[str] = []
        if darkness >= 60:
            reasons.append(f"Darkness index {darkness:.1f} is above the dry-lot range")
        if clumping >= 0.16:
            reasons.append(f"Clumping density {clumping:.3f} suggests moisture-linked aggregation")
        if uniformity <= 52:
            reasons.append(f"Uniformity {uniformity:.1f}/100 indicates a mixed or unstable lot")
        if entropy <= 3.0:
            reasons.append(f"Texture entropy {entropy:.2f} is consistent with a smoother, wetter grain surface")
        if not reasons:
            reasons.append(f"Proxy evidence points to a {moisture_risk.value.lower()} moisture-risk lot")
        return reasons

    def _score_proxy_fastpath(
        self,
        physics_proxies: Dict[str, Any],
        moisture_risk: MoistureRisk,
    ) -> int:
        """Compute a more meaningful quality score for proxy-only decisions."""
        darkness = float(
            physics_proxies.get("lab_features", {}).get("color_darkness_index", 0.0)
        )
        clumping = float(physics_proxies.get("clumping", {}).get("density", 0.0))
        uniformity = float(physics_proxies.get("uniformity_score", 70.0))
        entropy = float(physics_proxies.get("texture_entropy", 10.0))

        score = 76.0
        score -= max(0.0, darkness - 50.0) * 1.1
        score -= max(0.0, 62.0 - uniformity) * 1.0
        score -= max(0.0, 3.2 - entropy) * 12.0
        score -= max(0.0, clumping - 0.10) * 110.0
        if moisture_risk == MoistureRisk.CRITICAL:
            score -= 6.0
        elif moisture_risk == MoistureRisk.HIGH:
            score -= 4.0
        return int(np.clip(round(score), 22, 56))

    def _build_operator_summary(
        self,
        grade: QualityGrade,
        moisture_risk: MoistureRisk,
        reject_recommended: bool,
        overall_confidence: int,
        reject_reasons: List[str],
    ) -> str:
        """Create a concise action sentence for the UI."""
        if reject_recommended:
            if reject_reasons:
                reason = "; ".join(reject_reasons[:2])
            else:
                reason = "risk signals are too strong"
            return f"Hold this batch. {reason}."
        if moisture_risk == MoistureRisk.CRITICAL:
            return "Dry this batch immediately and recheck before storage."
        if moisture_risk == MoistureRisk.HIGH:
            return "Dry this batch before storage and confirm with operator review."
        if grade == QualityGrade.A and overall_confidence >= 75:
            return "This lot looks strong for direct food-grade handling."
        if grade == QualityGrade.B:
            return "This lot is usable, but not premium. Keep routine storage checks in place."
        if grade == QualityGrade.C:
            return "This lot is low grade and should be reworked, dried, or manually reviewed."
        return "Review this lot with an operator before release."

    def format_result_for_api(self, grading_result: GradingResult) -> Dict[str, Any]:
        """Format GradingResult for JSON API response."""
        return {
            "quality": {
                "grade": grading_result.quality_grade.value,
                "score": grading_result.quality_score,
                "reject_recommended": grading_result.reject_recommended,
                "reject_reasons": grading_result.reject_reasons,
                "broken_grain_percent": grading_result.broken_grain_percent,
                "foreign_matter_percent": grading_result.foreign_matter_percent,
                "uniformity_score": grading_result.uniformity_score,
                "mold_visible": grading_result.mold_visible,
            },
            "moisture": {
                "risk_level": grading_result.moisture_risk.value,
                "percent_estimate": grading_result.moisture_percent_estimate,
                "calibrated": grading_result.moisture_estimate_calibrated,
            },
            "confidence": {
                "overall": grading_result.overall_confidence,
                "pass1_safety_gate": grading_result.pass1_confidence,
                "pass2_grading": grading_result.pass2_confidence,
            },
            "audit": {
                "timestamp": grading_result.timestamp,
                "model_version": grading_result.model_version,
                "rag_chunks_used": grading_result.rag_chunks_used,
            },
        }


# Minimal test
if __name__ == "__main__":
    import os

    api_key = os.getenv("SILICONFLOW_API_KEY", "your-key-here")

    # This would require a real image path and physics proxies
    pipeline = VisionRAGPipeline(siliconflow_api_key=api_key)
    print("✓ Vision-RAG Pipeline ready")
