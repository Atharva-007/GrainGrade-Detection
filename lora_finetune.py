"""
Qwen3-VL QLoRA Fine-Tuning for Ragi Grain Grading
=================================================

Standalone PEFT trainer for local active-learning loops:
  - Reads human-corrected JSON feedback from feedback_data/
  - Supports records with embedded base64 images or image_path fallbacks
  - Fine-tunes Qwen3-VL with 4-bit BitsAndBytes + LoRA attention adapters
  - Applies asymmetric food-safety loss for false-safe moisture predictions
  - Saves LoRA adapters to models/qwen_grain_lora_latest/

This file also keeps FeedbackCollector and GradingFeedbackItem compatible with
app.py, which imports them for Streamlit feedback capture.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import logging
import math
import os
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


MOISTURE_ORDER = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
GRADE_VALUES = {"A", "B", "C"}
MOISTURE_VALUES = set(MOISTURE_ORDER)


def flatten_feature_dict(data: Dict[str, Any], prefix: str = "") -> Dict[str, float]:
    """Flatten nested numeric feedback feature dictionaries for retrieval similarity."""
    flat: Dict[str, float] = {}
    for key, value in (data or {}).items():
        joined = f"{prefix}_{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_feature_dict(value, joined))
        elif isinstance(value, (int, float, np.integer, np.floating)):
            flat[joined] = float(value)
    return flat


def _clean_enum(value: Any, allowed: set[str], default: str) -> str:
    text = str(value or default).strip().upper()
    return text if text in allowed else default


def _version_tuple(version_text: str) -> Tuple[int, int, int]:
    """Parse package versions loosely enough to handle dev wheels."""
    parts = [int(part) for part in re.findall(r"\d+", version_text)[:3]]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


@dataclass
class GradingFeedbackItem:
    """Single feedback instance captured by the Streamlit correction workflow."""

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


@dataclass
class VisionFeedbackExample:
    """Normalized multimodal SFT example for Qwen3-VL."""

    sample_id: str
    prompt: str
    target_json: Dict[str, Any]
    image_base64: Optional[str]
    image_path: Optional[Path]
    true_moisture_risk: str
    predicted_moisture_risk: str
    true_grade: str
    source_file: Path

    @property
    def target_text(self) -> str:
        return json.dumps(self.target_json, ensure_ascii=False, sort_keys=True)


def _strip_data_url(image_text: str) -> str:
    """Return the raw base64 payload from either plain base64 or data:image/... URLs."""
    if "," in image_text and image_text.lower().lstrip().startswith("data:"):
        return image_text.split(",", 1)[1].strip()
    return image_text.strip()


def _find_base64_image(data: Dict[str, Any]) -> Optional[str]:
    """Search common feedback schemas for an embedded base64 image string."""
    direct_keys = (
        "image_base64",
        "base64_image",
        "image_b64",
        "input_image_base64",
        "original_image_base64",
        "image",
    )
    for key in direct_keys:
        value = data.get(key)
        if isinstance(value, str) and len(value) > 500:
            return _strip_data_url(value)

    nested = data.get("image_data")
    if isinstance(nested, dict):
        for key in direct_keys:
            value = nested.get(key)
            if isinstance(value, str) and len(value) > 500:
                return _strip_data_url(value)
    return None


def _resolve_image_path(record: Dict[str, Any], source_file: Path) -> Optional[Path]:
    """Resolve image paths relative to cwd first, then the feedback file directory."""
    raw_path = record.get("image_path") or record.get("original_image_path")
    if not raw_path:
        return None

    candidate = Path(str(raw_path))
    if candidate.exists():
        return candidate

    relative_to_cwd = Path.cwd() / candidate
    if relative_to_cwd.exists():
        return relative_to_cwd

    relative_to_feedback = source_file.parent / candidate
    if relative_to_feedback.exists():
        return relative_to_feedback
    return candidate


def _build_prompt_from_feedback(record: Dict[str, Any]) -> str:
    """Construct a compact prompt when the feedback record did not store the original prompt."""
    prompt = (
        record.get("original_prompt")
        or record.get("prompt")
        or record.get("input_prompt")
        or record.get("user_prompt")
    )
    if prompt:
        return str(prompt)

    features = record.get("image_features", {}) or {}
    lab = features.get("lab_features", {}) or {}
    clumping = features.get("clumping", {}) or {}
    calibration = features.get("calibration", {}) or {}
    physical = features.get("physical_properties", {}) or {}
    notes = str(record.get("notes") or "").strip()
    return (
        "Grade this finger millet (ragi) batch from the image and measured proxies. "
        "Return only strict JSON with quality_grade, moisture_risk, visible_defects, "
        "foreign_matter_percent, broken_grain_percent, and brief_reason.\n"
        f"Measured signals: darkness={float(lab.get('color_darkness_index') or 0.0):.1f}, "
        f"clumping={float(clumping.get('density') or 0.0):.3f}, "
        f"uniformity={float(features.get('uniformity_score') or 0.0):.1f}, "
        f"entropy={float(features.get('texture_entropy') or 0.0):.2f}, "
        f"calibration={calibration.get('source', 'none')}, "
        f"grain_size={physical.get('size_class', 'unknown')}. "
        f"Operator note: {notes or 'none'}"
    )


def _extract_corrected_json(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize human-corrected labels into the assistant JSON target."""
    for key in (
        "human_corrected_json",
        "corrected_json",
        "corrected_output",
        "human_output",
        "target_json",
        "assistant_target",
    ):
        value = record.get(key)
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip().startswith("{"):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

    features = record.get("image_features", {}) or {}
    physical = features.get("physical_properties", {}) or {}
    geometry = features.get("calibrated_geometry", {}) or {}
    true_grade = _clean_enum(record.get("true_grade"), GRADE_VALUES, "C")
    true_moisture = _clean_enum(record.get("true_moisture_risk"), MOISTURE_VALUES, "HIGH")
    return {
        "quality_grade": true_grade,
        "moisture_risk": true_moisture,
        "reject_recommended": true_grade == "C" or true_moisture in {"HIGH", "CRITICAL"},
        "broken_grain_percent": float(record.get("broken_grain_percent") or 0.0),
        "foreign_matter_percent": float(record.get("foreign_matter_percent") or 0.0),
        "mold_visible": bool(record.get("mold_visible") or False),
        "visible_defects": [str(record.get("notes") or "").strip()] if record.get("notes") else [],
        "grain_size_class": physical.get("size_class", "unknown"),
        "grain_fill_ratio": float(geometry.get("grain_fill_ratio") or 0.0),
        "brief_reason": (
            f"Human correction: grade {true_grade}, moisture risk {true_moisture}."
        ),
    }


def load_feedback_examples(feedback_dir: Path, require_image: bool = True) -> List[VisionFeedbackExample]:
    """
    Load JSON feedback files into multimodal SFT examples.

    The loader accepts both the requested embedded-base64 schema and the current
    Streamlit schema, where JSON stores image_path and labels while images live
    under feedback_data/session_uploads/.
    """
    examples: List[VisionFeedbackExample] = []
    feedback_files = sorted(feedback_dir.glob("*.json"))
    for path in feedback_files:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Skipping unreadable feedback file %s: %s", path, exc)
            continue

        image_base64 = _find_base64_image(record)
        image_path = _resolve_image_path(record, path)
        has_image = bool(image_base64) or bool(image_path and image_path.exists())
        if require_image and not has_image:
            logger.warning("Skipping %s: no embedded base64 image or readable image_path", path.name)
            continue

        true_grade = _clean_enum(record.get("true_grade"), GRADE_VALUES, "C")
        true_moisture = _clean_enum(record.get("true_moisture_risk"), MOISTURE_VALUES, "HIGH")
        predicted_moisture = _clean_enum(
            record.get("predicted_moisture_risk"),
            MOISTURE_VALUES,
            "LOW",
        )
        target_json = _extract_corrected_json(record)
        target_json["quality_grade"] = _clean_enum(target_json.get("quality_grade"), GRADE_VALUES, true_grade)
        target_json["moisture_risk"] = _clean_enum(target_json.get("moisture_risk"), MOISTURE_VALUES, true_moisture)

        examples.append(
            VisionFeedbackExample(
                sample_id=str(record.get("sample_id") or path.stem),
                prompt=_build_prompt_from_feedback(record),
                target_json=target_json,
                image_base64=image_base64,
                image_path=image_path if image_path and image_path.exists() else None,
                true_moisture_risk=true_moisture,
                predicted_moisture_risk=predicted_moisture,
                true_grade=true_grade,
                source_file=path,
            )
        )

    logger.info("Loaded %d trainable feedback examples from %s", len(examples), feedback_dir)
    return examples


class QwenGrainFeedbackDataset(Dataset):
    """Lazy image dataset for Qwen3-VL supervised fine-tuning."""

    def __init__(self, examples: Sequence[VisionFeedbackExample], max_image_side: int = 640):
        self.examples = list(examples)
        self.max_image_side = int(max_image_side)

    def __len__(self) -> int:
        return len(self.examples)

    def _load_image(self, example: VisionFeedbackExample) -> Image.Image:
        if example.image_base64:
            raw = base64.b64decode(_strip_data_url(example.image_base64), validate=False)
            image = Image.open(io.BytesIO(raw)).convert("RGB")
        elif example.image_path:
            image = Image.open(example.image_path).convert("RGB")
        else:
            raise ValueError(f"Example {example.sample_id} has no image")

        image.thumbnail((self.max_image_side, self.max_image_side), Image.Resampling.LANCZOS)
        return image

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        example = self.examples[idx]
        return {
            "sample_id": example.sample_id,
            "image": self._load_image(example),
            "prompt": example.prompt,
            "target_text": example.target_text,
            "true_moisture_risk": example.true_moisture_risk,
            "predicted_moisture_risk": example.predicted_moisture_risk,
            "true_grade": example.true_grade,
        }


class QwenVLDataCollator:
    """Build multimodal Qwen chat batches and mask prompt tokens from loss."""

    def __init__(self, processor: Any, tokenizer: Any, max_length: int = 1536):
        self.processor = processor
        self.tokenizer = tokenizer
        self.max_length = max_length

    def _chat_text(self, prompt: str, target_text: Optional[str]) -> str:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        if target_text is not None:
            messages.append(
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": target_text}],
                }
            )
            return self.processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
        return self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        images = [item["image"] for item in features]
        full_texts = [self._chat_text(item["prompt"], item["target_text"]) for item in features]
        prompt_texts = [self._chat_text(item["prompt"], None) for item in features]

        full_batch = self.processor(
            text=full_texts,
            images=images,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        prompt_batch = self.processor(
            text=prompt_texts,
            images=images,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )

        labels = full_batch["input_ids"].clone()
        labels[full_batch["attention_mask"] == 0] = -100
        prompt_lengths = prompt_batch["attention_mask"].sum(dim=1).tolist()
        for row_idx, prompt_len in enumerate(prompt_lengths):
            labels[row_idx, : int(prompt_len)] = -100

        full_batch["labels"] = labels
        full_batch["true_moisture_risk"] = [item["true_moisture_risk"] for item in features]
        full_batch["sample_id"] = [item["sample_id"] for item in features]
        return full_batch


def parse_moisture_risk(text: str) -> Optional[str]:
    """Extract moisture risk from generated JSON-ish text."""
    match = re.search(r'"?moisture[_\s-]*risk"?\s*[:=]\s*"?(LOW|MODERATE|HIGH|CRITICAL)"?', text, re.I)
    if match:
        return match.group(1).upper()
    for value in ("CRITICAL", "HIGH", "MODERATE", "LOW"):
        if re.search(rf"\b{value}\b", text, re.I):
            return value
    return None


class AsymmetricMoistureSFTLoss(nn.Module):
    """
    Token-level SFT loss with food-safety asymmetric weighting.

    If the current model argmax completion says moisture_risk LOW while human
    truth is HIGH or CRITICAL, the whole assistant completion loss for that
    sample is multiplied by false_safe_weight (default 5.0).
    """

    def __init__(self, tokenizer: Any, false_safe_weight: float = 5.0):
        super().__init__()
        self.tokenizer = tokenizer
        self.false_safe_weight = float(false_safe_weight)

    def forward(
        self,
        logits: torch.Tensor,
        labels: torch.Tensor,
        true_moisture_risk: Sequence[str],
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        shift_logits = logits[:, :-1, :].contiguous()
        shift_labels = labels[:, 1:].contiguous()
        per_token_loss = nn.functional.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            ignore_index=-100,
            reduction="none",
        ).view_as(shift_labels)

        valid_mask = shift_labels.ne(-100)
        pred_ids = shift_logits.detach().argmax(dim=-1)
        sample_losses: List[torch.Tensor] = []
        false_safe_count = 0
        weights: List[float] = []

        for row_idx in range(shift_labels.size(0)):
            token_count = valid_mask[row_idx].sum().clamp_min(1)
            base_loss = (per_token_loss[row_idx] * valid_mask[row_idx]).sum() / token_count
            pred_completion = self.tokenizer.decode(
                pred_ids[row_idx][valid_mask[row_idx]].detach().cpu().tolist(),
                skip_special_tokens=True,
            )
            predicted_moisture = parse_moisture_risk(pred_completion)
            truth = str(true_moisture_risk[row_idx]).upper()

            weight = 1.0
            if predicted_moisture == "LOW" and truth in {"HIGH", "CRITICAL"}:
                weight = self.false_safe_weight
                false_safe_count += 1
            sample_losses.append(base_loss * weight)
            weights.append(weight)

        loss = torch.stack(sample_losses).mean()
        metrics = {
            "false_safe_count": float(false_safe_count),
            "mean_safety_weight": float(sum(weights) / max(1, len(weights))),
        }
        return loss, metrics


class AsymmetricGradingLoss(nn.Module):
    """
    Backward-compatible grade classifier loss used by older smoke tests.

    The production trainer below uses AsymmetricMoistureSFTLoss on generated
    Qwen tokens. This small class remains useful for unit tests and lightweight
    classifiers: grade IDs are ordered A=0, B=1, C=2, so predicting a safer
    class than the human label receives the false-safe multiplier.
    """

    def __init__(self, false_safe_weight: float = 5.0):
        super().__init__()
        self.false_safe_weight = float(false_safe_weight)

    def forward(self, logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        per_sample_loss = nn.functional.cross_entropy(logits, labels, reduction="none")
        predictions = logits.detach().argmax(dim=-1)
        false_safe_mask = predictions.lt(labels)
        weights = torch.ones_like(per_sample_loss)
        weights = torch.where(
            false_safe_mask,
            weights * self.false_safe_weight,
            weights,
        )
        return (per_sample_loss * weights).mean()


class QwenGrainLoRATrainer:
    """Local RTX 3050-oriented QLoRA trainer for Qwen3-VL."""

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-VL-8B-Instruct",
        output_dir: Optional[Path] = None,
        lora_rank: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.05,
        target_modules: Optional[List[str]] = None,
        max_length: int = 1536,
        max_image_side: int = 640,
        gpu_memory_gb: Optional[float] = None,
        cpu_memory_gb: int = 32,
    ):
        self.model_name = model_name
        self.output_dir = Path(output_dir or "models/qwen_grain_lora_latest")
        self.lora_rank = lora_rank
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules or ["q_proj", "v_proj"]
        self.max_length = max_length
        self.max_image_side = max_image_side
        self.gpu_memory_gb = gpu_memory_gb
        self.cpu_memory_gb = cpu_memory_gb
        self.processor = None
        self.tokenizer = None
        self.model = None

    @staticmethod
    def split_by_farm(
        feedback_items: Sequence[GradingFeedbackItem],
        test_farms: Sequence[str],
    ) -> Tuple[List[GradingFeedbackItem], List[GradingFeedbackItem]]:
        """Keep farms disjoint across train/test to avoid farm-specific leakage."""
        test_farm_set = {str(farm) for farm in test_farms}
        train: List[GradingFeedbackItem] = []
        test: List[GradingFeedbackItem] = []
        for item in feedback_items:
            if item.farm_id in test_farm_set:
                test.append(item)
            else:
                train.append(item)
        return train, test

    def _require_training_dependencies(self) -> None:
        missing = []
        try:
            import peft  # noqa: F401
        except Exception:
            missing.append("peft")
        try:
            import bitsandbytes  # noqa: F401
        except Exception:
            missing.append("bitsandbytes")
        try:
            import transformers
            from importlib.metadata import version

            transformers_version = version("transformers")
            if _version_tuple(transformers_version) < (4, 57, 0):
                missing.append(f"transformers>=4.57.0 for Qwen3-VL (found {transformers_version})")
        except Exception:
            missing.append("transformers")
        if missing:
            raise RuntimeError(
                "Missing training dependencies: "
                + ", ".join(sorted(set(missing)))
                + ". Install a Qwen3-VL compatible stack, for example: "
                "pip install -U transformers accelerate peft bitsandbytes "
                "or pip install git+https://github.com/huggingface/transformers"
            )

    def _device_memory_map(self) -> Optional[Dict[Any, str]]:
        """
        Build an Accelerate max_memory map.

        Qwen3-VL 8B in 4-bit is still too large for a true 4 GB RTX 3050-only
        training run. max_memory lets Accelerate keep the hot path on CUDA while
        spilling full modules to CPU instead of hard-crashing with CUDA OOM. On
        an actual 8 GB card, the default budget leaves roughly 1 GB for kernels,
        activations, and Streamlit/Ollama leftovers.
        """
        if not torch.cuda.is_available():
            return None

        total_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        if self.gpu_memory_gb is not None:
            gpu_budget = max(1.0, float(self.gpu_memory_gb))
        else:
            reserve_gb = 0.75 if total_gb <= 6 else 1.25
            gpu_budget = max(1.0, math.floor((total_gb - reserve_gb) * 10) / 10)

        if total_gb < 6:
            logger.warning(
                "Detected %.1fGB CUDA memory. Qwen3-VL 8B QLoRA will require CPU offload "
                "and will be slow; an 8GB+ GPU is strongly preferred.",
                total_gb,
            )
        return {0: f"{gpu_budget:.1f}GiB", "cpu": f"{int(self.cpu_memory_gb)}GiB"}

    def load_model(self, resume_adapter: bool = True) -> None:
        """Load Qwen3-VL in 4-bit and attach LoRA adapters to attention projections."""
        self._require_training_dependencies()

        from transformers import AutoProcessor, BitsAndBytesConfig
        from peft import LoraConfig, PeftModel, TaskType, get_peft_model, prepare_model_for_kbit_training

        try:
            from transformers import Qwen3VLForConditionalGeneration

            model_cls = Qwen3VLForConditionalGeneration
        except Exception:
            try:
                from transformers import AutoModelForImageTextToText

                model_cls = AutoModelForImageTextToText
            except Exception:
                from transformers import AutoModelForCausalLM

                model_cls = AutoModelForCausalLM

        compute_dtype = torch.float16
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=compute_dtype,
        )

        logger.info("Loading processor: %s", self.model_name)
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            use_fast=True,
        )
        self.tokenizer = getattr(self.processor, "tokenizer", self.processor)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        logger.info("Loading 4-bit base model: %s", self.model_name)
        offload_dir = self.output_dir / "offload"
        offload_dir.mkdir(parents=True, exist_ok=True)
        base_model = model_cls.from_pretrained(
            self.model_name,
            quantization_config=quant_config,
            device_map="auto",
            max_memory=self._device_memory_map(),
            offload_folder=str(offload_dir),
            offload_state_dict=True,
            torch_dtype=compute_dtype,
            trust_remote_code=True,
        )
        base_model.config.use_cache = False
        if hasattr(base_model, "gradient_checkpointing_enable"):
            base_model.gradient_checkpointing_enable()

        base_model = prepare_model_for_kbit_training(base_model, use_gradient_checkpointing=True)

        if resume_adapter and (self.output_dir / "adapter_config.json").exists():
            logger.info("Resuming trainable LoRA adapter from %s", self.output_dir)
            self.model = PeftModel.from_pretrained(base_model, self.output_dir, is_trainable=True)
        else:
            lora_config = LoraConfig(
                r=self.lora_rank,
                lora_alpha=self.lora_alpha,
                lora_dropout=self.lora_dropout,
                bias="none",
                task_type=TaskType.CAUSAL_LM,
                # PEFT applies suffix matches, so q_proj/v_proj hits both text
                # and vision attention projections when Qwen3-VL exposes them
                # with the standard Qwen naming. Keeping the list narrow is
                # deliberate for an 8GB RTX 3050; all-linear QLoRA is stronger
                # but materially heavier on activations.
                target_modules=self.target_modules,
            )
            self.model = get_peft_model(base_model, lora_config)

        self.model.print_trainable_parameters()

    def _optimizer(self, learning_rate: float) -> torch.optim.Optimizer:
        try:
            import bitsandbytes as bnb

            return bnb.optim.PagedAdamW8bit(
                self.model.parameters(),
                lr=learning_rate,
                weight_decay=0.01,
            )
        except Exception:
            logger.warning("bitsandbytes optimizer unavailable; falling back to torch AdamW.")
            return torch.optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=0.01)

    def train(
        self,
        examples: Sequence[VisionFeedbackExample],
        epochs: int = 1,
        batch_size: int = 1,
        gradient_accumulation_steps: int = 8,
        learning_rate: float = 2e-4,
        max_steps: Optional[int] = None,
        resume_adapter: bool = True,
    ) -> Dict[str, Any]:
        if not examples:
            raise ValueError("No trainable feedback examples were loaded.")

        self.load_model(resume_adapter=resume_adapter)
        dataset = QwenGrainFeedbackDataset(examples, max_image_side=self.max_image_side)
        collator = QwenVLDataCollator(self.processor, self.tokenizer, max_length=self.max_length)
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0,
            collate_fn=collator,
        )
        optimizer = self._optimizer(learning_rate)
        safety_loss = AsymmetricMoistureSFTLoss(self.tokenizer, false_safe_weight=5.0)

        device_type = "cuda" if torch.cuda.is_available() else "cpu"
        use_amp = torch.cuda.is_available()
        self.model.train()
        global_step = 0
        optimizer.zero_grad(set_to_none=True)
        history: List[Dict[str, float]] = []

        for epoch in range(epochs):
            logger.info("Starting epoch %d/%d", epoch + 1, epochs)
            for batch_idx, batch in enumerate(loader):
                true_moisture = batch.pop("true_moisture_risk")
                sample_ids = batch.pop("sample_id")
                model_device = next(self.model.parameters()).device
                batch = {
                    key: value.to(model_device) if torch.is_tensor(value) else value
                    for key, value in batch.items()
                }

                with torch.autocast(device_type=device_type, dtype=torch.float16, enabled=use_amp):
                    outputs = self.model(**batch)
                    loss, loss_metrics = safety_loss(outputs.logits, batch["labels"], true_moisture)
                    scaled_loss = loss / gradient_accumulation_steps

                scaled_loss.backward()

                if (batch_idx + 1) % gradient_accumulation_steps == 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 0.3)
                    optimizer.step()
                    optimizer.zero_grad(set_to_none=True)
                    global_step += 1

                    if torch.cuda.is_available():
                        allocated_gb = torch.cuda.memory_allocated() / 1024**3
                    else:
                        allocated_gb = 0.0
                    record = {
                        "step": float(global_step),
                        "loss": float(loss.detach().cpu()),
                        "false_safe_count": loss_metrics["false_safe_count"],
                        "mean_safety_weight": loss_metrics["mean_safety_weight"],
                        "cuda_allocated_gb": float(allocated_gb),
                    }
                    history.append(record)
                    logger.info(
                        "step=%d loss=%.4f safety_weight=%.2f false_safe=%d samples=%s vram=%.2fGB",
                        global_step,
                        record["loss"],
                        record["mean_safety_weight"],
                        int(record["false_safe_count"]),
                        ",".join(sample_ids[:2]),
                        record["cuda_allocated_gb"],
                    )

                    if max_steps is not None and global_step >= max_steps:
                        logger.info("Reached max_steps=%d", max_steps)
                        return self.save(history, examples)

            leftover = len(loader) % gradient_accumulation_steps
            if leftover:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 0.3)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1

        return self.save(history, examples)

    def save(self, history: List[Dict[str, float]], examples: Sequence[VisionFeedbackExample]) -> Dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(self.output_dir)
        self.processor.save_pretrained(self.output_dir)

        manifest = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "base_model": self.model_name,
            "adapter_dir": str(self.output_dir),
            "sample_count": len(examples),
            "lora_target_modules": self.target_modules,
            "lora_rank": self.lora_rank,
            "lora_alpha": self.lora_alpha,
            "asymmetric_loss": {
                "rule": "predicted LOW while human truth HIGH/CRITICAL",
                "weight": 5.0,
            },
            "sources": [str(example.source_file) for example in examples],
            "history": history,
        }
        (self.output_dir / "training_manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        logger.info("Saved LoRA adapters to %s", self.output_dir)
        return manifest


RagiLoRAFinetuner = QwenGrainLoRATrainer


class FeedbackCollector:
    """Storage and retrieval helper used by the Streamlit feedback UI."""

    def __init__(self, storage_path: str = "./feedback_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def submit_feedback(self, feedback_item: GradingFeedbackItem) -> bool:
        try:
            filename = self.storage_path / f"{feedback_item.sample_id}_{datetime.now(timezone.utc).timestamp()}.json"
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

    def retrieve_similar_feedback(self, image_features: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
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
            graded_change = item.predicted_grade != item.true_grade
            moisture_change = item.predicted_moisture_risk != item.true_moisture_risk
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
                        "grade_changed": graded_change,
                        "moisture_changed": moisture_change,
                    },
                )
            )
        scored.sort(key=lambda pair: (pair[0], -int(pair[1]["grade_changed"]), -int(pair[1]["moisture_changed"])))
        return [item for _, item in scored[:limit]]

    def summarize_feedback_patterns(self, limit: int = 5) -> List[str]:
        transitions: Dict[str, int] = {}
        for item in self.load_all_feedback():
            key = f"{item.predicted_grade}->{item.true_grade}"
            transitions[key] = transitions.get(key, 0) + 1
        ranked = sorted(transitions.items(), key=lambda pair: pair[1], reverse=True)
        return [f"{transition} occurred {count} time(s)" for transition, count in ranked[:limit]]

    def check_and_trigger_training(self, threshold: int = 500) -> bool:
        pending = self.get_pending_count()
        logger.info("Pending feedback: %d/%d", pending, threshold)
        return pending >= threshold


def _fingerprint_feedback(files: Iterable[Path]) -> Dict[str, float]:
    return {str(path): path.stat().st_mtime for path in files if path.exists()}


def train_once(args: argparse.Namespace) -> Dict[str, Any]:
    feedback_dir = Path(args.feedback_dir)
    output_dir = Path(args.output_dir)
    examples = load_feedback_examples(feedback_dir, require_image=not args.allow_missing_images)
    if len(examples) < args.min_samples:
        raise RuntimeError(f"Only {len(examples)} examples available; min_samples={args.min_samples}.")

    trainer = QwenGrainLoRATrainer(
        model_name=args.model_name,
        output_dir=output_dir,
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=args.target_modules,
        max_length=args.max_length,
        max_image_side=args.max_image_side,
        gpu_memory_gb=args.gpu_memory_gb,
        cpu_memory_gb=args.cpu_memory_gb,
    )
    return trainer.train(
        examples=examples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        max_steps=args.max_steps,
        resume_adapter=not args.no_resume_adapter,
    )


def continuous_train(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    manifest_path = output_dir / "continuous_state.json"
    last_fingerprint: Dict[str, float] = {}
    if manifest_path.exists():
        try:
            last_fingerprint = json.loads(manifest_path.read_text(encoding="utf-8")).get("fingerprint", {})
        except Exception:
            last_fingerprint = {}

    while True:
        files = sorted(Path(args.feedback_dir).glob("*.json"))
        fingerprint = _fingerprint_feedback(files)
        changed = fingerprint != last_fingerprint
        if changed and len(files) >= args.min_samples:
            logger.info("Feedback changed; starting LoRA update.")
            train_once(args)
            last_fingerprint = fingerprint
            output_dir.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "fingerprint": last_fingerprint,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        else:
            logger.info("No training run needed. files=%d changed=%s", len(files), changed)
        time.sleep(args.poll_seconds)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Qwen3-VL QLoRA trainer for ragi grading feedback.")
    parser.add_argument("--feedback-dir", default="feedback_data")
    parser.add_argument("--output-dir", default="models/qwen_grain_lora_latest")
    parser.add_argument("--model-name", default="Qwen/Qwen3-VL-8B-Instruct")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--max-length", type=int, default=1536)
    parser.add_argument("--max-image-side", type=int, default=640)
    parser.add_argument("--gpu-memory-gb", type=float, default=None)
    parser.add_argument("--cpu-memory-gb", type=int, default=32)
    parser.add_argument("--lora-rank", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--target-modules", nargs="+", default=["q_proj", "v_proj"])
    parser.add_argument("--min-samples", type=int, default=1)
    parser.add_argument("--allow-missing-images", action="store_true")
    parser.add_argument("--no-resume-adapter", action="store_true")
    parser.add_argument("--continuous", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    examples = load_feedback_examples(Path(args.feedback_dir), require_image=not args.allow_missing_images)
    logger.info("Dataset dry check: %d example(s)", len(examples))
    if args.dry_run:
        preview = examples[0] if examples else None
        if preview:
            logger.info("First example: sample_id=%s target=%s", preview.sample_id, preview.target_text)
        return

    if args.continuous:
        continuous_train(args)
    else:
        train_once(args)


if __name__ == "__main__":
    main()
