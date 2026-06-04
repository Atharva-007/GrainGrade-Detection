"""
Streamlit UI for Ragi Quality Grading System - "Millets Now"
=============================================================

Production-ready web interface featuring:
  - Image upload with validation
  - Real-time physics proxy extraction
  - Vision-RAG grading with two-pass logic
  - Moisture risk assessment
  - Human feedback collection for active learning
  - Results dashboard with confidence scores
  - Audit trail and export capabilities

Deployment: streamlit run app.py --server.port 8501

Author: Copilot
Date: 2026-04-29
"""

import streamlit as st
import asyncio
import json
import html
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageOps

# Our modules
from .paths import (
    FEEDBACK_DIR,
    PROJECT_ROOT,
    RAG_INDEX_PATH,
    SESSION_UPLOADS_DIR,
    ensure_runtime_dirs,
)
from .physics_proxies import PhysicsProxiesExtractor
from .vision_rag_pipeline import VisionRAGPipeline, MoistureRisk, QualityGrade
from .feedback import FeedbackCollector, GradingFeedbackItem

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")
ensure_runtime_dirs()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG & INITIALIZATION
# ============================================================================

DEFAULT_QWEN_PROVIDER = "dashscope"
DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
CLOUD_QWEN_PROVIDERS = {"dashscope", "siliconflow", "custom"}


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _is_local_base_url(url: str) -> bool:
    text = str(url or "").lower()
    return any(marker in text for marker in ("localhost", "127.0.0.1", "0.0.0.0", "[::1]", "::1"))


def _qwen_runtime_config() -> Dict[str, Any]:
    requested_provider = os.getenv("QWEN_VL_PROVIDER", DEFAULT_QWEN_PROVIDER).strip().lower()
    provider = requested_provider if requested_provider in CLOUD_QWEN_PROVIDERS else DEFAULT_QWEN_PROVIDER
    provider_warning = ""
    if requested_provider and requested_provider not in CLOUD_QWEN_PROVIDERS:
        provider_warning = (
            f"Provider `{requested_provider}` is not supported in this cloud-only build; "
            f"using `{provider}`."
        )

    if provider == "siliconflow":
        model = os.getenv("QWEN_VL_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")
        base_url = _first_env(
            "QWEN_VL_BASE_URL",
            "SILICONFLOW_BASE_URL",
            default=DEFAULT_SILICONFLOW_BASE_URL,
        )
        api_key = _first_env("QWEN_VL_API_KEY", "SILICONFLOW_API_KEY")
    else:
        model = os.getenv("QWEN_VL_MODEL", "qwen3-vl-plus")
        base_url = _first_env(
            "QWEN_VL_BASE_URL",
            "DASHSCOPE_BASE_URL",
            default=DEFAULT_DASHSCOPE_BASE_URL if provider == "dashscope" else "",
        )
        api_key = _first_env("QWEN_VL_API_KEY", "DASHSCOPE_API_KEY")

    local_url_blocked = False
    if _is_local_base_url(base_url):
        local_url_blocked = True
        base_url = ""

    return {
        "provider": provider,
        "requested_provider": requested_provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
        "provider_warning": provider_warning,
        "local_url_blocked": local_url_blocked,
        "label": f"{provider}/{model}",
    }

st.set_page_config(
    page_title="Millets Now - Ragi Grading",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for Cyber-Green Workstation
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&family=Inter:wght@400;700;900&display=swap');

    :root {
        --bg-main: #000000;
        --bg-surface: #0a0c0b;
        --bg-card: #0f1210;
        --border-neon: #00ff41;
        --border-dim: #1a221c;
        --neon-green: #00ff41;
        --neon-dim: rgba(0, 255, 65, 0.05);
        --text-primary: #ffffff;
        --text-secondary: #8b9d92;
        --radius-m: 12px;
        --gap-main: 2rem;
    }

    /* Kill Streamlit Defaults */
    [data-testid="stHeader"], [data-testid="stSidebar"], .stDeployButton, [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background-color: var(--bg-main) !important;
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Professional Workstation Header */
    .workstation-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 72px;
        background: var(--bg-surface);
        border-bottom: 1px solid var(--border-dim);
        display: flex;
        align-items: center;
        padding: 0 3rem;
        z-index: 10000;
        justify-content: space-between;
    }

    .brand-group {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }

    .brand-id {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 800;
        color: var(--neon-green);
        font-size: 1.4rem;
        letter-spacing: -1px;
    }

    .mission-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: var(--text-secondary);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--border-dim);
        padding: 4px 12px;
        border-radius: 20px;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--neon-green);
        box-shadow: 0 0 10px var(--neon-green);
    }

    /* Main Viewport with Space */
    .workstation-viewport {
        margin-top: 100px;
        padding: 0 4rem 6rem 4rem;
        max-width: 1600px;
        margin-left: auto;
        margin-right: auto;
    }

    /* Cyber Cards & Spacing */
    .cyber-card, [data-testid="stMetric"], .stChatMessage {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: var(--radius-m) !important;
        padding: 2rem !important;
        transition: all 0.3s ease;
    }

    .cyber-card:hover {
        border-color: rgba(0, 255, 65, 0.3) !important;
        background-color: #121714 !important;
    }

    /* Pro Metrics */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        color: var(--neon-green) !important;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        letter-spacing: -2px !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1rem !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
    }

    /* Cyber Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00ff41 0%, #00cc33 100%) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 900 !important;
        font-size: 1rem !important;
        padding: 1rem 2rem !important;
        width: 100% !important;
        box-shadow: 0 4px 20px rgba(0, 255, 65, 0.2) !important;
        transition: all 0.2s !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 255, 65, 0.4) !important;
    }

    /* Navigation - Segmented Control */
    div[data-testid="stRadio"] > div {
        background: var(--bg-surface);
        border: 1px solid var(--border-dim);
        padding: 6px;
        border-radius: 12px;
        display: flex;
        gap: 8px;
    }

    div[data-testid="stRadio"] label {
        flex: 1;
        padding: 10px !important;
        background: transparent !important;
        color: var(--text-secondary) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 0.8rem !important;
        letter-spacing: 0.05em;
    }

    div[data-testid="stRadio"] label[data-selected="true"] {
        background: var(--border-dim) !important;
        color: var(--neon-green) !important;
    }

    /* File Uploader - Cyber Style */
    [data-testid="stFileUploaderDropzone"] {
        background: var(--bg-card) !important;
        border: 2px dashed var(--border-dim) !important;
        border-radius: 12px !important;
    }

    /* Decision Panel */
    .decision-hero {
        background: linear-gradient(180deg, var(--neon-dim) 0%, transparent 100%);
        border: 1px solid var(--neon-green);
        border-radius: 16px;
        padding: 3rem;
        position: relative;
    }

    .decision-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 5.5rem;
        font-weight: 900;
        color: var(--neon-green);
        line-height: 1;
        letter-spacing: -4px;
    }

    /* Trace/Overlay Toggle */
    .trace-btn {
        background: var(--bg-surface);
        border: 1px solid var(--neon-green);
        color: var(--neon-green);
        padding: 8px 20px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 800;
        cursor: pointer;
        transition: all 0.2s;
    }

    .trace-btn:hover {
        background: var(--neon-green);
        color: #000;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    :root {
        --bg-main: #07120b;
        --bg-soft: #0d1a11;
        --bg-surface: #102016;
        --bg-card: rgba(16, 32, 22, 0.94);
        --bg-card-strong: #13291b;
        --border-dim: rgba(132, 204, 22, 0.20);
        --border-strong: rgba(132, 204, 22, 0.42);
        --accent: #84cc16;
        --accent-strong: #a3e635;
        --accent-soft: rgba(132, 204, 22, 0.12);
        --text: #f4fff2;
        --muted: #a8bba2;
        --muted-2: #789070;
        --danger: #fb7185;
        --warn: #facc15;
        --radius-s: 8px;
        --radius-m: 10px;
        --radius-l: 14px;
        --shadow-soft: 0 22px 70px rgba(0, 0, 0, 0.30);
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background:
            radial-gradient(circle at 12% 5%, rgba(132, 204, 22, 0.16), transparent 28rem),
            radial-gradient(circle at 90% 12%, rgba(34, 197, 94, 0.12), transparent 26rem),
            linear-gradient(180deg, #07120b 0%, #09150d 48%, #050b07 100%) !important;
        color: var(--text) !important;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }

    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    .workstation-header {
        height: 72px;
        background: rgba(7, 18, 11, 0.92);
        border-bottom: 1px solid var(--border-dim);
        box-shadow: 0 12px 34px rgba(0, 0, 0, 0.24);
        backdrop-filter: blur(16px);
        padding: 0 clamp(1rem, 4vw, 3rem);
    }

    .brand-id {
        color: var(--accent-strong);
        font-size: 1rem;
        letter-spacing: 0;
    }

    .mission-status {
        background: var(--accent-soft);
        color: var(--muted);
        border: 1px solid var(--border-dim);
        border-radius: 999px;
    }

    .status-dot {
        background: var(--accent);
        box-shadow: 0 0 16px rgba(132, 204, 22, 0.8);
    }

    .workstation-viewport {
        margin-top: 96px;
        padding: 0 clamp(1rem, 4vw, 4rem) 5rem;
        max-width: 1480px;
    }

    .detail-action-row {
        display: flex;
        justify-content: flex-end;
        margin: 0 0 1rem;
    }

    .app-hero {
        border: 1px solid var(--border-dim);
        border-radius: var(--radius-l);
        background:
            linear-gradient(135deg, rgba(132, 204, 22, 0.14), rgba(16, 32, 22, 0.92)),
            linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent);
        box-shadow: var(--shadow-soft);
        padding: clamp(1.4rem, 3vw, 2.75rem);
        margin-bottom: 1.5rem;
    }

    .hero-eyebrow,
    .section-eyebrow,
    .sidebar-label,
    .hero-stat-label {
        color: var(--accent-strong);
        font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, monospace;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .hero-title {
        color: var(--text);
        font-size: clamp(2rem, 5vw, 4.1rem);
        line-height: 1.02;
        font-weight: 900;
        letter-spacing: 0;
        max-width: 820px;
        margin-top: 0.45rem;
    }

    .hero-body,
    .section-copy,
    .decision-note,
    .result-subtitle,
    .sidebar-sub,
    .signal-caption {
        color: var(--muted);
        line-height: 1.6;
    }

    .hero-body {
        max-width: 760px;
        font-size: 1rem;
        margin-top: 1rem;
    }

    .hero-mini {
        color: var(--muted-2);
        margin-top: 0.5rem;
    }

    .pill-row {
        display: flex;
        gap: 0.65rem;
        flex-wrap: wrap;
        margin-top: 1.4rem;
    }

    .status-pill {
        border: 1px solid var(--border-dim);
        background: rgba(7, 18, 11, 0.48);
        color: var(--muted);
        border-radius: 999px;
        padding: 0.48rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .status-online { color: var(--accent-strong) !important; }
    .status-warn { color: var(--warn) !important; }
    .status-alert { color: var(--danger) !important; }

    .hero-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin-top: 1.6rem;
    }

    .hero-stat,
    .sidebar-card,
    .insight-card,
    .signal-card,
    .decision-card,
    [data-testid="stMetric"],
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: var(--radius-m) !important;
        box-shadow: none !important;
    }

    .hero-stat {
        padding: 1rem;
    }

    .hero-stat-value {
        color: var(--text);
        font-weight: 800;
        margin-top: 0.28rem;
    }

    .workspace-nav {
        margin: 1.25rem 0 1.5rem;
    }

    div[data-testid="stRadio"] > div {
        background: rgba(7, 18, 11, 0.54) !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: var(--radius-m) !important;
        gap: 0.5rem !important;
    }

    div[data-testid="stRadio"] label {
        border-radius: var(--radius-s) !important;
        color: var(--muted) !important;
        min-height: 2.55rem;
        display: flex !important;
        align-items: center;
        justify-content: center;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: rgba(16, 32, 22, 0.72) !important;
        border: 1.5px dashed var(--border-strong) !important;
        border-radius: var(--radius-m) !important;
        min-height: 164px;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, var(--accent-strong), var(--accent)) !important;
        color: #061007 !important;
        border: 1px solid rgba(190, 242, 100, 0.55) !important;
        border-radius: var(--radius-s) !important;
        box-shadow: 0 12px 28px rgba(132, 204, 22, 0.18) !important;
        font-weight: 850 !important;
        letter-spacing: 0 !important;
        min-height: 2.9rem;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 18px 36px rgba(132, 204, 22, 0.28) !important;
    }

    .stButton > button:disabled {
        background: rgba(120, 144, 112, 0.24) !important;
        color: rgba(244, 255, 242, 0.45) !important;
        border-color: rgba(120, 144, 112, 0.22) !important;
        box-shadow: none !important;
    }

    [data-testid="stMetric"] {
        padding: 1rem !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--accent-strong) !important;
        font-size: clamp(1.45rem, 2.5vw, 2rem) !important;
        letter-spacing: 0 !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        letter-spacing: 0.06em !important;
    }

    .section-shell {
        margin: 1.9rem 0 1rem;
    }

    .section-title {
        color: var(--text);
        font-size: clamp(1.45rem, 3vw, 2.15rem);
        line-height: 1.1;
        margin: 0.25rem 0 0.5rem;
        letter-spacing: 0;
    }

    .result-banner {
        background:
            linear-gradient(135deg, rgba(132, 204, 22, 0.15), rgba(19, 41, 27, 0.94)),
            var(--bg-card-strong);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-l);
        padding: clamp(1.25rem, 3vw, 2rem);
        margin-bottom: 1rem;
        box-shadow: var(--shadow-soft);
    }

    .decision-main {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(260px, 0.42fr);
        gap: 1rem;
        align-items: stretch;
    }

    .decision-state {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.36rem 0.65rem;
        margin-top: 0.7rem;
        font-size: 0.78rem;
        font-weight: 900;
        text-transform: uppercase;
    }

    .decision-release {
        color: #dcfce7;
        background: rgba(34, 197, 94, 0.16);
        border: 1px solid rgba(34, 197, 94, 0.42);
    }

    .decision-review {
        color: #fef9c3;
        background: rgba(250, 204, 21, 0.14);
        border: 1px solid rgba(250, 204, 21, 0.38);
    }

    .decision-hold {
        color: #ffe4e6;
        background: rgba(251, 113, 133, 0.14);
        border: 1px solid rgba(251, 113, 133, 0.38);
    }

    .decision-grade {
        font-size: clamp(3.1rem, 8vw, 6rem);
        line-height: 0.92;
        font-weight: 950;
        margin: 0.65rem 0 0.65rem;
        letter-spacing: 0;
    }

    .grade-a { color: #bef264; }
    .grade-b { color: #fde68a; }
    .grade-c { color: #fca5a5; }
    .moisture-low { color: #bef264; font-weight: 900; }
    .moisture-moderate { color: #fef08a; font-weight: 900; }
    .moisture-high,
    .moisture-critical { color: #fda4af; font-weight: 900; }

    .decision-card {
        padding: 1rem;
    }

    .decision-card h4,
    .signal-card h4 {
        color: var(--muted);
        margin: 0 0 0.5rem;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .decision-card p {
        color: var(--muted);
        margin: 0.45rem 0;
    }

    .compact-list,
    .tip-list {
        margin: 0.8rem 0 0;
        padding-left: 1.1rem;
        color: var(--muted);
    }

    .signal-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.85rem;
    }

    .signal-card {
        padding: 1rem;
        min-height: 142px;
    }

    .signal-value {
        color: var(--accent-strong);
        font-size: 1.35rem;
        font-weight: 900;
        line-height: 1.1;
        word-break: break-word;
    }

    .workflow-drawer {
        position: fixed;
        top: 88px;
        right: 18px;
        bottom: 18px;
        width: min(420px, calc(100vw - 36px));
        z-index: 10001;
        overflow-y: auto;
        background: rgba(7, 18, 11, 0.96);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-l);
        box-shadow: 0 30px 90px rgba(0, 0, 0, 0.46);
        padding: 1rem;
        backdrop-filter: blur(18px);
    }

    .workflow-drawer h3 {
        margin: 0.25rem 0 0.25rem;
        color: var(--text);
        font-size: 1.15rem;
        letter-spacing: 0;
    }

    .workflow-kicker {
        color: var(--accent-strong);
        font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, monospace;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .workflow-step {
        display: grid;
        grid-template-columns: 1.75rem 1fr;
        gap: 0.75rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(132, 204, 22, 0.13);
    }

    .workflow-index {
        width: 1.75rem;
        height: 1.75rem;
        border-radius: 999px;
        background: var(--accent-soft);
        border: 1px solid var(--border-strong);
        color: var(--accent-strong);
        display: grid;
        place-items: center;
        font-weight: 900;
        font-size: 0.72rem;
    }

    .workflow-title {
        color: var(--text);
        font-weight: 850;
        font-size: 0.9rem;
    }

    .workflow-copy {
        color: var(--muted);
        font-size: 0.78rem;
        line-height: 1.45;
        margin-top: 0.15rem;
    }

    .model-detail-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.6rem;
        margin-top: 0.85rem;
    }

    .model-detail {
        background: rgba(16, 32, 22, 0.70);
        border: 1px solid rgba(132, 204, 22, 0.16);
        border-radius: var(--radius-s);
        padding: 0.72rem;
    }

    .model-detail span {
        display: block;
        color: var(--muted-2);
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .model-detail strong {
        color: var(--text);
        font-size: 0.85rem;
        word-break: break-word;
    }

    .stExpander {
        border-color: var(--border-dim) !important;
    }

    @media (max-width: 900px) {
        .workstation-header {
            height: auto;
            min-height: 68px;
            padding: 0.75rem 1rem;
        }

        .brand-group {
            gap: 0.7rem;
            flex-wrap: wrap;
        }

        .workstation-viewport {
            margin-top: 112px;
            padding-inline: 1rem;
        }

        .hero-grid,
        .decision-main,
        .signal-grid {
            grid-template-columns: 1fr;
        }

        .workflow-drawer {
            top: 82px;
            left: 12px;
            right: 12px;
            width: auto;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* Compact minimal redesign: neutral field-lab interface */
    :root {
        --app-bg: #f5f6f1;
        --app-surface: #ffffff;
        --app-surface-2: #eef2e8;
        --app-ink: #172016;
        --app-muted: #64705f;
        --app-soft: #87927f;
        --app-line: #dce3d5;
        --app-line-strong: #c3d0bc;
        --app-accent: #2f6f4e;
        --app-accent-2: #0f766e;
        --app-accent-soft: #e4eee5;
        --app-warn: #b7791f;
        --app-danger: #b42318;
        --app-radius: 8px;
        --app-shadow: 0 8px 28px rgba(23, 32, 22, 0.08);
    }

    [data-testid="stHeader"],
    [data-testid="stSidebar"],
    .stDeployButton,
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        background: var(--app-bg) !important;
        color: var(--app-ink) !important;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }

    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    .workstation-header {
        position: sticky;
        top: 0;
        height: 54px;
        background: rgba(255, 255, 255, 0.92) !important;
        border-bottom: 1px solid var(--app-line) !important;
        box-shadow: 0 1px 12px rgba(23, 32, 22, 0.06) !important;
        padding: 0 clamp(1rem, 3vw, 2rem) !important;
        backdrop-filter: blur(14px);
    }

    .brand-group {
        gap: 0.8rem !important;
    }

    .brand-id {
        color: var(--app-ink) !important;
        font-family: Inter, system-ui, sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 850 !important;
        letter-spacing: 0 !important;
    }

    .mission-status,
    .trace-btn,
    .status-pill {
        background: var(--app-accent-soft) !important;
        border: 1px solid var(--app-line-strong) !important;
        color: var(--app-accent) !important;
        border-radius: 999px !important;
        font-family: Inter, system-ui, sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 750 !important;
        letter-spacing: 0 !important;
        padding: 0.32rem 0.55rem !important;
        text-transform: none !important;
        box-shadow: none !important;
    }

    .status-dot {
        background: var(--app-accent) !important;
        box-shadow: none !important;
    }

    .workstation-viewport {
        margin-top: 0 !important;
        max-width: 1240px !important;
        padding: 1rem clamp(0.85rem, 2.5vw, 2rem) 2.5rem !important;
    }

    .app-hero {
        background: var(--app-surface) !important;
        border: 1px solid var(--app-line) !important;
        border-radius: var(--app-radius) !important;
        box-shadow: var(--app-shadow) !important;
        padding: 1rem !important;
        margin: 0.8rem 0 0.8rem !important;
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 1rem;
        align-items: center;
    }

    .hero-eyebrow,
    .section-eyebrow,
    .sidebar-label,
    .hero-stat-label,
    .workflow-kicker,
    .model-detail span {
        color: var(--app-muted) !important;
        font-family: Inter, system-ui, sans-serif !important;
        font-size: 0.68rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }

    .hero-title {
        color: var(--app-ink) !important;
        font-size: clamp(1.35rem, 2.6vw, 2rem) !important;
        font-weight: 850 !important;
        line-height: 1.12 !important;
        margin-top: 0.12rem !important;
        letter-spacing: 0 !important;
        max-width: 720px !important;
    }

    .hero-body {
        color: var(--app-muted) !important;
        font-size: 0.88rem !important;
        line-height: 1.45 !important;
        margin-top: 0.35rem !important;
        max-width: 740px !important;
    }

    .hero-mini {
        color: var(--app-soft) !important;
        margin-top: 0.2rem !important;
    }

    .hero-grid {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(110px, 1fr)) !important;
        gap: 0.5rem !important;
        margin: 0 !important;
        min-width: 390px;
    }

    .hero-stat,
    .sidebar-card,
    .insight-card,
    .signal-card,
    .decision-card,
    [data-testid="stMetric"],
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background: var(--app-surface) !important;
        border: 1px solid var(--app-line) !important;
        border-radius: var(--app-radius) !important;
        box-shadow: none !important;
    }

    .hero-stat {
        padding: 0.62rem 0.7rem !important;
    }

    .hero-stat-value {
        color: var(--app-ink) !important;
        font-size: 0.84rem !important;
        font-weight: 800 !important;
        margin-top: 0.12rem !important;
        white-space: nowrap;
    }

    .workspace-nav {
        margin: 0.7rem 0 0.9rem !important;
    }

    div[data-testid="stRadio"] > div {
        background: var(--app-surface-2) !important;
        border: 1px solid var(--app-line) !important;
        border-radius: var(--app-radius) !important;
        padding: 0.22rem !important;
        gap: 0.2rem !important;
    }

    div[data-testid="stRadio"] label {
        color: var(--app-muted) !important;
        min-height: 2rem !important;
        border-radius: 6px !important;
        padding: 0.35rem 0.65rem !important;
        font-size: 0.78rem !important;
        font-weight: 760 !important;
        letter-spacing: 0 !important;
        text-transform: none !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) {
        background: var(--app-surface) !important;
        color: var(--app-accent) !important;
        box-shadow: 0 1px 6px rgba(23, 32, 22, 0.08) !important;
    }

    [data-testid="stMetric"] {
        padding: 0.72rem !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--app-ink) !important;
        font-family: Inter, system-ui, sans-serif !important;
        font-size: clamp(1rem, 1.7vw, 1.35rem) !important;
        font-weight: 850 !important;
        letter-spacing: 0 !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--app-muted) !important;
        font-size: 0.68rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.03em !important;
        text-transform: uppercase !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: var(--app-surface-2) !important;
        border: 1px dashed var(--app-line-strong) !important;
        border-radius: var(--app-radius) !important;
        min-height: 116px !important;
        padding: 0.85rem !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        background: var(--app-accent) !important;
        color: #ffffff !important;
        border: 1px solid var(--app-accent) !important;
        border-radius: 7px !important;
        min-height: 2.35rem !important;
        padding: 0.45rem 0.8rem !important;
        font-size: 0.84rem !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
        box-shadow: none !important;
        transform: none !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: var(--app-accent-2) !important;
        border-color: var(--app-accent-2) !important;
        box-shadow: none !important;
        transform: none !important;
    }

    .stButton > button:disabled {
        background: #e4e8df !important;
        border-color: var(--app-line) !important;
        color: var(--app-soft) !important;
    }

    .section-shell {
        margin: 1rem 0 0.55rem !important;
    }

    .section-title {
        color: var(--app-ink) !important;
        font-size: 1.25rem !important;
        font-weight: 850 !important;
        line-height: 1.2 !important;
        margin: 0.1rem 0 0.15rem !important;
        letter-spacing: 0 !important;
    }

    .section-copy,
    .decision-note,
    .result-subtitle,
    .sidebar-sub,
    .signal-caption,
    .workflow-copy,
    .decision-card p,
    .compact-list,
    .tip-list,
    .stCaptionContainer,
    p {
        color: var(--app-muted) !important;
        font-size: 0.84rem !important;
        line-height: 1.45 !important;
    }

    .result-banner {
        background: var(--app-surface) !important;
        border: 1px solid var(--app-line) !important;
        border-radius: var(--app-radius) !important;
        padding: 1rem !important;
        margin-bottom: 0.7rem !important;
        box-shadow: var(--app-shadow) !important;
    }

    .decision-main {
        grid-template-columns: minmax(0, 1fr) minmax(220px, 0.32fr) !important;
        gap: 0.75rem !important;
    }

    .decision-state {
        border-radius: 999px !important;
        padding: 0.25rem 0.52rem !important;
        margin-top: 0.4rem !important;
        font-size: 0.7rem !important;
        font-weight: 850 !important;
    }

    .decision-release {
        color: var(--app-accent) !important;
        background: var(--app-accent-soft) !important;
        border: 1px solid #b8d4bd !important;
    }

    .decision-review {
        color: var(--app-warn) !important;
        background: #fff7df !important;
        border: 1px solid #ead69b !important;
    }

    .decision-hold {
        color: var(--app-danger) !important;
        background: #fff1f0 !important;
        border: 1px solid #f2c7c2 !important;
    }

    .decision-grade {
        font-size: clamp(2rem, 5vw, 4rem) !important;
        font-weight: 900 !important;
        line-height: 0.95 !important;
        margin: 0.35rem 0 !important;
        letter-spacing: 0 !important;
    }

    .grade-a { color: var(--app-accent) !important; }
    .grade-b { color: var(--app-warn) !important; }
    .grade-c { color: var(--app-danger) !important; }
    .moisture-low { color: var(--app-accent) !important; font-weight: 850 !important; }
    .moisture-moderate { color: var(--app-warn) !important; font-weight: 850 !important; }
    .moisture-high,
    .moisture-critical { color: var(--app-danger) !important; font-weight: 850 !important; }

    .decision-card {
        background: var(--app-surface-2) !important;
        padding: 0.75rem !important;
    }

    .decision-card h4,
    .signal-card h4 {
        color: var(--app-muted) !important;
        margin: 0 0 0.35rem !important;
        font-size: 0.68rem !important;
        font-weight: 850 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }

    .compact-list,
    .tip-list {
        margin: 0.45rem 0 0 !important;
        padding-left: 1rem !important;
    }

    .signal-grid {
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 0.55rem !important;
    }

    .signal-card {
        padding: 0.75rem !important;
        min-height: 110px !important;
    }

    .signal-value {
        color: var(--app-ink) !important;
        font-size: 1.08rem !important;
        font-weight: 850 !important;
        line-height: 1.15 !important;
    }

    .workflow-drawer {
        top: 66px !important;
        right: 14px !important;
        bottom: 14px !important;
        width: min(360px, calc(100vw - 28px)) !important;
        background: var(--app-surface) !important;
        color: var(--app-ink) !important;
        border: 1px solid var(--app-line) !important;
        border-radius: var(--app-radius) !important;
        box-shadow: 0 18px 54px rgba(23, 32, 22, 0.16) !important;
        padding: 0.85rem !important;
        backdrop-filter: none !important;
    }

    .workflow-drawer h3 {
        color: var(--app-ink) !important;
        font-size: 1rem !important;
        line-height: 1.25 !important;
        margin: 0.15rem 0 0.2rem !important;
    }

    .workflow-step {
        grid-template-columns: 1.35rem 1fr !important;
        gap: 0.6rem !important;
        padding: 0.58rem 0 !important;
        border-bottom: 1px solid var(--app-line) !important;
    }

    .workflow-index {
        width: 1.35rem !important;
        height: 1.35rem !important;
        background: var(--app-surface-2) !important;
        border: 1px solid var(--app-line-strong) !important;
        color: var(--app-accent) !important;
        font-size: 0.63rem !important;
    }

    .workflow-title {
        color: var(--app-ink) !important;
        font-size: 0.82rem !important;
        font-weight: 820 !important;
    }

    .model-detail-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 0.42rem !important;
        margin-top: 0.65rem !important;
    }

    .model-detail {
        background: var(--app-surface-2) !important;
        border: 1px solid var(--app-line) !important;
        border-radius: 7px !important;
        padding: 0.52rem !important;
    }

    .model-detail strong {
        color: var(--app-ink) !important;
        font-size: 0.78rem !important;
        font-weight: 800 !important;
    }

    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3 {
        color: var(--app-ink) !important;
        letter-spacing: 0 !important;
    }

    .stAlert {
        border-radius: var(--app-radius) !important;
    }

    .stExpander,
    details {
        border-color: var(--app-line) !important;
        border-radius: var(--app-radius) !important;
    }

    hr {
        margin: 1rem 0 !important;
        border-color: var(--app-line) !important;
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stTable"] {
        border-radius: var(--app-radius) !important;
    }

    @media (max-width: 960px) {
        .app-hero {
            grid-template-columns: 1fr !important;
        }

        .hero-grid,
        .decision-main,
        .signal-grid {
            grid-template-columns: 1fr !important;
            min-width: 0 !important;
        }

        .workstation-header {
            height: auto !important;
            min-height: 54px !important;
            align-items: flex-start !important;
            padding-block: 0.55rem !important;
        }

        .workstation-viewport {
            padding-inline: 0.75rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* Final density/polish layer */
    .workstation-viewport {
        max-width: 1080px !important;
        padding-top: 0.65rem !important;
    }

    .workstation-header {
        height: 46px !important;
    }

    .brand-id {
        font-size: 0.86rem !important;
    }

    .mission-status,
    .trace-btn {
        font-size: 0.66rem !important;
        padding: 0.22rem 0.48rem !important;
    }

    .app-hero {
        padding: 0.75rem 0.85rem !important;
        margin: 0.45rem 0 0.55rem !important;
        box-shadow: 0 3px 14px rgba(23, 32, 22, 0.06) !important;
    }

    .hero-title {
        font-size: clamp(1.08rem, 2vw, 1.45rem) !important;
        line-height: 1.15 !important;
    }

    .hero-body,
    .hero-mini {
        font-size: 0.76rem !important;
        line-height: 1.35 !important;
    }

    .hero-grid {
        min-width: 318px !important;
        gap: 0.38rem !important;
    }

    .hero-stat {
        padding: 0.44rem 0.5rem !important;
    }

    .hero-stat-label,
    .section-eyebrow,
    .workflow-kicker,
    .model-detail span {
        font-size: 0.6rem !important;
    }

    .hero-stat-value {
        font-size: 0.74rem !important;
    }

    .workspace-nav {
        margin: 0.45rem 0 0.55rem !important;
    }

    div[data-testid="stRadio"] label {
        min-height: 1.78rem !important;
        font-size: 0.72rem !important;
        padding: 0.26rem 0.48rem !important;
    }

    [data-testid="stMetric"] {
        padding: 0.52rem 0.58rem !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1rem !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.6rem !important;
    }

    .stSlider {
        padding-top: 0 !important;
    }

    .stSlider label,
    .stFileUploader label,
    .stSelectbox label,
    .stTextArea label {
        font-size: 0.74rem !important;
        color: var(--app-muted) !important;
        font-weight: 750 !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 88px !important;
        padding: 0.58rem !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 2.05rem !important;
        font-size: 0.76rem !important;
        padding: 0.35rem 0.62rem !important;
    }

    .section-shell {
        margin: 0.75rem 0 0.38rem !important;
    }

    .section-title,
    .stMarkdown h2,
    h2 {
        font-size: 1.02rem !important;
    }

    .section-copy,
    .decision-note,
    .result-subtitle,
    .signal-caption,
    .workflow-copy,
    .decision-card p,
    .compact-list,
    .tip-list,
    .stCaptionContainer,
    p {
        font-size: 0.76rem !important;
        line-height: 1.34 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0.65rem !important;
    }

    .result-banner {
        padding: 0.72rem !important;
        margin-bottom: 0.48rem !important;
        box-shadow: 0 4px 16px rgba(23, 32, 22, 0.06) !important;
    }

    .decision-main {
        grid-template-columns: minmax(0, 1fr) minmax(180px, 0.28fr) !important;
        gap: 0.55rem !important;
    }

    .decision-state {
        margin-top: 0.25rem !important;
        font-size: 0.62rem !important;
        padding: 0.18rem 0.42rem !important;
    }

    .decision-grade {
        font-size: clamp(1.25rem, 3vw, 2rem) !important;
        margin: 0.22rem 0 !important;
        line-height: 1 !important;
    }

    .decision-card {
        padding: 0.52rem !important;
    }

    .decision-card h4,
    .signal-card h4 {
        font-size: 0.6rem !important;
        margin-bottom: 0.22rem !important;
    }

    .compact-list,
    .tip-list {
        margin-top: 0.32rem !important;
    }

    .signal-grid {
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 0.4rem !important;
    }

    .signal-card {
        min-height: 86px !important;
        padding: 0.52rem !important;
    }

    .signal-value {
        font-size: 0.92rem !important;
    }

    .workflow-drawer {
        top: 56px !important;
        width: min(320px, calc(100vw - 24px)) !important;
        padding: 0.68rem !important;
    }

    .workflow-step {
        grid-template-columns: 1.15rem 1fr !important;
        gap: 0.48rem !important;
        padding: 0.46rem 0 !important;
    }

    .workflow-index {
        width: 1.15rem !important;
        height: 1.15rem !important;
        font-size: 0.55rem !important;
    }

    .workflow-title {
        font-size: 0.74rem !important;
    }

    .model-detail-grid {
        gap: 0.32rem !important;
    }

    .model-detail {
        padding: 0.42rem !important;
    }

    .model-detail strong {
        font-size: 0.7rem !important;
    }

    .stImage img {
        border-radius: 7px;
    }

    .element-container {
        margin-bottom: 0.22rem !important;
    }

    hr {
        margin: 0.7rem 0 !important;
    }

    @media (max-width: 960px) {
        .hero-grid,
        .decision-main,
        .signal-grid {
            grid-template-columns: 1fr !important;
            min-width: 0 !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* Full dark operations console polish */
    :root {
        color-scheme: dark;
        --ui-bg: #07100e;
        --ui-bg-deep: #030807;
        --ui-panel: #0d1714;
        --ui-panel-raised: #111e1a;
        --ui-panel-soft: #14231f;
        --ui-ink: #f0f7f2;
        --ui-muted: #a8b8ad;
        --ui-faint: #6f8176;
        --ui-line: rgba(150, 177, 158, 0.18);
        --ui-line-strong: rgba(151, 208, 171, 0.34);
        --ui-accent: #68d391;
        --ui-accent-strong: #a7f3d0;
        --ui-accent-soft: rgba(104, 211, 145, 0.14);
        --ui-gold: #f7c948;
        --ui-red: #fb7185;
        --ui-cyan: #67e8f9;
        --ui-radius: 8px;
        --ui-shadow: 0 18px 50px rgba(0, 0, 0, 0.34), 0 1px 0 rgba(255, 255, 255, 0.03) inset;
        --app-muted: var(--ui-muted);
        --accent: var(--ui-accent);
        --muted: var(--ui-muted);
        --text: var(--ui-ink);
        --border: var(--ui-line);
    }

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        background:
            linear-gradient(rgba(148, 163, 184, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(148, 163, 184, 0.028) 1px, transparent 1px),
            linear-gradient(180deg, #0a1613 0%, #07100e 48%, #030807 100%) !important;
        background-size: 28px 28px, 28px 28px, auto !important;
        color: var(--ui-ink) !important;
        font-size: 16px !important;
    }

    .workstation-header {
        position: sticky !important;
        top: 0 !important;
        height: 62px !important;
        background: rgba(7, 16, 14, 0.88) !important;
        border-bottom: 1px solid var(--ui-line) !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.28) !important;
        backdrop-filter: blur(18px) saturate(140%) !important;
        z-index: 10000 !important;
    }

    .brand-id {
        color: var(--ui-ink) !important;
        font-size: 0.98rem !important;
        font-weight: 900 !important;
    }

    .mission-status,
    .trace-btn {
        background: var(--ui-accent-soft) !important;
        border: 1px solid var(--ui-line-strong) !important;
        color: var(--ui-accent-strong) !important;
        font-size: 0.72rem !important;
        padding: 0.36rem 0.62rem !important;
    }

    .status-dot {
        width: 7px !important;
        height: 7px !important;
        background: var(--ui-accent) !important;
        box-shadow: 0 0 18px rgba(104, 211, 145, 0.85) !important;
    }

    .workstation-viewport {
        max-width: 1260px !important;
        margin-top: 0 !important;
        padding: 1.15rem clamp(1rem, 3vw, 2rem) 3rem !important;
    }

    .app-hero {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(280px, 390px) !important;
        gap: clamp(1rem, 3vw, 2rem) !important;
        align-items: stretch !important;
        background:
            linear-gradient(135deg, rgba(104, 211, 145, 0.14), rgba(17, 30, 26, 0.96) 42%, rgba(6, 15, 13, 0.98)),
            var(--ui-panel-raised) !important;
        border: 1px solid var(--ui-line-strong) !important;
        border-radius: 12px !important;
        box-shadow: var(--ui-shadow) !important;
        padding: clamp(1.2rem, 3vw, 2.2rem) !important;
        margin: 0.65rem 0 1rem !important;
    }

    .hero-eyebrow,
    .section-eyebrow,
    .hero-stat-label,
    .workflow-kicker,
    .model-detail span {
        color: var(--ui-accent-strong) !important;
        font-size: 0.68rem !important;
        letter-spacing: 0.08em !important;
        font-weight: 900 !important;
    }

    .hero-title {
        color: var(--ui-ink) !important;
        font-size: clamp(2.1rem, 5vw, 4.8rem) !important;
        font-weight: 900 !important;
        line-height: 0.98 !important;
        max-width: 760px !important;
    }

    .hero-body,
    .hero-mini,
    .section-copy,
    .decision-note,
    .result-subtitle,
    .signal-caption,
    .workflow-copy,
    .decision-card p,
    .compact-list,
    .tip-list,
    .stCaptionContainer,
    p {
        color: var(--ui-muted) !important;
        font-size: 0.9rem !important;
        line-height: 1.55 !important;
    }

    .hero-body {
        max-width: 720px !important;
        margin-top: 0.9rem !important;
    }

    .hero-mini {
        color: var(--ui-faint) !important;
        margin-top: 0.45rem !important;
    }

    .hero-grid {
        min-width: 0 !important;
        grid-template-columns: 1fr !important;
        gap: 0.75rem !important;
        margin-top: 0 !important;
    }

    .hero-stat {
        background: rgba(7, 16, 14, 0.52) !important;
        border: 1px solid var(--ui-line) !important;
        border-left: 3px solid var(--ui-accent) !important;
        border-radius: var(--ui-radius) !important;
        padding: 0.92rem 1rem !important;
    }

    .hero-stat-value {
        color: var(--ui-ink) !important;
        font-size: 1.04rem !important;
        font-weight: 900 !important;
    }

    .workspace-nav {
        margin: 0.9rem 0 1.1rem !important;
    }

    div[data-testid="stRadio"] > div {
        background: rgba(13, 23, 20, 0.86) !important;
        border-color: var(--ui-line) !important;
        padding: 0.28rem !important;
        box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset !important;
    }

    div[data-testid="stRadio"] label {
        min-height: 2.45rem !important;
        font-size: 0.78rem !important;
        padding: 0.42rem 0.75rem !important;
        color: var(--ui-muted) !important;
    }

    div[data-testid="stRadio"] label:hover {
        color: var(--ui-ink) !important;
        background: rgba(104, 211, 145, 0.08) !important;
    }

    [data-testid="stMetric"],
    .sidebar-card,
    .insight-card,
    .signal-card,
    .decision-card,
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background: linear-gradient(180deg, rgba(17, 30, 26, 0.98), rgba(13, 23, 20, 0.98)) !important;
        border: 1px solid var(--ui-line) !important;
        border-radius: var(--ui-radius) !important;
        box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset !important;
    }

    [data-testid="stMetric"] {
        padding: 0.9rem 1rem !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--ui-accent-strong) !important;
        font-size: 1.35rem !important;
        font-weight: 900 !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--ui-faint) !important;
        font-size: 0.66rem !important;
        font-weight: 900 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 1.05rem !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 2.75rem !important;
        border-radius: var(--ui-radius) !important;
        background: linear-gradient(135deg, var(--ui-accent-strong), var(--ui-accent)) !important;
        border-color: rgba(167, 243, 208, 0.72) !important;
        color: #04100c !important;
        font-size: 0.86rem !important;
        font-weight: 900 !important;
        box-shadow: 0 14px 34px rgba(16, 185, 129, 0.18) !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        filter: brightness(1.04) !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button:disabled {
        background: rgba(111, 129, 118, 0.22) !important;
        border-color: var(--ui-line) !important;
        color: var(--ui-faint) !important;
        box-shadow: none !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 150px !important;
        background: rgba(7, 16, 14, 0.58) !important;
        border: 1px dashed var(--ui-line-strong) !important;
        border-radius: 10px !important;
        color: var(--ui-muted) !important;
    }

    .section-shell {
        margin: 1.4rem 0 0.7rem !important;
    }

    .section-title,
    h2,
    .stMarkdown h2 {
        font-size: clamp(1.35rem, 2vw, 1.9rem) !important;
        color: var(--ui-ink) !important;
        font-weight: 900 !important;
        line-height: 1.12 !important;
    }

    .result-banner {
        background:
            linear-gradient(135deg, rgba(104, 211, 145, 0.12), rgba(17, 30, 26, 0.98) 44%, rgba(7, 16, 14, 0.98)) !important;
        border: 1px solid var(--ui-line-strong) !important;
        border-radius: 12px !important;
        box-shadow: var(--ui-shadow) !important;
        padding: clamp(1.1rem, 2.5vw, 1.8rem) !important;
    }

    .decision-main {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(260px, 0.38fr) !important;
        gap: 1rem !important;
    }

    .decision-state {
        font-size: 0.72rem !important;
        padding: 0.32rem 0.58rem !important;
    }

    .decision-grade {
        font-size: clamp(2.6rem, 7vw, 5.2rem) !important;
        margin: 0.5rem 0 !important;
        line-height: 0.94 !important;
    }

    .decision-card {
        background: rgba(7, 16, 14, 0.50) !important;
        padding: 1rem !important;
    }

    .decision-card h4,
    .signal-card h4 {
        color: var(--ui-faint) !important;
        font-size: 0.68rem !important;
        font-weight: 900 !important;
    }

    .compact-list {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.35rem 1rem;
        margin-top: 0.8rem !important;
    }

    .signal-grid {
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 0.75rem !important;
    }

    .signal-card {
        padding: 0.95rem !important;
        min-height: 132px !important;
    }

    .signal-value {
        color: var(--ui-accent-strong) !important;
        font-size: 1.25rem !important;
    }

    .workflow-drawer {
        top: 76px !important;
        width: min(390px, calc(100vw - 24px)) !important;
        background: rgba(13, 23, 20, 0.96) !important;
        border-color: var(--ui-line-strong) !important;
        box-shadow: 0 28px 80px rgba(0, 0, 0, 0.48) !important;
        padding: 1rem !important;
    }

    .workflow-drawer h3 {
        color: var(--ui-ink) !important;
        font-size: 1.1rem !important;
    }

    .workflow-step {
        padding: 0.68rem 0 !important;
    }

    .workflow-title {
        font-size: 0.86rem !important;
    }

    .model-detail {
        background: rgba(7, 16, 14, 0.60) !important;
        padding: 0.65rem !important;
    }

    .model-detail strong {
        color: var(--ui-ink) !important;
        font-size: 0.78rem !important;
    }

    .element-container {
        margin-bottom: 0.35rem !important;
    }

    hr {
        margin: 1.2rem 0 !important;
        border-color: var(--ui-line) !important;
    }

    .stImage img {
        border: 1px solid var(--ui-line);
        border-radius: 10px;
        box-shadow: 0 16px 34px rgba(0, 0, 0, 0.22);
    }

    .utility-row {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        flex-wrap: wrap;
        min-height: 2.75rem;
    }

    .utility-chip {
        color: var(--ui-muted);
        border: 1px solid var(--ui-line);
        background: rgba(13, 23, 20, 0.72);
        border-radius: 999px;
        padding: 0.38rem 0.68rem;
        font-size: 0.78rem;
        font-weight: 750;
    }

    .stSlider label,
    .stFileUploader label,
    .stSelectbox label,
    .stTextArea label,
    .stCheckbox label,
    .stRadio label {
        color: var(--ui-muted) !important;
        font-weight: 800 !important;
    }

    .stSelectbox div[data-baseweb="select"] > div,
    .stTextArea textarea,
    .stTextInput input,
    input,
    textarea {
        background: rgba(7, 16, 14, 0.72) !important;
        border-color: var(--ui-line) !important;
        color: var(--ui-ink) !important;
        border-radius: var(--ui-radius) !important;
    }

    .stExpander,
    [data-testid="stExpander"] {
        background: rgba(13, 23, 20, 0.72) !important;
        border: 1px solid var(--ui-line) !important;
        border-radius: var(--ui-radius) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem !important;
        border-bottom: 1px solid var(--ui-line) !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(13, 23, 20, 0.78) !important;
        border: 1px solid var(--ui-line) !important;
        border-radius: var(--ui-radius) var(--ui-radius) 0 0 !important;
        color: var(--ui-muted) !important;
        height: 2.4rem !important;
        padding: 0 0.9rem !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--ui-accent-strong) !important;
        border-color: var(--ui-line-strong) !important;
        background: var(--ui-panel-raised) !important;
    }

    [data-testid="stDataFrame"],
    .stDataFrame,
    [data-testid="stTable"] {
        border: 1px solid var(--ui-line) !important;
        border-radius: var(--ui-radius) !important;
        overflow: hidden !important;
    }

    [data-testid="stAlert"] {
        background: rgba(17, 30, 26, 0.96) !important;
        color: var(--ui-ink) !important;
        border: 1px solid var(--ui-line) !important;
        border-radius: var(--ui-radius) !important;
    }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--ui-accent), var(--ui-cyan)) !important;
    }

    a {
        color: var(--ui-accent-strong) !important;
    }

    footer,
    #MainMenu {
        visibility: hidden !important;
    }

    @media (max-width: 960px) {
        .app-hero,
        .decision-main,
        .signal-grid,
        .compact-list {
            grid-template-columns: 1fr !important;
        }

        .workstation-header {
            height: auto !important;
            min-height: 62px !important;
            align-items: flex-start !important;
            padding-block: 0.7rem !important;
        }

        .workstation-viewport {
            padding-inline: 0.85rem !important;
        }

        .hero-title {
            font-size: clamp(1.9rem, 13vw, 3.2rem) !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* Designer reset: compact inspection console */
    :root {
        --cx-bg: #e9ece3;
        --cx-canvas: #f8f8f3;
        --cx-panel: #fffffb;
        --cx-panel-soft: #f1f4ec;
        --cx-ink: #111611;
        --cx-text: #20281f;
        --cx-muted: #697365;
        --cx-faint: #9aa493;
        --cx-line: #d4dccd;
        --cx-line-2: #bdc9b5;
        --cx-green: #2d5b43;
        --cx-green-dark: #1f4632;
        --cx-green-soft: #dfe9df;
        --cx-yellow: #9b6716;
        --cx-red: #a6362d;
        --cx-radius: 5px;
    }

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        background: var(--cx-bg) !important;
        color: var(--cx-text) !important;
    }

    .workstation-header {
        height: 38px !important;
        background: var(--cx-canvas) !important;
        border-bottom: 1px solid var(--cx-line) !important;
        padding: 0 0.85rem !important;
    }

    .brand-group {
        gap: 0.5rem !important;
    }

    .brand-id {
        color: var(--cx-ink) !important;
        font-size: 0.78rem !important;
        letter-spacing: 0 !important;
    }

    .mission-status,
    .trace-btn {
        background: var(--cx-panel-soft) !important;
        border: 1px solid var(--cx-line) !important;
        color: var(--cx-muted) !important;
        font-size: 0.58rem !important;
        border-radius: 999px !important;
        padding: 0.14rem 0.36rem !important;
    }

    .workstation-viewport {
        max-width: 980px !important;
        padding: 0.45rem 0.75rem 1.6rem !important;
    }

    .app-hero {
        background: var(--cx-panel) !important;
        border: 1px solid var(--cx-line) !important;
        border-top: 2px solid var(--cx-green) !important;
        border-left: 1px solid var(--cx-line) !important;
        border-radius: var(--cx-radius) !important;
        box-shadow: none !important;
        padding: 0.5rem 0.6rem !important;
        margin: 0.28rem 0 0.38rem !important;
        grid-template-columns: minmax(0, 1fr) 220px !important;
        gap: 0.55rem !important;
    }

    .hero-title {
        font-size: 0.96rem !important;
        font-weight: 900 !important;
        color: var(--cx-ink) !important;
    }

    .hero-body,
    .hero-mini {
        font-size: 0.66rem !important;
        color: var(--cx-muted) !important;
        line-height: 1.26 !important;
    }

    .hero-eyebrow,
    .hero-stat-label,
    .section-eyebrow,
    .workflow-kicker,
    .model-detail span {
        font-size: 0.52rem !important;
        color: var(--cx-faint) !important;
        font-weight: 900 !important;
        letter-spacing: 0.05em !important;
    }

    .hero-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 0.25rem !important;
    }

    .hero-stat {
        background: var(--cx-panel-soft) !important;
        border: 1px solid var(--cx-line) !important;
        border-radius: var(--cx-radius) !important;
        padding: 0.3rem 0.34rem !important;
    }

    .hero-stat-value {
        font-size: 0.62rem !important;
        color: var(--cx-green-dark) !important;
        font-weight: 900 !important;
    }

    .workspace-nav {
        margin: 0.28rem 0 0.36rem !important;
    }

    div[data-testid="stRadio"] > div {
        background: #dde4d5 !important;
        border: 1px solid var(--cx-line-2) !important;
        border-radius: var(--cx-radius) !important;
        padding: 0.12rem !important;
    }

    div[data-testid="stRadio"] label {
        min-height: 1.42rem !important;
        font-size: 0.64rem !important;
        padding: 0.16rem 0.36rem !important;
        border-radius: 4px !important;
        color: var(--cx-muted) !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) {
        background: var(--cx-panel) !important;
        color: var(--cx-green-dark) !important;
        box-shadow: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div,
    [data-testid="stMetric"],
    .insight-card,
    .decision-card,
    .signal-card,
    .model-detail {
        background: var(--cx-panel) !important;
        border: 1px solid var(--cx-line) !important;
        border-radius: var(--cx-radius) !important;
        box-shadow: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0.48rem !important;
    }

    [data-testid="stMetric"] {
        padding: 0.36rem 0.42rem !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--cx-green-dark) !important;
        font-size: 0.82rem !important;
        font-weight: 900 !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--cx-faint) !important;
        font-size: 0.5rem !important;
        font-weight: 900 !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        background: var(--cx-green) !important;
        border-color: var(--cx-green) !important;
        color: #fff !important;
        min-height: 1.72rem !important;
        border-radius: var(--cx-radius) !important;
        font-size: 0.68rem !important;
        font-weight: 900 !important;
        padding: 0.24rem 0.5rem !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: var(--cx-green-dark) !important;
        border-color: var(--cx-green-dark) !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 68px !important;
        padding: 0.42rem !important;
        background: var(--cx-panel-soft) !important;
        border: 1px dashed var(--cx-line-2) !important;
        border-radius: var(--cx-radius) !important;
    }

    .section-shell {
        margin: 0.46rem 0 0.22rem !important;
    }

    .section-title,
    h2,
    .stMarkdown h2 {
        font-size: 0.86rem !important;
        color: var(--cx-ink) !important;
        font-weight: 900 !important;
    }

    .section-copy,
    .decision-note,
    .signal-caption,
    .workflow-copy,
    .decision-card p,
    .compact-list,
    .tip-list,
    .stCaptionContainer,
    p {
        color: var(--cx-muted) !important;
        font-size: 0.66rem !important;
        line-height: 1.24 !important;
    }

    .result-banner {
        background: var(--cx-panel) !important;
        border: 1px solid var(--cx-line) !important;
        border-top: 2px solid var(--cx-green) !important;
        border-left: 1px solid var(--cx-line) !important;
        border-radius: var(--cx-radius) !important;
        box-shadow: none !important;
        padding: 0.46rem 0.52rem !important;
    }

    .decision-main {
        grid-template-columns: minmax(0, 1fr) 150px !important;
        gap: 0.35rem !important;
    }

    .decision-state {
        font-size: 0.5rem !important;
        padding: 0.12rem 0.3rem !important;
    }

    .decision-grade {
        font-size: 0.92rem !important;
        margin: 0.1rem 0 !important;
    }

    .decision-card {
        background: var(--cx-panel-soft) !important;
        padding: 0.34rem !important;
    }

    .decision-card h4,
    .signal-card h4 {
        color: var(--cx-faint) !important;
        font-size: 0.5rem !important;
        font-weight: 900 !important;
        margin-bottom: 0.12rem !important;
    }

    .compact-list {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        margin-top: 0.24rem !important;
        gap: 0.08rem 0.65rem !important;
    }

    .signal-grid {
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 0.28rem !important;
    }

    .signal-card {
        padding: 0.34rem !important;
        min-height: 62px !important;
    }

    .signal-value {
        color: var(--cx-green-dark) !important;
        font-size: 0.76rem !important;
    }

    .stImage img {
        max-height: 280px !important;
        object-fit: contain !important;
        background: #fff;
        border: 1px solid var(--cx-line) !important;
        border-radius: var(--cx-radius) !important;
    }

    .workflow-drawer {
        top: 46px !important;
        right: 10px !important;
        bottom: 10px !important;
        width: min(286px, calc(100vw - 20px)) !important;
        background: var(--cx-panel) !important;
        border: 1px solid var(--cx-line-2) !important;
        border-radius: var(--cx-radius) !important;
        box-shadow: 0 10px 36px rgba(17, 22, 17, 0.16) !important;
        padding: 0.46rem !important;
    }

    .workflow-drawer h3 {
        font-size: 0.8rem !important;
    }

    .workflow-step {
        grid-template-columns: 1rem 1fr !important;
        gap: 0.38rem !important;
        padding: 0.3rem 0 !important;
    }

    .workflow-index {
        width: 1rem !important;
        height: 1rem !important;
        font-size: 0.48rem !important;
    }

    .workflow-title {
        font-size: 0.62rem !important;
    }

    .model-detail-grid {
        gap: 0.24rem !important;
    }

    .model-detail {
        padding: 0.28rem !important;
        background: var(--cx-panel-soft) !important;
    }

    .model-detail strong {
        color: var(--cx-green-dark) !important;
        font-size: 0.58rem !important;
    }

    .element-container {
        margin-bottom: 0.06rem !important;
    }

    hr {
        margin: 0.36rem 0 !important;
    }

    @media (max-width: 900px) {
        .workstation-viewport {
            padding-inline: 0.5rem !important;
        }
        .app-hero,
        .decision-main,
        .signal-grid,
        .compact-list {
            grid-template-columns: 1fr !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <style>
    /* Final sizing pass: narrower workspace, larger text, calmer padding. */
    .workstation-viewport {
        max-width: 980px !important;
        padding: 1.35rem clamp(0.95rem, 2.2vw, 1.35rem) 3.5rem !important;
    }

    .app-hero {
        grid-template-columns: minmax(0, 1fr) minmax(230px, 300px) !important;
        gap: 1.15rem !important;
        padding: clamp(1.1rem, 2.1vw, 1.55rem) !important;
        margin: 0.75rem 0 1rem !important;
    }

    .hero-title {
        font-size: clamp(2.15rem, 4.4vw, 3.55rem) !important;
        line-height: 1.02 !important;
    }

    .hero-body,
    .hero-mini,
    .section-copy,
    .decision-note,
    .result-subtitle,
    .signal-caption,
    .workflow-copy,
    .decision-card p,
    .compact-list,
    .tip-list,
    .stCaptionContainer,
    p {
        font-size: 1rem !important;
        line-height: 1.58 !important;
    }

    .hero-eyebrow,
    .section-eyebrow,
    .hero-stat-label,
    .workflow-kicker,
    .model-detail span,
    [data-testid="stMetricLabel"] {
        font-size: 0.76rem !important;
    }

    .hero-stat {
        padding: 0.78rem 0.86rem !important;
    }

    .hero-stat-value {
        font-size: 1.08rem !important;
    }

    .hero-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        max-width: 760px !important;
        margin: 0 auto !important;
        width: 100% !important;
    }

    .workspace-nav {
        margin: 0.85rem 0 1rem !important;
    }

    div[data-testid="stRadio"] label {
        min-height: 2.25rem !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0.95rem !important;
    }

    [data-testid="stMetric"] {
        padding: 0.78rem 0.9rem !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 126px !important;
        padding: 0.9rem !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 2.55rem !important;
        font-size: 0.95rem !important;
        padding: 0.48rem 0.9rem !important;
    }

    .analyze-hint {
        min-height: 2.55rem;
        display: flex;
        align-items: center;
        color: var(--ui-muted);
        font-size: 0.92rem;
        line-height: 1.35;
        padding-left: 0.25rem;
    }

    .section-shell {
        margin: 1.25rem 0 0.65rem !important;
    }

    .section-title,
    h2,
    .stMarkdown h2 {
        font-size: clamp(1.45rem, 2.2vw, 1.95rem) !important;
    }

    h3,
    .stMarkdown h3 {
        font-size: 1.2rem !important;
    }

    .result-banner {
        padding: clamp(1rem, 2vw, 1.35rem) !important;
    }

    .decision-main {
        grid-template-columns: minmax(0, 1fr) minmax(220px, 0.35fr) !important;
        gap: 0.85rem !important;
    }

    .decision-grade {
        font-size: clamp(2.35rem, 6vw, 4.4rem) !important;
    }

    .signal-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 0.7rem !important;
    }

    .signal-card {
        min-height: 118px !important;
        padding: 0.85rem !important;
    }

    .visual-focus img {
        width: 100% !important;
        max-height: none !important;
        object-fit: contain !important;
    }

    .sample-image-frame {
        margin-top: 0.85rem;
        border: 1px solid var(--ui-line);
        border-radius: 10px;
        background: rgba(7, 16, 14, 0.48);
        overflow: hidden;
    }

    .sample-image-frame img {
        display: block;
        width: 100%;
        height: auto;
        max-height: 560px;
        object-fit: contain;
        background: #050a08;
    }

    .image-caption,
    .visual-caption {
        color: var(--ui-muted);
        font-size: 0.94rem;
        line-height: 1.3;
        text-align: center;
        margin: 0;
        padding: 0.6rem 0.75rem;
        border-top: 1px solid var(--ui-line);
        background: rgba(13, 23, 20, 0.72);
    }

    .visual-copy {
        color: var(--ui-muted);
        font-size: 0.98rem;
        line-height: 1.42;
        margin: 0.15rem 0 0.8rem;
    }

    .visual-placeholder {
        min-height: 336px;
        display: grid;
        place-items: center;
        text-align: center;
        border: 1px dashed var(--ui-line-strong);
        border-radius: 10px;
        background: rgba(7, 16, 14, 0.42);
        color: var(--ui-muted);
        font-size: 1rem;
        line-height: 1.35;
        padding: 1.2rem;
    }

    [data-testid="stFileUploader"] {
        margin-top: 0.55rem !important;
    }

    [data-testid="stFileUploader"] label {
        font-size: 1rem !important;
        font-weight: 850 !important;
        color: var(--ui-ink) !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 96px !important;
    }

    .image-caption,
    .visual-caption {
        color: var(--ui-muted);
        font-size: 0.92rem;
        line-height: 1.3;
        text-align: center;
        margin: 0.35rem auto 0;
    }

    .visual-copy {
        color: var(--ui-muted);
        font-size: 0.96rem;
        line-height: 1.38;
        margin: 0.2rem 0 0.75rem;
    }

    .visual-placeholder {
        min-height: 260px;
        display: grid;
        place-items: center;
        text-align: center;
        border: 1px dashed var(--ui-line-strong);
        border-radius: 10px;
        background: rgba(7, 16, 14, 0.42);
        color: var(--ui-muted);
        padding: 1.2rem;
    }

    .utility-row {
        gap: 0.5rem !important;
    }

    .utility-chip {
        font-size: 0.86rem !important;
        padding: 0.34rem 0.62rem !important;
    }

    @media (max-width: 960px) {
        .workstation-viewport {
            max-width: 100% !important;
            padding-inline: 0.85rem !important;
        }

        .app-hero,
        .decision-main {
            grid-template-columns: 1fr !important;
        }

        .signal-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        .compact-list {
            grid-template-columns: 1fr !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <style>
    /* Authoritative dark-mode pass. This sits last so every Streamlit widget and legacy polish layer stays dark. */
    :root {
        color-scheme: dark;
        --cx-bg: #07100e;
        --cx-canvas: #07100e;
        --cx-panel: #0d1714;
        --cx-panel-soft: #14231f;
        --cx-ink: #f0f7f2;
        --cx-text: #f0f7f2;
        --cx-muted: #a8b8ad;
        --cx-faint: #6f8176;
        --cx-line: rgba(150, 177, 158, 0.18);
        --cx-line-2: rgba(151, 208, 171, 0.34);
        --cx-green: #68d391;
        --cx-green-dark: #a7f3d0;
        --cx-green-soft: rgba(104, 211, 145, 0.14);
        --cx-yellow: #f7c948;
        --cx-red: #fb7185;
        --cx-radius: 8px;
        --ui-bg: #07100e;
        --ui-panel: #0d1714;
        --ui-panel-soft: #14231f;
        --ui-panel-raised: #111e1a;
        --ui-ink: #f0f7f2;
        --ui-muted: #a8b8ad;
        --ui-faint: #6f8176;
        --ui-line: rgba(150, 177, 158, 0.18);
        --ui-line-strong: rgba(151, 208, 171, 0.34);
        --ui-accent: #68d391;
        --ui-accent-strong: #a7f3d0;
        --ui-accent-soft: rgba(104, 211, 145, 0.14);
        --app-muted: var(--ui-muted);
        --accent: var(--ui-accent);
        --muted: var(--ui-muted);
        --text: var(--ui-ink);
        --border: var(--ui-line);
    }

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        background:
            linear-gradient(rgba(148, 163, 184, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(148, 163, 184, 0.028) 1px, transparent 1px),
            linear-gradient(180deg, #0a1613 0%, #07100e 48%, #030807 100%) !important;
        background-size: 28px 28px, 28px 28px, auto !important;
        color: var(--ui-ink) !important;
    }

    .workstation-header {
        position: sticky !important;
        top: 0 !important;
        height: 62px !important;
        background: rgba(7, 16, 14, 0.9) !important;
        border-bottom: 1px solid var(--ui-line) !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.28) !important;
        backdrop-filter: blur(18px) saturate(140%) !important;
    }

    .workstation-viewport {
        max-width: 1260px !important;
        margin-top: 0 !important;
        padding: 1.15rem clamp(1rem, 3vw, 2rem) 3rem !important;
    }

    .app-hero {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(280px, 390px) !important;
        gap: clamp(1rem, 3vw, 2rem) !important;
        align-items: stretch !important;
        background:
            linear-gradient(135deg, rgba(104, 211, 145, 0.14), rgba(17, 30, 26, 0.96) 42%, rgba(6, 15, 13, 0.98)),
            var(--ui-panel-raised) !important;
        border: 1px solid var(--ui-line-strong) !important;
        border-top: 1px solid var(--ui-line-strong) !important;
        border-radius: 12px !important;
        box-shadow: 0 18px 50px rgba(0, 0, 0, 0.34), 0 1px 0 rgba(255, 255, 255, 0.03) inset !important;
        padding: clamp(1.2rem, 3vw, 2.2rem) !important;
        margin: 0.65rem 0 1rem !important;
    }

    .hero-title {
        color: var(--ui-ink) !important;
        font-size: clamp(2.1rem, 5vw, 4.8rem) !important;
        line-height: 0.98 !important;
        max-width: 760px !important;
    }

    .hero-body,
    .hero-mini,
    .section-copy,
    .decision-note,
    .result-subtitle,
    .signal-caption,
    .workflow-copy,
    .decision-card p,
    .compact-list,
    .tip-list,
    .stCaptionContainer,
    p {
        color: var(--ui-muted) !important;
        font-size: 0.9rem !important;
        line-height: 1.55 !important;
    }

    .hero-grid {
        grid-template-columns: 1fr !important;
        gap: 0.75rem !important;
    }

    .hero-stat {
        background: rgba(7, 16, 14, 0.52) !important;
        border: 1px solid var(--ui-line) !important;
        border-left: 3px solid var(--ui-accent) !important;
        border-radius: var(--ui-radius) !important;
        padding: 0.92rem 1rem !important;
    }

    .hero-stat-value {
        color: var(--ui-ink) !important;
        font-size: 1.04rem !important;
    }

    .workspace-nav {
        margin: 0.9rem 0 1.1rem !important;
    }

    div[data-testid="stRadio"] > div {
        background: rgba(13, 23, 20, 0.86) !important;
        border-color: var(--ui-line) !important;
        padding: 0.28rem !important;
    }

    div[data-testid="stRadio"] label {
        min-height: 2.45rem !important;
        font-size: 0.78rem !important;
        padding: 0.42rem 0.75rem !important;
        color: var(--ui-muted) !important;
    }

    [data-testid="stMetric"],
    .sidebar-card,
    .insight-card,
    .signal-card,
    .decision-card,
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background: linear-gradient(180deg, rgba(17, 30, 26, 0.98), rgba(13, 23, 20, 0.98)) !important;
        border: 1px solid var(--ui-line) !important;
        border-top: 1px solid var(--ui-line) !important;
        border-radius: var(--ui-radius) !important;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.03) inset !important;
    }

    [data-testid="stMetric"] {
        padding: 0.9rem 1rem !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--ui-accent-strong) !important;
        font-size: 1.35rem !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 1.05rem !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 2.75rem !important;
        background: linear-gradient(135deg, var(--ui-accent-strong), var(--ui-accent)) !important;
        border-color: rgba(167, 243, 208, 0.72) !important;
        color: #04100c !important;
        font-size: 0.86rem !important;
        box-shadow: 0 14px 34px rgba(16, 185, 129, 0.18) !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 150px !important;
        background: rgba(7, 16, 14, 0.58) !important;
        border: 1px dashed var(--ui-line-strong) !important;
        border-radius: 10px !important;
    }

    .section-shell {
        margin: 1.4rem 0 0.7rem !important;
    }

    .section-title,
    h2,
    .stMarkdown h2 {
        color: var(--ui-ink) !important;
        font-size: clamp(1.35rem, 2vw, 1.9rem) !important;
        line-height: 1.12 !important;
    }

    .result-banner {
        background:
            linear-gradient(135deg, rgba(104, 211, 145, 0.12), rgba(17, 30, 26, 0.98) 44%, rgba(7, 16, 14, 0.98)) !important;
        border: 1px solid var(--ui-line-strong) !important;
        border-top: 1px solid var(--ui-line-strong) !important;
        border-radius: 12px !important;
        box-shadow: 0 18px 50px rgba(0, 0, 0, 0.34), 0 1px 0 rgba(255, 255, 255, 0.03) inset !important;
        padding: clamp(1.1rem, 2.5vw, 1.8rem) !important;
    }

    .decision-main {
        grid-template-columns: minmax(0, 1fr) minmax(260px, 0.38fr) !important;
        gap: 1rem !important;
    }

    .decision-grade {
        font-size: clamp(2.6rem, 7vw, 5.2rem) !important;
        margin: 0.5rem 0 !important;
        line-height: 0.94 !important;
    }

    .decision-card {
        background: rgba(7, 16, 14, 0.5) !important;
        padding: 1rem !important;
    }

    .compact-list {
        gap: 0.35rem 1rem !important;
        margin-top: 0.8rem !important;
    }

    .signal-grid {
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 0.75rem !important;
    }

    .signal-card {
        padding: 0.95rem !important;
        min-height: 132px !important;
    }

    .signal-value {
        color: var(--ui-accent-strong) !important;
        font-size: 1.25rem !important;
    }

    .workflow-drawer {
        top: 76px !important;
        width: min(390px, calc(100vw - 24px)) !important;
        background: rgba(13, 23, 20, 0.96) !important;
        border-color: var(--ui-line-strong) !important;
        box-shadow: 0 28px 80px rgba(0, 0, 0, 0.48) !important;
        padding: 1rem !important;
    }

    .stSelectbox div[data-baseweb="select"] > div,
    .stTextArea textarea,
    .stTextInput input,
    input,
    textarea {
        background: rgba(7, 16, 14, 0.72) !important;
        border-color: var(--ui-line) !important;
        color: var(--ui-ink) !important;
        border-radius: var(--ui-radius) !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(13, 23, 20, 0.78) !important;
        border: 1px solid var(--ui-line) !important;
        color: var(--ui-muted) !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--ui-accent-strong) !important;
        border-color: var(--ui-line-strong) !important;
        background: var(--ui-panel-raised) !important;
    }

    [data-testid="stAlert"],
    .stExpander,
    [data-testid="stExpander"] {
        background: rgba(13, 23, 20, 0.86) !important;
        color: var(--ui-ink) !important;
        border: 1px solid var(--ui-line) !important;
        border-radius: var(--ui-radius) !important;
    }

    .stImage img {
        border: 1px solid var(--ui-line) !important;
        border-radius: 10px !important;
        box-shadow: 0 16px 34px rgba(0, 0, 0, 0.22) !important;
    }

    .utility-row {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        flex-wrap: wrap;
        min-height: 2.75rem;
    }

    .utility-chip {
        color: var(--ui-muted);
        border: 1px solid var(--ui-line);
        background: rgba(13, 23, 20, 0.72);
        border-radius: 999px;
        padding: 0.38rem 0.68rem;
        font-size: 0.78rem;
        font-weight: 750;
    }

    @media (max-width: 960px) {
        .app-hero,
        .decision-main,
        .signal-grid,
        .compact-list {
            grid-template-columns: 1fr !important;
        }

        .hero-title {
            font-size: clamp(1.9rem, 13vw, 3.2rem) !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <style>
    /* Last-mile size and spacing overrides. Keep this after all theme layers. */
    .block-container {
        max-width: 1180px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding: 0 clamp(1.4rem, 5.4vw, 4.75rem) 3.5rem !important;
    }

    .workstation-viewport {
        height: 0 !important;
        max-width: 100% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding: 0 !important;
    }

    .workstation-header {
        justify-content: center !important;
        left: auto !important;
        right: auto !important;
        width: 100% !important;
        padding-left: clamp(1.5rem, 5vw, 4rem) !important;
        padding-right: clamp(1.5rem, 5vw, 4rem) !important;
        text-align: center !important;
    }

    .header-inner {
        width: min(100%, 1120px);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        flex-wrap: wrap;
        margin: 0 auto;
    }

    .brand-group,
    .header-meta {
        justify-content: center !important;
        text-align: center !important;
        flex-wrap: wrap !important;
    }

    .header-meta {
        display: flex;
        gap: 0.7rem;
        align-items: center;
    }

    .app-hero {
        grid-template-columns: minmax(0, 1fr) minmax(250px, 330px) !important;
        align-items: center !important;
        gap: clamp(0.8rem, 2.4vw, 1.4rem) !important;
        max-width: 980px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding: clamp(1.05rem, 2.2vw, 1.45rem) clamp(1.4rem, 4.2vw, 2.7rem) !important;
        text-align: left !important;
    }

    .hero-copy-block {
        max-width: 610px;
    }

    .hero-title {
        font-size: clamp(2.35rem, 4.6vw, 3.45rem) !important;
        line-height: 1 !important;
        margin: 0.15rem 0 0.55rem !important;
    }

    .hero-body,
    .hero-mini,
    .section-copy,
    .decision-note,
    .result-subtitle,
    .signal-caption,
    .workflow-copy,
    .decision-card p,
    .compact-list,
    .tip-list,
    .stCaptionContainer,
    p {
        font-size: 1.08rem !important;
        line-height: 1.44 !important;
    }

    .hero-body {
        max-width: 610px !important;
        margin: 0 !important;
    }

    .hero-mini {
        margin-top: 0.65rem !important;
        padding-top: 0.65rem !important;
        border-top: 1px solid var(--ui-line) !important;
        color: var(--ui-muted) !important;
    }

    .hero-eyebrow,
    .section-eyebrow,
    .hero-stat-label,
    .workflow-kicker,
    .model-detail span,
    [data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
    }

    .hero-eyebrow {
        color: var(--ui-accent-strong) !important;
        margin-bottom: 0.15rem !important;
    }

    .hero-stat {
        min-height: auto !important;
        padding: 0.72rem 0.88rem !important;
        text-align: left !important;
    }

    .hero-stat-value {
        font-size: 1.08rem !important;
        line-height: 1.18 !important;
    }

    .hero-grid {
        grid-template-columns: 1fr !important;
        gap: 0.5rem !important;
        max-width: 330px !important;
        width: 100% !important;
        margin: 0 !important;
    }

    .workspace-nav {
        width: min(100%, 640px) !important;
        margin: 1rem auto 0.45rem !important;
        color: var(--ui-muted);
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-align: center;
        text-transform: uppercase;
    }

    div[data-testid="stRadio"] {
        width: min(100%, 640px) !important;
        margin: 0 auto 1.1rem !important;
    }

    div[data-testid="stRadio"] > div {
        justify-content: center !important;
        gap: 0.45rem !important;
    }

    div[data-testid="stRadio"] label {
        min-height: 2.28rem !important;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
        text-align: center !important;
        border-radius: 999px !important;
    }

    .control-band {
        max-width: 920px;
        margin: 0.2rem auto 1rem;
        padding: 0.95rem clamp(1.2rem, 3.6vw, 2.4rem);
        border: 1px solid var(--ui-line);
        border-radius: 12px;
        background: linear-gradient(180deg, rgba(17, 30, 26, 0.72), rgba(13, 23, 20, 0.68));
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.03) inset;
    }

    .control-band [data-testid="stMetric"] {
        background: rgba(7, 16, 14, 0.45) !important;
    }

    .control-band .stSlider {
        padding-top: 0.1rem !important;
    }

    .control-band [data-testid="stSlider"] {
        max-width: 320px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    .control-title {
        color: var(--ui-ink);
        font-size: 1.05rem;
        font-weight: 850;
        text-align: center;
        margin: 0 0 0.35rem;
    }

    .control-subtitle {
        color: var(--ui-muted);
        font-size: 0.95rem;
        line-height: 1.35;
        text-align: center;
        margin: -0.05rem auto 0.85rem;
        max-width: 520px;
    }

    div[data-testid="stSlider"] {
        max-width: 460px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    div[data-testid="stSlider"] label,
    div[data-testid="stSlider"] [data-testid="stWidgetLabel"] {
        justify-content: center !important;
        text-align: center !important;
        font-size: 1rem !important;
        font-weight: 850 !important;
        color: var(--ui-ink) !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        max-width: 1040px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 1rem clamp(1.4rem, 4vw, 2.8rem) !important;
    }

    [data-testid="stMetric"] {
        padding: 0.72rem 1rem !important;
        text-align: center !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 110px !important;
        padding: 0.95rem clamp(1.4rem, 4vw, 2.6rem) !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 2.18rem !important;
        font-size: 0.92rem !important;
        padding: 0.36rem 0.68rem !important;
    }

    .analyze-hint {
        min-height: 2.18rem;
        display: flex;
        align-items: center;
        color: var(--ui-muted);
        font-size: 0.96rem;
        line-height: 1.35;
        padding-left: 0.5rem;
    }

    .run-status {
        min-height: 2.72rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.14rem;
        padding: 0.58rem 0.8rem;
        border: 1px solid var(--ui-line);
        border-radius: 10px;
        background: rgba(13, 23, 20, 0.62);
    }

    .run-status.complete {
        border-color: rgba(104, 211, 145, 0.42);
        background: rgba(20, 83, 45, 0.22);
    }

    .run-status-title {
        color: var(--ui-ink);
        font-size: 0.96rem;
        font-weight: 850;
        line-height: 1.12;
    }

    .run-status-copy {
        color: var(--ui-muted);
        font-size: 0.92rem;
        line-height: 1.25;
    }

    .visual-action-divider {
        height: 1px;
        margin: 0.95rem 0 0.75rem;
        background: linear-gradient(90deg, transparent, var(--ui-line-strong), transparent);
    }

    .result-transition {
        max-width: 980px;
        height: 1px;
        margin: 1.15rem auto 0.9rem;
        background: linear-gradient(90deg, transparent, var(--ui-line-strong), transparent);
    }

    .result-intro-shell {
        max-width: 760px;
        margin: 0 auto 0.45rem;
        text-align: left;
    }

    .result-intro-title {
        color: var(--ui-ink);
        font-size: clamp(1.6rem, 2.2vw, 2rem);
        font-weight: 900;
        line-height: 1.06;
        margin: 0.14rem 0 0.25rem;
    }

    .result-intro-copy {
        color: var(--ui-muted);
        font-size: 1.02rem;
        line-height: 1.38;
        max-width: 620px;
    }

    .section-shell {
        max-width: 760px !important;
        margin: 1.25rem auto 0.75rem !important;
        text-align: center !important;
    }

    .section-title,
    h2,
    .stMarkdown h2 {
        font-size: clamp(1.5rem, 2.1vw, 1.85rem) !important;
    }

    h3,
    .stMarkdown h3 {
        font-size: 1.2rem !important;
    }

    .result-banner {
        padding: clamp(1.05rem, 2.2vw, 1.45rem) clamp(1.25rem, 3.2vw, 2rem) !important;
        max-width: 980px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        text-align: left !important;
    }

    .decision-main {
        grid-template-columns: minmax(0, 1.2fr) minmax(260px, 0.48fr) !important;
        gap: 0.95rem !important;
        align-items: stretch !important;
    }

    .decision-summary-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-bottom: 0.25rem;
    }

    .decision-confidence {
        color: var(--ui-muted);
        font-size: 0.92rem;
        font-weight: 800;
        padding: 0.28rem 0.56rem;
        border: 1px solid var(--ui-line);
        border-radius: 999px;
        background: rgba(7, 16, 14, 0.45);
    }

    .decision-grade {
        font-size: clamp(2.25rem, 5vw, 3.8rem) !important;
        margin: 0.12rem 0 0.35rem !important;
        line-height: 0.98 !important;
    }

    .decision-card {
        padding: 0.95rem 1rem !important;
        border-radius: 10px !important;
        background: rgba(7, 16, 14, 0.48) !important;
    }

    .decision-card h4 {
        margin: 0 0 0.5rem !important;
        font-size: 1.08rem !important;
        line-height: 1.15 !important;
    }

    .compact-list {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 0.45rem !important;
        margin: 0.9rem 0 0 !important;
        padding: 0.85rem 0 0 !important;
        border-top: 1px solid var(--ui-line) !important;
        list-style: none !important;
    }

    .compact-list li {
        margin: 0 !important;
        padding: 0.55rem 0.7rem !important;
        border: 1px solid var(--ui-line) !important;
        border-radius: 8px !important;
        background: rgba(13, 23, 20, 0.62) !important;
        color: var(--ui-muted) !important;
        font-size: 0.94rem !important;
        line-height: 1.28 !important;
    }

    .reject-list {
        margin-top: 0.75rem;
        padding: 0.75rem;
        border: 1px solid rgba(251, 113, 133, 0.32);
        border-radius: 10px;
        background: rgba(127, 29, 29, 0.18);
    }

    .reject-list-title {
        color: #fecdd3;
        font-size: 0.82rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }

    .reject-list ul {
        margin: 0;
        padding-left: 1rem;
        color: #fecdd3;
        font-size: 0.94rem;
        line-height: 1.35;
    }

    .signal-grid {
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 0.5rem !important;
        max-width: 1040px !important;
        margin: 0.45rem auto 0 !important;
    }

    .signal-card {
        min-height: 132px !important;
        padding: 0.78rem 0.82rem !important;
        text-align: left !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        gap: 0.28rem !important;
    }

    .signal-card h4 {
        font-size: 1rem !important;
        line-height: 1.15 !important;
        margin: 0 !important;
        color: var(--ui-ink) !important;
        letter-spacing: 0 !important;
        text-transform: none !important;
    }

    .signal-value {
        font-size: clamp(1.35rem, 2.1vw, 1.8rem) !important;
        line-height: 1.02 !important;
        margin: 0.05rem 0 !important;
    }

    .signal-caption {
        font-size: 0.9rem !important;
        line-height: 1.3 !important;
        color: var(--ui-muted) !important;
        margin: 0 !important;
    }

    .signal-section-head {
        max-width: 1040px;
        margin: 0.9rem auto 0.35rem;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
    }

    .signal-section-title {
        color: var(--ui-ink);
        font-size: 1.35rem;
        line-height: 1.12;
        font-weight: 900;
        margin: 0.12rem 0 0;
    }

    .signal-section-note {
        max-width: 390px;
        color: var(--ui-muted);
        font-size: 0.95rem;
        line-height: 1.35;
        text-align: right;
    }

    .utility-row {
        justify-content: center !important;
        text-align: center !important;
        max-width: 760px;
        margin: 0 auto 0.65rem;
    }

    .trace-action-row {
        display: flex;
        justify-content: center;
        margin: 0 auto 0.85rem;
        max-width: 220px;
    }

    [data-testid="stAlert"] {
        max-width: 760px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        text-align: center !important;
    }

    [data-testid="stAlert"] > div {
        justify-content: center !important;
    }

    .visual-focus img {
        width: 100% !important;
        max-height: none !important;
        object-fit: contain !important;
    }

    div[data-testid="stImage"] img {
        width: 100% !important;
        height: auto !important;
        object-fit: contain !important;
    }

    div[data-testid="stImage"] {
        margin-top: 0.75rem !important;
        border: 1px solid var(--ui-line) !important;
        border-radius: 10px !important;
        background: rgba(7, 16, 14, 0.5) !important;
        overflow: hidden !important;
    }

    .sample-image-frame {
        margin-top: 0.75rem !important;
        border: 1px solid var(--ui-line) !important;
        border-radius: 10px !important;
        background: rgba(7, 16, 14, 0.5) !important;
        overflow: hidden !important;
    }

    .sample-image-frame img {
        display: block !important;
        width: 100% !important;
        height: auto !important;
        max-height: 560px !important;
        object-fit: contain !important;
        background: #050a08 !important;
    }

    .image-caption,
    .visual-caption {
        color: var(--ui-muted) !important;
        font-size: 0.94rem !important;
        line-height: 1.3 !important;
        text-align: center !important;
        margin: 0 !important;
        padding: 0.6rem 0.75rem !important;
        border-top: 1px solid var(--ui-line) !important;
        background: rgba(13, 23, 20, 0.72) !important;
    }

    .visual-copy {
        color: var(--ui-muted) !important;
        font-size: 0.98rem !important;
        line-height: 1.42 !important;
        margin: 0.15rem 0 0.8rem !important;
    }

    .visual-placeholder {
        min-height: 336px !important;
        display: grid !important;
        place-items: center !important;
        text-align: center !important;
        border: 1px dashed var(--ui-line-strong) !important;
        border-radius: 10px !important;
        background: rgba(7, 16, 14, 0.42) !important;
        color: var(--ui-muted) !important;
        font-size: 1rem !important;
        line-height: 1.35 !important;
        padding: 1.2rem !important;
    }

    [data-testid="stFileUploader"] {
        margin-top: 0.55rem !important;
    }

    [data-testid="stFileUploader"] label {
        font-size: 1rem !important;
        font-weight: 850 !important;
        color: var(--ui-ink) !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 96px !important;
    }

    [data-testid="stFileUploader"] small {
        color: var(--ui-faint) !important;
        font-size: 0.82rem !important;
    }

    [data-testid="stFileUploader"] input[type="file"] {
        display: none !important;
    }

    .utility-row {
        gap: 0.5rem !important;
    }

    .utility-chip {
        font-size: 0.86rem !important;
        padding: 0.34rem 0.62rem !important;
    }

    @media (max-width: 960px) {
        .block-container {
            max-width: 100% !important;
            padding-inline: 1.15rem !important;
        }

        .workstation-viewport {
            max-width: 100% !important;
            padding-inline: 0 !important;
        }

        .workstation-header {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            height: auto !important;
            min-height: 70px !important;
        }

        .app-hero {
            padding-inline: 1.2rem !important;
        }

        .app-hero,
        .decision-main {
            grid-template-columns: 1fr !important;
        }

        .signal-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        .app-hero,
        .hero-stat,
        .result-banner {
            text-align: center !important;
        }

        .hero-copy-block,
        .hero-body,
        .hero-grid {
            margin-left: auto !important;
            margin-right: auto !important;
        }

        .signal-section-head {
            display: block;
            text-align: center;
        }

        .signal-section-note {
            max-width: 100%;
            text-align: center;
            margin-top: 0.35rem;
        }
    }

    @media (max-width: 640px) {
        .signal-grid {
            grid-template-columns: 1fr !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_cyber_header(status: Dict[str, Any], show_trace: bool):
    provider_text = "Cloud Qwen3-VL"
    st.markdown(
        f"""
        <div class="workstation-header">
            <div class="header-inner">
                <div class="brand-group">
                    <div class="brand-id">MILLETS NOW</div>
                    <div class="mission-status">
                        <div class="status-dot"></div>
                        {html.escape(status['runtime_label'])} · {status['chunk_count']} rules
                    </div>
                </div>
                <div class="header-meta">
                    <div style="font-size: 0.76rem; color: var(--app-muted);">
                        {html.escape(provider_text)} · rule RAG
                    </div>
                    <div class="trace-btn">{"Workflow open" if show_trace else "Workflow ready"}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_cyber_hero():
    st.markdown(
        """
        <div class="app-hero">
            <div class="hero-copy-block">
                <div class="hero-eyebrow">Dark field console</div>
                <div class="hero-title">Ragi batch decision workspace</div>
                <div class="hero-body">
                    Grade the current lot, inspect moisture risk, review evidence, and capture corrections without leaving the primary workflow.
                    <div class="hero-mini">OpenCV proxies | rule retrieval | cloud Qwen3-VL | deterministic threshold gate</div>
                </div>
            </div>
            <div class="hero-grid">
                <div class="hero-stat">
                    <div class="hero-stat-label">Input</div>
                    <div class="hero-stat-value">Lot image</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-label">Decision</div>
                    <div class="hero-stat-value">Grade + moisture</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-label">Feedback</div>
                    <div class="hero-stat-value">Correction loop</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_intro(eyebrow: str, title: str, copy: str):
    st.markdown(
        f"""
        <div style="margin-bottom: 2rem;">
            <div style="color: var(--accent); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 800; text-transform: uppercase;">{html.escape(eyebrow)}</div>
            <h2 style="font-size: 1.8rem; font-weight: 900; margin: 0.2rem 0;">{html.escape(title)}</h2>
            <p style="color: var(--muted); font-size: 0.9rem; max-width: 800px;">{html.escape(copy)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _decision_state(grading_result, confidence_threshold: int) -> Dict[str, str]:
    if grading_result.reject_recommended:
        return {"label": "HOLD_BATCH", "color": "#ff5252", "note": "Do not release this lot."}
    if grading_result.moisture_risk in {MoistureRisk.HIGH, MoistureRisk.CRITICAL}:
        return {"label": "DRY_RECHECK", "color": "#ffd740", "note": "Moisture levels exceed safety guardrails."}
    if grading_result.overall_confidence < confidence_threshold:
        return {"label": "OPERATOR_REVIEW", "color": "#ffd740", "note": "Confidence level below threshold."}
    return {"label": "RELEASE_READY", "color": "#00ff41", "note": "Lot within acceptable parameters."}


def render_result_banner(grading_result, confidence_threshold: int):
    state = _decision_state(grading_result, confidence_threshold)
    grade = grading_result.quality_grade.value
    st.markdown(
        f"""
        <div class="result-banner">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="color: var(--muted); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;">DECISION_OUTPUT</div>
                    <div style="color: {state['color']}; font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 800;">{state['label']}</div>
                    <div class="decision-title" style="color: {state['color']};">GRADE_{grade}</div>
                    <div style="color: var(--text); font-size: 1.1rem; margin-top: 1rem; max-width: 600px;">{grading_result.operator_summary}</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: var(--muted); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;">CONFIDENCE</div>
                    <div style="color: var(--accent); font-family: 'JetBrains Mono', monospace; font-size: 3rem; font-weight: 800;">{grading_result.overall_confidence}%</div>
                </div>
            </div>
            <div style="margin-top: 2rem; border-top: 1px solid var(--border); padding-top: 1.5rem;">
                <div style="color: var(--muted); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; margin-bottom: 0.5rem;">CRITICAL_SIGNALS</div>
                <ul style="color: var(--muted); font-size: 0.85rem; padding-left: 1.2rem;">
                    {"".join(f"<li>{html.escape(s)}</li>" for s in grading_result.signal_highlights)}
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def init_local_stack():
    """Initialize the physics extractor and configured cloud Qwen runtime."""
    qwen_cfg = _qwen_runtime_config()
    extractor = PhysicsProxiesExtractor(
        grain_mask_threshold=50,
        morph_kernel_size=5,
    )

    pipeline = VisionRAGPipeline(
        qwen_provider=qwen_cfg["provider"],
        qwen_model=qwen_cfg["model"],
        qwen_base_url=qwen_cfg["base_url"],
        qwen_api_key=qwen_cfg["api_key"],
        vector_db_type="local",
        rag_retrieval_mode="lexical",
    )

    return extractor, pipeline


@st.cache_resource
def get_feedback_collector():
    """Keep feedback storage available without initializing the cloud client."""
    return FeedbackCollector(storage_path=str(FEEDBACK_DIR))


def _load_rag_chunk_count() -> int:
    path = RAG_INDEX_PATH
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            payload = payload.get("chunks", [])
        return len(payload) if isinstance(payload, list) else 0
    except Exception:
        return 0


@st.cache_data(ttl=20)
def get_runtime_status() -> Dict[str, Any]:
    """Return runtime and knowledge-base status for the UI."""
    qwen_cfg = _qwen_runtime_config()
    status = {
        "runtime_online": False,
        "model_ready": False,
        "runtime_label": "Offline",
        "runtime_detail": "Cloud Qwen-VL runtime is not configured.",
        "chunk_count": _load_rag_chunk_count(),
        "provider": qwen_cfg["provider"],
        "model": qwen_cfg["model"],
        "provider_label": qwen_cfg["label"],
    }
    if qwen_cfg["api_key"] and qwen_cfg["base_url"] and qwen_cfg["model"]:
        status["runtime_online"] = True
        status["model_ready"] = True
        status["runtime_label"] = "Cloud Ready"
        status["runtime_detail"] = (
            f"{qwen_cfg['provider']} is configured for {qwen_cfg['model']}. "
            "The app will call the cloud Qwen-VL endpoint during analysis."
        )
        if qwen_cfg["provider_warning"]:
            status["runtime_detail"] = f"{qwen_cfg['provider_warning']} {status['runtime_detail']}"
    else:
        missing = []
        if not qwen_cfg["api_key"]:
            missing.append("API key")
        if not qwen_cfg["base_url"]:
            missing.append("cloud base URL")
        if not qwen_cfg["model"]:
            missing.append("model")
        status["runtime_label"] = "Cloud Config Needed"
        detail = f"Missing {', '.join(missing)} for {qwen_cfg['provider']} Qwen-VL."
        if qwen_cfg["provider_warning"]:
            detail = f"{qwen_cfg['provider_warning']} {detail}"
        if qwen_cfg["local_url_blocked"]:
            detail = f"{detail} Localhost Qwen endpoints are disabled in this build."
        status["runtime_detail"] = detail
    return status


def _persist_uploaded_sample(uploaded_file) -> str:
    """Store uploaded samples on disk so inference and feedback share a stable path."""
    upload_dir = SESSION_UPLOADS_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name or "sample.jpg").suffix.lower() or ".jpg"
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
    saved_path = upload_dir / f"sample_{stamp}{suffix}"
    with saved_path.open("wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(saved_path)


def _build_auto_batch_metadata(file_signature: str, uploaded_name: str) -> Dict[str, str]:
    """Create compact read-only batch metadata for the current sample."""
    session_stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return {
        "farm_id": "AUTO",
        "batch_id": f"BATCH-{session_stamp}",
        "device_model": "Auto",
        "source_label": Path(uploaded_name or "sample").stem[:24] or "sample",
        "file_signature": file_signature,
    }


def _detect_sample_field(img_rgb: np.ndarray):
    """Detect the blue sample field / grading box when the calibration sheet is visible."""
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    lower = np.array([92, 45, 40])
    upper = np.array([135, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours_info = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours_info[0] if len(contours_info) == 2 else contours_info[1]
    if not contours:
        return None

    img_area = float(img_rgb.shape[0] * img_rgb.shape[1])
    best = None
    best_area = 0.0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < img_area * 0.02:
            continue
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.03 * peri, True)
        if len(approx) < 4:
            continue
        if area > best_area:
            best_area = area
            best = contour

    if best is None:
        return None

    x, y, w, h = cv2.boundingRect(best)
    return {"bbox": (x, y, w, h), "contour": best}


def _cuda_device_count() -> int:
    """Return CUDA device count without letting non-CUDA OpenCV wheels break the UI."""
    try:
        if not hasattr(cv2, "cuda"):
            return 0
        return int(cv2.cuda.getCudaEnabledDeviceCount())
    except Exception:
        return 0


def _scale_bbox_to_render(
    bbox: Any,
    render_scale: float,
    width: int,
    height: int,
) -> Optional[Tuple[int, int, int, int]]:
    """Scale an original-image bbox into the diagnostic render coordinate space."""
    try:
        values = np.asarray(bbox, dtype=np.float32).reshape(-1)
    except Exception:
        return None
    if values.size != 4 or width <= 0 or height <= 0:
        return None

    x, y, w, h = np.rint(values * float(render_scale)).astype(np.int32)
    x1 = int(np.clip(x, 0, max(0, width - 1)))
    y1 = int(np.clip(y, 0, max(0, height - 1)))
    x2 = int(np.clip(x + max(1, w), x1 + 1, width))
    y2 = int(np.clip(y + max(1, h), y1 + 1, height))
    return (x1, y1, x2 - x1, y2 - y1)


def _detect_sample_field_fast(hsv: np.ndarray) -> Optional[Dict[str, Any]]:
    """Detect the blue calibration field using connected-component stats, not contours."""
    lower_blue = np.array([92, 45, 40], dtype=np.uint8)
    upper_blue = np.array([135, 255, 255], dtype=np.uint8)
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_CLOSE, kernel)
    blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_OPEN, kernel)

    label_count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(
        blue_mask,
        connectivity=8,
        ltype=cv2.CV_32S,
    )
    if label_count <= 1:
        return None

    ids = np.arange(1, label_count, dtype=np.int32)
    img_area = float(hsv.shape[0] * hsv.shape[1])
    areas = stats[ids, cv2.CC_STAT_AREA].astype(np.float32)
    widths = stats[ids, cv2.CC_STAT_WIDTH].astype(np.float32)
    heights = stats[ids, cv2.CC_STAT_HEIGHT].astype(np.float32)
    valid = (
        (areas >= img_area * 0.02)
        & (widths >= hsv.shape[1] * 0.08)
        & (heights >= hsv.shape[0] * 0.08)
    )
    if not np.any(valid):
        return None

    best_id = ids[valid][int(np.argmax(areas[valid]))]
    x, y, w, h, _area = stats[best_id]
    return {"bbox": (int(x), int(y), int(w), int(h)), "source": "fast-blue-field"}


def _draw_grid_lines_vectorized(
    image_rgb: np.ndarray,
    bbox: Optional[Tuple[int, int, int, int]],
    spacing_px: Optional[float],
    color: Tuple[int, int, int],
    thickness: int = 1,
    max_lines: int = 220,
) -> None:
    """Draw all grid lines in one OpenCV call using generated line polylines."""
    if not bbox or not spacing_px or spacing_px <= 0:
        return
    x, y, w, h = np.asarray(bbox, dtype=np.int32).reshape(4).tolist()
    if w <= 0 or h <= 0:
        return

    spacing = float(spacing_px)
    line_count = int(w / spacing) + int(h / spacing)
    if line_count > max_lines:
        return

    cv2.rectangle(image_rgb, (x, y), (x + w, y + h), color, max(1, thickness))
    xs = np.rint(np.arange(float(x), float(x + w) + 0.5, spacing)).astype(np.int32)
    ys = np.rint(np.arange(float(y), float(y + h) + 0.5, spacing)).astype(np.int32)
    xs = np.clip(xs, x, x + w)
    ys = np.clip(ys, y, y + h)

    vertical = np.stack(
        (
            np.column_stack((xs, np.full_like(xs, y))),
            np.column_stack((xs, np.full_like(xs, y + h))),
        ),
        axis=1,
    )
    horizontal = np.stack(
        (
            np.column_stack((np.full_like(ys, x), ys)),
            np.column_stack((np.full_like(ys, x + w), ys)),
        ),
        axis=1,
    )
    lines = np.concatenate((vertical, horizontal), axis=0).astype(np.int32).reshape(-1, 2, 1, 2)
    if lines.size:
        cv2.polylines(image_rgb, lines, False, color, max(1, thickness), cv2.LINE_8)


def _draw_boxes_vectorized(image_rgb: np.ndarray, boxes_xywh: np.ndarray) -> None:
    """Render hundreds of grain boxes with two batched polyline calls instead of N rectangles."""
    if boxes_xywh.size == 0:
        return

    boxes = boxes_xywh.astype(np.int32, copy=False)
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 0] + boxes[:, 2]
    y2 = boxes[:, 1] + boxes[:, 3]
    polygons = np.stack(
        (
            np.column_stack((x1, y1)),
            np.column_stack((x2, y1)),
            np.column_stack((x2, y2)),
            np.column_stack((x1, y2)),
        ),
        axis=1,
    ).astype(np.int32).reshape(-1, 4, 1, 2)

    primary_count = min(20, len(polygons))
    line_thickness = max(1, int(round(max(image_rgb.shape[:2]) / 900.0)))
    if primary_count:
        cv2.polylines(image_rgb, polygons[:primary_count], True, (70, 255, 160), line_thickness, cv2.LINE_8)
    if len(polygons) > primary_count:
        cv2.polylines(image_rgb, polygons[primary_count:], True, (245, 210, 95), line_thickness, cv2.LINE_8)


def _blend_masked_overlay(
    base_rgb: np.ndarray,
    mask_u8: np.ndarray,
    color_rgb: Tuple[int, int, int],
    alpha: float,
    prefer_cuda: bool,
) -> Tuple[np.ndarray, bool]:
    """
    Apply a masked color overlay with CUDA addWeighted when available.

    The mask application itself is vectorized NumPy: outside-mask pixels in the
    overlay remain identical to the base, so cv2.addWeighted changes only the
    target region while still running as one contiguous matrix operation.
    """
    if mask_u8 is None or mask_u8.size == 0 or cv2.countNonZero(mask_u8) == 0:
        return base_rgb, False

    overlay_rgb = base_rgb.copy()
    overlay_rgb[mask_u8 > 0] = color_rgb

    if prefer_cuda:
        try:
            gpu_base = cv2.cuda_GpuMat()
            gpu_overlay = cv2.cuda_GpuMat()
            gpu_base.upload(base_rgb)
            gpu_overlay.upload(overlay_rgb)
            gpu_blended = cv2.cuda.addWeighted(gpu_overlay, float(alpha), gpu_base, 1.0 - float(alpha), 0.0)
            return gpu_blended.download(), True
        except Exception as exc:
            logger.debug("CUDA masked overlay blend unavailable; falling back to CPU addWeighted: %s", exc)

    return cv2.addWeighted(overlay_rgb, float(alpha), base_rgb, 1.0 - float(alpha), 0.0), False


def _component_boxes_and_clump_mask(
    grain_mask: np.ndarray,
    proxies: Optional[Dict[str, Any]],
    max_boxes: int,
) -> Tuple[np.ndarray, np.ndarray, int]:
    """Return sorted component boxes plus a vectorized large-component moisture-clump mask."""
    img_area = float(grain_mask.shape[0] * grain_mask.shape[1])
    label_count, labels, stats, _centroids = cv2.connectedComponentsWithStats(
        grain_mask,
        connectivity=8,
        ltype=cv2.CV_32S,
    )
    empty_mask = np.zeros(grain_mask.shape, dtype=np.uint8)
    if label_count <= 1:
        return np.empty((0, 4), dtype=np.int32), empty_mask, 0

    ids = np.arange(1, label_count, dtype=np.int32)
    areas = stats[ids, cv2.CC_STAT_AREA].astype(np.float32)
    widths = stats[ids, cv2.CC_STAT_WIDTH].astype(np.float32)
    heights = stats[ids, cv2.CC_STAT_HEIGHT].astype(np.float32)
    min_area = max(18.0, img_area * 0.00003)
    max_area = img_area * 0.35
    valid = (areas >= min_area) & (areas <= max_area) & (widths >= 3) & (heights >= 3)
    if not np.any(valid):
        return np.empty((0, 4), dtype=np.int32), empty_mask, 0

    valid_ids = ids[valid]
    valid_areas = stats[valid_ids, cv2.CC_STAT_AREA].astype(np.float32)
    order = np.argsort(valid_areas)[::-1]
    selected_ids = valid_ids[order[: max(1, int(max_boxes))]]
    boxes_xywh = stats[selected_ids, :4].astype(np.int32)

    clumping_density = float(((proxies or {}).get("clumping", {}) or {}).get("density") or 0.0)
    median_area = float(np.median(valid_areas))
    clump_factor = 2.1 if clumping_density >= 0.18 else 3.0
    clump_threshold = max(median_area * clump_factor, min_area * 6.0)
    clump_ids = valid_ids[valid_areas >= clump_threshold]
    if clump_ids.size == 0:
        return boxes_xywh, empty_mask, 0

    # Lookup-table indexing turns a label matrix into a clump mask without looping labels.
    lookup = np.zeros(label_count, dtype=np.uint8)
    lookup[clump_ids] = 255
    clump_mask = lookup[labels]
    return boxes_xywh, clump_mask, int(clump_ids.size)


def _foreign_matter_mask_fast(
    hsv: np.ndarray,
    grain_mask: np.ndarray,
    field_mask: Optional[np.ndarray],
) -> Tuple[np.ndarray, int]:
    """
    Build a compact red-alert mask for stones/foreign material.

    The candidate logic intentionally avoids Python pixel loops. It combines
    hue/saturation/value tests, then filters connected components by shape so
    printed calibration-grid lines are not promoted as stones.
    """
    h_channel = hsv[:, :, 0]
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]

    neighborhood_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
    grain_neighborhood = cv2.dilate(grain_mask, neighborhood_kernel) > 0
    if field_mask is not None and cv2.countNonZero(field_mask) > 0:
        # Calibration sheets contain printed grid lines and labels. Searching
        # only near the segmented grain layer prevents the red alert mask from
        # lighting up every empty grid/text mark in the field.
        field_pixels = field_mask > 0
        search_mask = field_pixels & grain_neighborhood
        if int(np.count_nonzero(search_mask)) < max(100, int(np.count_nonzero(field_pixels) * 0.01)):
            search_mask = field_pixels
    else:
        search_mask = grain_neighborhood

    grain_pixels = grain_mask > 0
    non_grain_search = search_mask & ~grain_pixels
    compact_dark = (v_channel < 56) & (s_channel < 140)
    compact_gray_stone = (s_channel < 36) & (v_channel < 150)
    red_or_organic_debris = (((h_channel < 7) | (h_channel > 170)) & (s_channel > 95) & (v_channel > 45))
    green_debris = ((h_channel > 35) & (h_channel < 95) & (s_channel > 75) & (v_channel > 45))
    candidate = non_grain_search & (compact_dark | compact_gray_stone | red_or_organic_debris | green_debris)

    candidate_mask = (candidate.astype(np.uint8) * 255)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    candidate_mask = cv2.morphologyEx(candidate_mask, cv2.MORPH_OPEN, kernel)

    label_count, labels, stats, _centroids = cv2.connectedComponentsWithStats(
        candidate_mask,
        connectivity=8,
        ltype=cv2.CV_32S,
    )
    if label_count <= 1:
        return np.zeros(candidate_mask.shape, dtype=np.uint8), 0

    ids = np.arange(1, label_count, dtype=np.int32)
    img_area = float(candidate_mask.shape[0] * candidate_mask.shape[1])
    areas = stats[ids, cv2.CC_STAT_AREA].astype(np.float32)
    widths = stats[ids, cv2.CC_STAT_WIDTH].astype(np.float32)
    heights = stats[ids, cv2.CC_STAT_HEIGHT].astype(np.float32)
    aspect = np.maximum(widths, heights) / np.maximum(1.0, np.minimum(widths, heights))
    fill_ratio = areas / np.maximum(1.0, widths * heights)
    valid = (
        (areas >= max(28.0, img_area * 0.000012))
        & (areas <= img_area * 0.018)
        & (widths >= 4)
        & (heights >= 4)
        & (aspect <= 3.2)
        & (fill_ratio >= 0.28)
    )
    if not np.any(valid):
        return np.zeros(candidate_mask.shape, dtype=np.uint8), 0

    valid_ids = ids[valid]
    valid_areas = stats[valid_ids, cv2.CC_STAT_AREA].astype(np.float32)
    foreign_ids = valid_ids[np.argsort(valid_areas)[::-1][:80]]
    lookup = np.zeros(label_count, dtype=np.uint8)
    lookup[foreign_ids] = 255
    return lookup[labels], int(foreign_ids.size)


def generate_diagnostic_overlay(
    base_image_path: str,
    proxies: Optional[Dict[str, Any]] = None,
    max_boxes: int = 600,
    max_render_side: int = 1800,
) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
    """
    Create a Streamlit-ready diagnostic overlay for grain grading.

    Architecture notes:
    - The source image is loaded from disk on every render and returned as a PIL
      image. The function never writes raw NumPy matrices into st.session_state;
      callers should keep only small metadata such as paths and scalar proxies.
    - CUDA is used opportunistically for the bandwidth-heavy stages that benefit
      most on an RTX 3050: resize, BGR->RGB/HSV conversion, and addWeighted
      overlay blending. OpenCV wheels without CUDA support fall back through the
      same vectorized CPU path without changing the UI contract.
    - Per-pixel decisions are NumPy/OpenCV matrix operations. Component stats,
      lookup-table masks, and batched polylines replace Python loops over pixels
      or hundreds of boxes.
    """
    stats: Dict[str, Any] = {
        "boxes": 0,
        "coverage": 0.0,
        "cuda": False,
        "render_scale": 1.0,
        "moisture_clumps": 0,
        "foreign_components": 0,
    }

    img_bgr_source = cv2.imread(str(base_image_path), cv2.IMREAD_COLOR)
    if img_bgr_source is None:
        return None, stats

    source_h, source_w = img_bgr_source.shape[:2]
    if source_w <= 0 or source_h <= 0:
        return None, stats

    longest_side = max(source_w, source_h)
    render_scale = min(1.0, float(max_render_side) / float(longest_side)) if max_render_side else 1.0
    render_w = max(1, int(round(source_w * render_scale)))
    render_h = max(1, int(round(source_h * render_scale)))
    stats["render_scale"] = render_scale

    cuda_preferred = _cuda_device_count() > 0
    cuda_used_for_prep = False
    try:
        if not cuda_preferred:
            raise RuntimeError("No CUDA-enabled OpenCV device available")

        gpu_bgr = cv2.cuda_GpuMat()
        gpu_bgr.upload(img_bgr_source)
        if render_scale < 1.0:
            gpu_bgr = cv2.cuda.resize(gpu_bgr, (render_w, render_h), interpolation=cv2.INTER_AREA)

        # Both conversions read the same GpuMat, avoiding two large CPU passes.
        gpu_rgb = cv2.cuda.cvtColor(gpu_bgr, cv2.COLOR_BGR2RGB)
        gpu_hsv = cv2.cuda.cvtColor(gpu_bgr, cv2.COLOR_BGR2HSV)
        img_rgb = gpu_rgb.download()
        hsv = gpu_hsv.download()
        cuda_used_for_prep = True
    except Exception as exc:
        logger.debug("CUDA diagnostic prep unavailable; using CPU path: %s", exc)
        img_bgr = img_bgr_source
        if render_scale < 1.0:
            img_bgr = cv2.resize(img_bgr_source, (render_w, render_h), interpolation=cv2.INTER_AREA)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    calibration = (proxies or {}).get("calibration", {}) or {}
    calibrated_geometry = (proxies or {}).get("calibrated_geometry", {}) or {}
    grid_box_analysis = (proxies or {}).get("grid_box_analysis", {}) or {}
    h, w = img_rgb.shape[:2]

    sample_field = None
    field_mask = None
    proxy_field = (proxies or {}).get("sample_field", {}) or {}
    if proxy_field.get("bbox"):
        scaled_bbox = _scale_bbox_to_render(proxy_field["bbox"], render_scale, w, h)
        if scaled_bbox:
            sample_field = {"bbox": scaled_bbox, "source": proxy_field.get("source", "proxy-field")}
    if sample_field is None:
        sample_field = _detect_sample_field_fast(hsv)

    if sample_field is not None:
        x, y, box_w, box_h = sample_field["bbox"]
        field_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.rectangle(field_mask, (x, y), (x + box_w, y + box_h), 255, thickness=-1)

    lower_grain = np.array([10, 30, 60], dtype=np.uint8)
    upper_grain = np.array([30, 130, 255], dtype=np.uint8)
    grain_mask = cv2.inRange(hsv, lower_grain, upper_grain)
    grain_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    grain_mask = cv2.morphologyEx(grain_mask, cv2.MORPH_CLOSE, grain_kernel)
    grain_mask = cv2.morphologyEx(grain_mask, cv2.MORPH_OPEN, grain_kernel)

    if field_mask is not None:
        grain_mask = cv2.bitwise_and(grain_mask, field_mask)

    denominator = cv2.countNonZero(field_mask) if field_mask is not None else grain_mask.size
    coverage = float(cv2.countNonZero(grain_mask) / max(1, denominator))

    if coverage < 0.02:
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        _, grain_mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        grain_mask = cv2.morphologyEx(grain_mask, cv2.MORPH_OPEN, grain_kernel)
        if field_mask is not None:
            grain_mask = cv2.bitwise_and(grain_mask, field_mask)
        coverage = float(cv2.countNonZero(grain_mask) / max(1, denominator))

    boxes_xywh, moisture_mask, moisture_clumps = _component_boxes_and_clump_mask(
        grain_mask,
        proxies,
        max_boxes=max_boxes,
    )
    foreign_mask, foreign_components = _foreign_matter_mask_fast(hsv, grain_mask, field_mask)

    annotated = img_rgb.copy()

    # Blue moisture clumps at alpha 0.6, then red stones/foreign matter at alpha 0.8.
    annotated, cuda_blend_1 = _blend_masked_overlay(
        annotated,
        moisture_mask,
        (0, 115, 255),
        0.60,
        prefer_cuda=cuda_preferred,
    )
    annotated, cuda_blend_2 = _blend_masked_overlay(
        annotated,
        foreign_mask,
        (255, 0, 0),
        0.80,
        prefer_cuda=cuda_preferred,
    )
    stats["cuda"] = bool(cuda_used_for_prep or cuda_blend_1 or cuda_blend_2)

    if grid_box_analysis.get("available") and calibration.get("pixels_per_mm"):
        active_field = grid_box_analysis.get("active_field", {}) or {}
        big_sheet_grid = grid_box_analysis.get("big_sheet_grid", {}) or {}
        if big_sheet_grid.get("available"):
            grid_bbox = _scale_bbox_to_render(big_sheet_grid.get("bbox"), render_scale, w, h)
            _draw_grid_lines_vectorized(
                annotated,
                grid_bbox,
                float(big_sheet_grid.get("major_spacing_px") or 0.0) * render_scale,
                (92, 146, 255),
                thickness=1,
                max_lines=90,
            )

        active_bbox = _scale_bbox_to_render(active_field.get("bbox"), render_scale, w, h)
        px_per_mm = float(calibration.get("pixels_per_mm") or 0.0) * render_scale
        if active_bbox and px_per_mm > 0:
            _draw_grid_lines_vectorized(
                annotated,
                active_bbox,
                px_per_mm,
                (105, 125, 145),
                thickness=1,
                max_lines=240,
            )
            _draw_grid_lines_vectorized(
                annotated,
                active_bbox,
                px_per_mm * float(active_field.get("major_cell_mm") or 10.0),
                (255, 218, 105),
                thickness=1,
                max_lines=40,
            )

    _draw_boxes_vectorized(annotated, boxes_xywh)

    if sample_field is not None:
        x, y, box_w, box_h = sample_field["bbox"]
        cv2.rectangle(annotated, (x, y), (x + box_w, y + box_h), (255, 218, 105), 3)
        label = "Calibrated field"
        if calibration.get("available") and calibration.get("mm_per_pixel"):
            label = f"{label} - {float(calibration['pixels_per_mm']):.2f} px/mm"
            if calibrated_geometry.get("median_equiv_diameter_mm") is not None:
                label += f" - grain {float(calibrated_geometry['median_equiv_diameter_mm']):.2f} mm"
        cv2.putText(
            annotated,
            label,
            (x, max(24, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255, 218, 105),
            2,
            cv2.LINE_AA,
        )
    elif boxes_xywh.size:
        x1 = int(np.min(boxes_xywh[:, 0]))
        y1 = int(np.min(boxes_xywh[:, 1]))
        x2 = int(np.max(boxes_xywh[:, 0] + boxes_xywh[:, 2]))
        y2 = int(np.max(boxes_xywh[:, 1] + boxes_xywh[:, 3]))
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 218, 105), 3)
        cv2.putText(
            annotated,
            "AI grain field",
            (x1, max(24, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 218, 105),
            2,
            cv2.LINE_AA,
        )

    stats.update(
        {
            "boxes": int(len(boxes_xywh)),
            "coverage": coverage,
            "moisture_clumps": int(moisture_clumps),
            "foreign_components": int(foreign_components),
            "calibration_available": bool(calibration.get("available")),
            "pixels_per_mm": calibration.get("pixels_per_mm"),
            "mm_per_pixel": calibration.get("mm_per_pixel"),
            "source": calibration.get("source", "none"),
            "sample_field": sample_field["bbox"] if sample_field is not None else None,
            "grid_box_analysis": bool(grid_box_analysis.get("available")),
            "major_occupied_cells": (
                (grid_box_analysis.get("active_field", {}) or {}).get("major_occupied_cells")
                if grid_box_analysis.get("available")
                else None
            ),
        }
    )
    return Image.fromarray(annotated), stats


def _build_grain_detection_overlay(image_path: str, proxies: Optional[Dict[str, Any]] = None, max_boxes: int = 600):
    """Compatibility wrapper for existing UI call sites."""
    return generate_diagnostic_overlay(image_path, proxies=proxies, max_boxes=max_boxes)


def render_section_intro(eyebrow: str, title: str, copy: str):
    st.markdown(
        f"""
        <div class="section-shell">
            <div class="section-eyebrow">{html.escape(eyebrow)}</div>
            <h2 class="section-title">{html.escape(title)}</h2>
            <div class="section-copy">{html.escape(copy)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_status(status: Dict[str, Any], pending_feedback: int):
    state_class = "status-online" if status["model_ready"] else "status-warn" if status.get("runtime_online") else "status-alert"
    st.markdown(
        f"""
        <div class="sidebar-card">
            <div class="sidebar-label">Runtime</div>
            <div class="sidebar-value {state_class}">{html.escape(status['runtime_label'])}</div>
            <div class="sidebar-sub">{html.escape(status['runtime_detail'])}</div>
        </div>
        <div style="height:0.75rem"></div>
        <div class="sidebar-card">
            <div class="sidebar-label">Rules Loaded</div>
            <div class="sidebar-value">{status['chunk_count']} indexed chunks</div>
            <div class="sidebar-sub">Grading and moisture rules are ready for retrieval.</div>
        </div>
        <div style="height:0.75rem"></div>
        <div class="sidebar-card">
            <div class="sidebar-label">Corrections</div>
            <div class="sidebar-value">{pending_feedback} pending samples</div>
            <div class="sidebar-sub">Operator corrections are reused during local inference.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_theme_overrides(dark_mode: bool) -> None:
    if dark_mode:
        tokens = {
            "scheme": "dark",
            "bg": "#0b0f17",
            "bg_deep": "#060914",
            "panel": "#111827",
            "panel_soft": "#172033",
            "panel_raised": "#151f2e",
            "ink": "#f8fafc",
            "muted": "#aeb8c6",
            "faint": "#6f7b8b",
            "line": "rgba(148, 163, 184, 0.22)",
            "line_strong": "rgba(245, 158, 11, 0.42)",
            "accent": "#f59e0b",
            "accent_strong": "#fbbf24",
            "accent_soft": "rgba(245, 158, 11, 0.14)",
            "grid": "rgba(148, 163, 184, 0.035)",
            "hero": "linear-gradient(135deg, rgba(245, 158, 11, 0.13), rgba(21, 31, 46, 0.96) 42%, rgba(8, 13, 24, 0.98))",
            "shadow": "0 18px 50px rgba(0, 0, 0, 0.34), 0 1px 0 rgba(255, 255, 255, 0.03) inset",
            "header_bg": "rgba(11, 15, 23, 0.92)",
            "panel_alpha": "rgba(17, 24, 39, 0.9)",
            "panel_soft_alpha": "rgba(23, 32, 51, 0.78)",
            "image_bg": "#090d17",
            "button_text": "#111827",
            "input_bg": "#0f172a",
        }
    else:
        tokens = {
            "scheme": "light",
            "bg": "#f7f9fc",
            "bg_deep": "#edf2f8",
            "panel": "#ffffff",
            "panel_soft": "#f4f7fb",
            "panel_raised": "#ffffff",
            "ink": "#111827",
            "muted": "#475569",
            "faint": "#7c8796",
            "line": "rgba(15, 23, 42, 0.13)",
            "line_strong": "rgba(37, 99, 235, 0.32)",
            "accent": "#2563eb",
            "accent_strong": "#1d4ed8",
            "accent_soft": "rgba(37, 99, 235, 0.1)",
            "grid": "rgba(30, 41, 59, 0.035)",
            "hero": "linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(255, 255, 255, 0.98) 45%, rgba(241, 245, 249, 0.98))",
            "shadow": "0 16px 42px rgba(15, 23, 42, 0.1), 0 1px 0 rgba(255, 255, 255, 0.8) inset",
            "header_bg": "rgba(255, 255, 255, 0.94)",
            "panel_alpha": "rgba(255, 255, 255, 0.94)",
            "panel_soft_alpha": "rgba(244, 247, 251, 0.92)",
            "image_bg": "#eef2f7",
            "button_text": "#ffffff",
            "input_bg": "#ffffff",
        }

    st.markdown(
        f"""
        <style>
        :root {{
            color-scheme: {tokens["scheme"]};
            --ui-bg: {tokens["bg"]};
            --ui-bg-deep: {tokens["bg_deep"]};
            --ui-panel: {tokens["panel"]};
            --ui-panel-soft: {tokens["panel_soft"]};
            --ui-panel-raised: {tokens["panel_raised"]};
            --ui-ink: {tokens["ink"]};
            --ui-muted: {tokens["muted"]};
            --ui-faint: {tokens["faint"]};
            --ui-line: {tokens["line"]};
            --ui-line-strong: {tokens["line_strong"]};
            --ui-accent: {tokens["accent"]};
            --ui-accent-strong: {tokens["accent_strong"]};
            --ui-accent-soft: {tokens["accent_soft"]};
            --ui-cyan: #38bdf8;
            --neon-green: var(--ui-accent);
            --accent: var(--ui-accent);
            --accent-strong: var(--ui-accent-strong);
            --accent-soft: var(--ui-accent-soft);
            --muted: var(--ui-muted);
            --text: var(--ui-ink);
            --border: var(--ui-line);
            --app-muted: var(--ui-muted);
            --cx-green: var(--ui-accent);
            --cx-green-dark: var(--ui-accent-strong);
            --cx-green-soft: var(--ui-accent-soft);
        }}

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {{
            background:
                linear-gradient({tokens["grid"]} 1px, transparent 1px),
                linear-gradient(90deg, {tokens["grid"]} 1px, transparent 1px),
                linear-gradient(180deg, var(--ui-bg) 0%, var(--ui-bg-deep) 100%) !important;
            background-color: var(--ui-bg) !important;
            background-size: 28px 28px, 28px 28px, auto !important;
            color: var(--ui-ink) !important;
        }}

        .workstation-header {{
            background: {tokens["header_bg"]} !important;
            border-bottom-color: var(--ui-line) !important;
            box-shadow: {tokens["shadow"]} !important;
        }}

        .brand-id,
        .hero-eyebrow,
        .section-eyebrow,
        .status-online,
        .signal-value,
        .model-detail strong {{
            color: var(--ui-accent-strong) !important;
        }}

        .status-dot {{
            background: var(--ui-accent) !important;
            box-shadow: none !important;
        }}

        .app-hero {{
            background: {tokens["hero"]}, var(--ui-panel-raised) !important;
            border-color: var(--ui-line-strong) !important;
            box-shadow: {tokens["shadow"]} !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] > div,
        div[data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stMetric"],
        [data-testid="stMetric"] > div,
        .result-banner,
        .signal-card,
        .decision-card,
        .insight-card,
        .model-detail,
        .sidebar-card,
        .workflow-drawer,
        .utility-chip,
        .run-status,
        .visual-placeholder,
        div[data-testid="stImage"] {{
            background-color: {tokens["panel_alpha"]} !important;
            border-color: var(--ui-line) !important;
            color: var(--ui-ink) !important;
            box-shadow: {tokens["shadow"]} !important;
        }}

        .block-container,
        section[data-testid="stMain"],
        div[data-testid="stAppViewContainer"] > .main,
        div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"] {{
            background: transparent !important;
            color: var(--ui-ink) !important;
        }}

        h1, h2, h3, h4, h5, h6,
        p,
        li,
        label,
        .stMarkdown,
        .stCaptionContainer,
        [data-testid="stMarkdownContainer"],
        [data-testid="stWidgetLabel"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"] {{
            color: var(--ui-ink) !important;
        }}

        .stCaptionContainer,
        .section-copy,
        .hero-body,
        .hero-mini,
        .decision-note,
        .signal-caption,
        .run-status-copy,
        .visual-copy,
        .image-caption,
        .utility-chip,
        [data-testid="stMetricLabel"] {{
            color: var(--ui-muted) !important;
        }}

        div[data-testid="stImage"] {{
            background: {tokens["image_bg"]} !important;
        }}

        div[data-testid="stImage"] img {{
            background: {tokens["image_bg"]} !important;
        }}

        .image-caption,
        .visual-caption {{
            background: {tokens["panel_soft_alpha"]} !important;
            border-top-color: var(--ui-line) !important;
        }}

        [data-testid="stFileUploaderDropzone"],
        div[data-testid="stRadio"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="select"] > div,
        input,
        textarea {{
            background: {tokens["input_bg"]} !important;
            color: var(--ui-ink) !important;
            border-color: var(--ui-line) !important;
        }}

        [data-testid="stExpander"],
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] summary,
        [data-testid="stAlert"],
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            background: {tokens["panel_alpha"]} !important;
            border-color: var(--ui-line) !important;
            color: var(--ui-ink) !important;
        }}

        [data-testid="stAlert"] * {{
            color: var(--ui-ink) !important;
        }}

        div[data-testid="stRadio"] label {{
            background: transparent !important;
            color: var(--ui-muted) !important;
        }}

        .stButton > button,
        .stFormSubmitButton > button {{
            background: linear-gradient(135deg, var(--ui-accent-strong), var(--ui-accent)) !important;
            border-color: var(--ui-accent) !important;
            color: {tokens["button_text"]} !important;
        }}

        div[data-testid="stRadio"] label:has(input:checked),
        .decision-state,
        .utility-chip.status-online {{
            border-color: var(--ui-line-strong) !important;
            background: var(--ui-accent-soft) !important;
            color: var(--ui-accent-strong) !important;
        }}

        div[data-testid="stToggle"] label,
        div[data-testid="stToggle"] p {{
            color: var(--ui-ink) !important;
            font-weight: 800 !important;
        }}

        .image-caption,
        .visual-caption {{
            background: {tokens["panel_soft_alpha"]} !important;
        }}

        .result-transition,
        .visual-action-divider {{
            background: linear-gradient(90deg, transparent, var(--ui-line-strong), transparent) !important;
        }}

        hr {{
            border-color: var(--ui-line) !important;
        }}

        [data-testid="stProgress"] > div > div > div > div {{
            background-color: var(--ui-accent) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(status: Dict[str, Any], pending_feedback: int):
    runtime_class = "status-online" if status["model_ready"] else "status-warn" if status.get("runtime_online") else "status-alert"
    model_label = html.escape(status.get("provider_label", "qwen-vl"))
    hero_title = "Cloud lot grading, live feedback."
    st.markdown(
        f"""
        <div class="app-hero">
            <div class="hero-eyebrow">Millets Now • Ragi Lot Grader</div>
            <div class="hero-title">{hero_title}</div>
            <div class="hero-body">
                Upload one photo. The engine checks grade, moisture risk, and the next action with local rule retrieval and operator feedback.
                <div class="hero-mini">Compact workflow: one image in, one decision out, corrections reused automatically.</div>
            </div>
            <div class="pill-row">
                <div class="status-pill {runtime_class}">● Runtime: {html.escape(status['runtime_label'])}</div>
                <div class="status-pill">◌ Rules: {status['chunk_count']}</div>
                <div class="status-pill">◌ Corrections: {pending_feedback}</div>
            </div>
            <div class="hero-grid">
                <div class="hero-stat">
                    <div class="hero-stat-label">Flow</div>
                    <div class="hero-stat-value">Inspect → Decide</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-label">Model</div>
                    <div class="hero-stat-value">{model_label}</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-label">Learning</div>
                    <div class="hero-stat-value">Corrections reused</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workspace_nav() -> str:
    nav_left, nav_center, nav_right = st.columns([0.18, 0.64, 0.18])
    with nav_center:
        workspace = st.radio(
            "Workspace",
            ["Inspect Batch", "Review Corrections", "Operations"],
            horizontal=True,
            label_visibility="collapsed",
        )
    return workspace


def _decision_state(grading_result, confidence_threshold: int) -> Dict[str, str]:
    if grading_result.reject_recommended:
        return {
            "label": "Hold Batch",
            "css": "decision-hold",
            "note": "Do not release this lot into storage or sale until the issue is corrected.",
        }
    if grading_result.moisture_risk in {MoistureRisk.HIGH, MoistureRisk.CRITICAL}:
        return {
            "label": "Dry And Recheck",
            "css": "decision-hold" if grading_result.moisture_risk == MoistureRisk.CRITICAL else "decision-review",
            "note": "Storage moisture is too high for a clean release decision.",
        }
    if grading_result.overall_confidence < confidence_threshold or grading_result.manual_review_required:
        return {
            "label": "Operator Review",
            "css": "decision-review",
            "note": "The model wants a human check before the lot is released.",
        }
    return {
        "label": "Release Ready",
        "css": "decision-release",
        "note": "This lot is within the current release guardrails.",
    }


def render_result_banner(grading_result, confidence_threshold: int):
    grade_val = grading_result.quality_grade.value
    grade_class = "grade-a" if grade_val == "A" else "grade-b" if grade_val == "B" else "grade-c"
    moisture_val = grading_result.moisture_risk.value
    moisture_class = {
        "LOW": "moisture-low",
        "MODERATE": "moisture-moderate",
        "HIGH": "moisture-high",
        "CRITICAL": "moisture-critical",
    }.get(moisture_val, "")
    state = _decision_state(grading_result, confidence_threshold)
    summary = grading_result.operator_summary or state["note"]
    highlights = "".join(
        f'<li>{html.escape(item)}</li>'
        for item in grading_result.signal_highlights[:4]
    )
    st.markdown(
        f"""
        <div class="result-banner">
            <div class="decision-main">
                <div>
                    <div class="decision-summary-head">
                        <div class="decision-state {state['css']}">{html.escape(state['label'])}</div>
                        <div class="decision-confidence">{grading_result.overall_confidence}% confidence</div>
                    </div>
                    <p class="decision-grade {grade_class}">Grade {grade_val} · {grading_result.quality_score}/100</p>
                    <div class="decision-note">{html.escape(summary)}</div>
                </div>
                <div class="decision-card">
                    <div class="section-eyebrow">Storage</div>
                    <h4>Moisture action</h4>
                    <p><span class="{moisture_class}">{html.escape(moisture_val)}</span> moisture risk</p>
                    <p>{grading_result.overall_confidence}% confidence · {grading_result.rag_chunks_used} rule chunks · {'fast rules' if is_fast_rules else 'vision assisted'}</p>
                </div>
            </div>
            <ul class="compact-list">{highlights}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_capture_tips():
    st.markdown(
        """
        <div class="insight-card">
            <div class="section-eyebrow">Capture guide</div>
            <ul class="tip-list">
                <li>Use a single, separated grain layer.</li>
                <li>Keep light soft, even, and glare-free.</li>
                <li>Keep the calibration marker or grid visible.</li>
                <li>Fill the frame without cropping the sample field.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_framed_image(image: Image.Image, caption: str) -> None:
    source = ImageOps.exif_transpose(image)
    if source.mode not in {"RGB", "RGBA"}:
        source = source.convert("RGB")

    target_w, target_h = 1600, 900
    canvas_color = (9, 13, 23) if st.session_state.get("dark_mode", True) else (238, 242, 247)
    canvas = Image.new("RGB", (target_w, target_h), canvas_color)
    if source.mode == "RGBA":
        base = Image.new("RGB", source.size, canvas_color)
        base.paste(source, mask=source.getchannel("A"))
        source = base

    resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
    scale = min(target_w / source.width, target_h / source.height)
    preview_size = (max(1, int(source.width * scale)), max(1, int(source.height * scale)))
    preview = source.resize(preview_size, resample)
    offset = ((target_w - preview.width) // 2, (target_h - preview.height) // 2)
    canvas.paste(preview, offset)

    st.image(canvas, use_container_width=True)
    st.markdown(
        f'<div class="image-caption">{html.escape(caption)}</div>',
        unsafe_allow_html=True,
    )


def render_visual_detection_panel(analysis_payload: Dict[str, Any]) -> None:
    proxies = analysis_payload["proxies"]
    annotated_image, overlay_stats = _build_grain_detection_overlay(
        analysis_payload["image_path"],
        proxies=proxies,
    )
    st.subheader("Visual detection")
    if overlay_stats.get("calibration_available"):
        grid_note = ""
        if overlay_stats.get("grid_box_analysis"):
            grid_note = (
                f" Grid overlay shows 1 mm minor cells and 10 mm major boxes; "
                f"occupied major cells: {overlay_stats.get('major_occupied_cells', 0)}."
            )
        st.markdown(
            f"""
            <div class="visual-copy">
                Green/yellow boxes mark detected grains. Blue overlay marks moisture clumps at 0.6 alpha; red overlay marks foreign matter/stones at 0.8 alpha.
                The yellow box marks the calibrated sample field
                ({overlay_stats.get('pixels_per_mm', 0.0):.2f} px/mm, source: {html.escape(str(overlay_stats.get('source', 'none')))}).
                {html.escape(grid_note)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="visual-copy">
                Green/yellow boxes mark detected grains. Blue overlay marks moisture clumps; red overlay marks foreign matter/stones.
                The yellow box marks the full visual grain field used for the local decision.
            </div>
            """,
            unsafe_allow_html=True,
        )
    if annotated_image is not None:
        overlay_engine = "CUDA" if overlay_stats.get("cuda") else "CPU"
        render_framed_image(
            annotated_image,
            (
                f"Detected grain view - {overlay_stats['boxes']} boxes - "
                f"{overlay_stats.get('moisture_clumps', 0)} clumps - "
                f"{overlay_stats.get('foreign_components', 0)} foreign candidates - "
                f"{overlay_stats['coverage']:.1%} mask coverage - {overlay_engine}"
            ),
        )
    else:
        st.warning("Could not generate the AI visual overlay for this image.")


def render_signal_summary(proxies: Dict[str, Any]):
    calibration = proxies.get("calibration", {}) or {}
    calibrated_geometry = proxies.get("calibrated_geometry", {}) or {}
    physical = proxies.get("physical_properties", {}) or {}
    grid_box_analysis = proxies.get("grid_box_analysis", {}) or {}
    if calibration.get("available"):
        calibration_reference = calibration.get("calibration_reference", "detected-grid-lines")
        sheet_style = calibration.get("sheet_style", "unknown")
        active_grid = grid_box_analysis.get("active_field", {}) if grid_box_analysis.get("available") else {}
        grid_caption = ""
        if active_grid:
            grid_caption = (
                f" · grid cells {int(active_grid.get('major_occupied_cells') or 0)}/"
                f"{int(active_grid.get('major_total_cells') or 0)}"
            )
        calibration_caption = (
            f"{float(calibration.get('pixels_per_mm') or 0.0):.2f} px/mm · "
            f"{float(calibration.get('mm_per_pixel') or 0.0):.4f} mm/px · "
            f"{float(calibrated_geometry.get('median_equiv_diameter_mm') or 0.0):.2f} mm grain · "
            f"{html.escape(str(sheet_style))} · {html.escape(str(calibration_reference))}"
            f"{html.escape(grid_caption)}"
        )
    else:
        calibration_caption = "No calibration sheet detected in this frame."
    st.markdown(
        f"""
        <div class="signal-grid">
            <div class="signal-card">
                <h4>Darkness index</h4>
                <div class="signal-value">{proxies['lab_features']['color_darkness_index']:.1f}</div>
                <div class="signal-caption">Darker grain tone, often linked with excess moisture.</div>
            </div>
            <div class="signal-card">
                <h4>Clump density</h4>
                <div class="signal-value">{proxies['clumping']['density']:.3f}</div>
                <div class="signal-caption">Higher clustering suggests moisture or poor separation.</div>
            </div>
            <div class="signal-card">
                <h4>Batch uniformity</h4>
                <div class="signal-value">{proxies['uniformity_score']:.1f}/100</div>
                <div class="signal-caption">Lower score means mixed color or uneven grain quality.</div>
            </div>
            <div class="signal-card">
                <h4>Texture entropy</h4>
                <div class="signal-value">{proxies['texture_entropy']:.2f}</div>
                <div class="signal-caption">Texture spread used to separate dry, rough, and smooth grain.</div>
            </div>
            <div class="signal-card">
                <h4>Calibration source</h4>
                <div class="signal-value">{calibration.get('source', 'none')}</div>
                <div class="signal-caption">{html.escape(calibration_caption)}</div>
            </div>
            <div class="signal-card">
                <h4>Grain Size</h4>
                <div class="signal-value">{html.escape(str(physical.get('size_class', 'unknown')))}</div>
                <div class="signal-caption">
                    Median {float(physical.get('median_diameter_mm') or 0.0):.2f} mm ·
                    P90 {float(physical.get('p90_diameter_mm') or 0.0):.2f} mm ·
                    CV {float(physical.get('size_cv_percent') or 0.0):.1f}%
                </div>
            </div>
            <div class="signal-card">
                <h4>Surface reflectance</h4>
                <div class="signal-value">{html.escape(str(physical.get('reflectiveness_class', 'unknown')))}</div>
                <div class="signal-caption">
                    Shine {float(physical.get('reflectiveness_index') or 0.0):.1f}/100 ·
                    dark {float(physical.get('dark_fraction') or 0.0):.1%} ·
                    highlight {float(physical.get('highlight_fraction') or 0.0):.1%}
                </div>
            </div>
            <div class="signal-card">
                <h4>Shape profile</h4>
                <div class="signal-value">{html.escape(str(physical.get('shape_class', 'unknown')))}</div>
                <div class="signal-caption">
                    Aspect {float(physical.get('median_aspect_ratio') or 0.0):.2f} ·
                    roundness {float(physical.get('median_roundness') or 0.0):.2f} ·
                    components {int(physical.get('component_count') or 0)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_live_physics_proxy_snapshot(
    proxies: Dict[str, Any],
    pipeline: Optional[VisionRAGPipeline] = None,
) -> None:
    """Render OpenCV proxy outputs immediately before the VLM stream starts."""
    clumping = float((proxies.get("clumping", {}) or {}).get("density") or 0.0)
    darkness = float((proxies.get("lab_features", {}) or {}).get("color_darkness_index") or 0.0)
    coverage = float(proxies.get("grain_mask_coverage") or 0.0)
    entropy = float(proxies.get("texture_entropy") or 0.0)
    moisture_label = "Pending"
    moisture_detail = "Proxy extraction complete"

    if pipeline is not None:
        try:
            moisture_risk, moisture_percent, is_calibrated = pipeline.estimate_moisture_risk(proxies)
            moisture_label = moisture_risk.value
            moisture_detail = (
                f"{moisture_percent:.1f}%"
                + (" calibrated" if is_calibrated else " estimated")
            )
        except Exception as exc:
            logger.debug("Moisture preview failed: %s", exc)

    st.markdown(
        """
        <div class="result-intro-shell" style="margin-top:1rem;">
            <div class="section-eyebrow">OpenCV Physics Proxies</div>
            <div class="result-intro-copy">
                These deterministic image signals are available before Qwen3-VL starts generating.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    cols[0].metric("Clumping Density", f"{clumping:.3f}")
    cols[1].metric("Moisture Risk", moisture_label, moisture_detail)
    cols[2].metric("Mask Coverage", f"{coverage:.1%}")
    cols[3].metric("Texture Entropy", f"{entropy:.2f}", f"Darkness {darkness:.1f}")


def run_streamlit_async_inference(
    pipeline: VisionRAGPipeline,
    image_path: str,
    proxies: Dict[str, Any],
    stream_callback,
):
    """
    Streamlit wrapper for cloud Qwen inference.

    Standard Streamlit scripts are synchronous, so the button handler bridges
    into the async pipeline with asyncio.run().
    """
    return asyncio.run(
        pipeline.infer_async(
            image_path,
            proxies,
            stream_callback=stream_callback,
        )
    )


def format_live_ai_reasoning_result(grading_result) -> str:
    """Build the final JSON shown in the live AI reasoning block."""
    return json.dumps(
        {
            "status": "completed",
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
        },
        indent=2,
    )


def _detail_value(value: Any, fallback: str = "Waiting") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def render_workflow_panel(
    status: Dict[str, Any],
    pending_feedback: int,
    analysis_payload: Optional[Dict[str, Any]],
    confidence_threshold: int,
):
    """Render the fixed right-side workflow detail drawer."""
    grading_result = analysis_payload.get("grading_result") if analysis_payload else None
    proxies = analysis_payload.get("proxies") if analysis_payload else {}
    auto_meta = analysis_payload.get("auto_meta") if analysis_payload else {}
    has_run = grading_result is not None

    model_version = (
        grading_result.model_version
        if grading_result is not None
        else status.get("provider_label", "qwen-vl")
    )
    grade = grading_result.quality_grade.value if grading_result is not None else "Waiting"
    moisture = grading_result.moisture_risk.value if grading_result is not None else "Waiting"
    confidence = (
        f"{grading_result.overall_confidence}%"
        if grading_result is not None
        else "Waiting"
    )
    rag_chunks_used = (
        grading_result.rag_chunks_used
        if grading_result is not None
        else status["chunk_count"]
    )
    image_name = Path(str(analysis_payload.get("image_path", ""))).name if analysis_payload else ""

    darkness = (proxies.get("lab_features", {}) or {}).get("color_darkness_index")
    clumping = (proxies.get("clumping", {}) or {}).get("density")
    uniformity = proxies.get("uniformity_score")
    entropy = proxies.get("texture_entropy")
    calibration = proxies.get("calibration", {}) or {}
    darkness_text = f"{darkness:.1f}" if isinstance(darkness, (int, float)) else None
    clumping_text = f"{clumping:.3f}" if isinstance(clumping, (int, float)) else None
    uniformity_text = f"{uniformity:.1f}" if isinstance(uniformity, (int, float)) else None
    entropy_text = f"{entropy:.2f}" if isinstance(entropy, (int, float)) else None

    steps = [
        (
            "01",
            "Image intake",
            f"Saved sample {image_name} for repeatable inference and feedback."
            if has_run
            else "Waiting for an uploaded lot image.",
        ),
        (
            "02",
            "Input quality check",
            "Resolution, blur, and luminance checks are shown before analysis.",
        ),
        (
            "03",
            "Physics proxies",
            (
                f"Darkness {_detail_value(darkness_text)}, "
                f"clumping {_detail_value(clumping_text)}, "
                f"uniformity {_detail_value(uniformity_text)}."
            ),
        ),
        (
            "04",
            "RAG rule retrieval",
            f"Local rule retrieval supplies {rag_chunks_used} chunk(s) for the grading prompt.",
        ),
        (
            "05",
            "Vision model",
            f"Qwen3-VL inspects the image crop and returns strict JSON for grade evidence.",
        ),
        (
            "06",
            "Rule gate",
            "FAO/BIS-aligned thresholds own the final grade, reject reasons, and downgrade gates.",
        ),
        (
            "07",
            "Moisture calibration",
            (
                f"Risk is {moisture}; calibrated field source is "
                f"{str(calibration.get('source', 'none'))}."
            ),
        ),
        (
            "08",
            "Feedback loop",
            f"{pending_feedback} correction file(s) are available for similar-sample reuse and audit review.",
        ),
    ]
    step_html = "".join(
        f"""
        <div class="workflow-step">
            <div class="workflow-index">{idx}</div>
            <div>
                <div class="workflow-title">{html.escape(title)}</div>
                <div class="workflow-copy">{html.escape(copy)}</div>
            </div>
        </div>
        """
        for idx, title, copy in steps
    )

    detail_tiles = [
        ("Runtime", status["runtime_label"]),
        ("Model", model_version),
        ("Retrieval", "Lexical RAG"),
        ("Rules", f"{status['chunk_count']} chunks"),
        ("Batch", _detail_value((auto_meta or {}).get("batch_id"))),
        ("Grade", grade),
        ("Moisture", moisture),
        ("Confidence", confidence),
        ("Threshold", f"{confidence_threshold}%"),
        ("Entropy", _detail_value(entropy_text)),
    ]
    tiles_html = "".join(
        f"""
        <div class="model-detail">
            <span>{html.escape(label)}</span>
            <strong>{html.escape(str(value))}</strong>
        </div>
        """
        for label, value in detail_tiles
    )

    st.markdown(
        f"""
        <aside class="workflow-drawer">
            <div class="workflow-kicker">Current Model Workflow</div>
            <h3>From image scan to lot result</h3>
            <div class="workflow-copy">
                This panel follows the current run state. Use the Details button again to close it.
            </div>
            <div class="model-detail-grid">{tiles_html}</div>
            <div style="height:0.85rem"></div>
            {step_html}
        </aside>
        """,
        unsafe_allow_html=True,
    )


feedback_collector = get_feedback_collector()
runtime_status = get_runtime_status()
pending_feedback = feedback_collector.get_pending_count()

# ============================================================================
# MAIN UI EXECUTION
# ============================================================================

# Initialize detail drawer state
if "show_workflow_details" not in st.session_state:
    st.session_state["show_workflow_details"] = False
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = True

# Call fixed header
render_cyber_header(runtime_status, st.session_state["show_workflow_details"])

# Main spacing anchor
st.markdown('<div class="workstation-viewport" aria-hidden="true"></div>', unsafe_allow_html=True)

status_class = "status-online" if runtime_status["model_ready"] else "status-warn" if runtime_status.get("runtime_online") else "status-alert"
st.markdown(
    f"""
    <div class="utility-row">
        <span class="utility-chip {status_class}">{html.escape(runtime_status["runtime_label"])}</span>
        <span class="utility-chip">{runtime_status["chunk_count"]} rules indexed</span>
        <span class="utility-chip">{pending_feedback} corrections queued</span>
    </div>
    """,
    unsafe_allow_html=True,
)
trace_left, trace_mid, theme_mid, trace_right = st.columns([0.36, 0.14, 0.18, 0.32])
with trace_mid:
    detail_label = "Hide Trace" if st.session_state["show_workflow_details"] else "Trace"
    if st.button(detail_label, key="workflow_details_btn", help="Show current model workflow and run details"):
        st.session_state["show_workflow_details"] = not st.session_state["show_workflow_details"]
        st.rerun()
with theme_mid:
    dark_mode_enabled = st.toggle("Dark mode", key="dark_mode", help="Switch between dark and light interface themes")

render_theme_overrides(bool(dark_mode_enabled))

if st.session_state["show_workflow_details"]:
    render_workflow_panel(
        runtime_status,
        pending_feedback,
        st.session_state.get("current_analysis"),
        confidence_threshold=st.session_state.get("confidence_threshold", 60),
    )

# Call Cyber Hero
render_cyber_hero()

# Workspace Navigation
workspace = render_workspace_nav()
confidence_threshold = int(st.session_state.get("confidence_threshold", 60))

# ============================================================================
# TAB 1: ANALYZE
# ============================================================================

if workspace == "Inspect Batch":
    if not runtime_status["model_ready"]:
        with st.container(border=True):
            st.error(runtime_status["runtime_detail"])
            st.code(
                "QWEN_VL_PROVIDER=dashscope\nQWEN_VL_MODEL=qwen3-vl-plus\nQWEN_VL_API_KEY=...\n# optional: QWEN_VL_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
                language="bash",
            )

    col1, col2 = st.columns([1.02, 0.98], gap="medium")
    file_signature = None
    auto_meta = None
    tmp_path = st.session_state.get("uploaded_sample_path")
    has_loaded_sample = bool(tmp_path and Path(tmp_path).exists())
    analyze_requested = False
    analysis_completed = st.session_state.pop("analysis_completed_notice", False)

    with col1:
        with st.container(border=True):
            st.subheader("Lot image")
            st.caption("Upload one clear lot image. The engine works best with a single grain layer and even light.")
            upload_target = st.expander("Replace lot image", expanded=False) if has_loaded_sample else st.container()
            with upload_target:
                uploaded_file = st.file_uploader(
                    "Upload a ragi grain image",
                    type=["jpg", "jpeg", "png"],
                    help="Diffuse lighting is preferred.",
                    key="lot_image_upload",
                )
            if uploaded_file is not None:
                file_signature = f"{uploaded_file.name}:{uploaded_file.size}"
                if st.session_state.get("uploaded_signature") != file_signature:
                    st.session_state["uploaded_signature"] = file_signature
                    st.session_state["uploaded_name"] = uploaded_file.name
                    st.session_state["uploaded_sample_path"] = _persist_uploaded_sample(uploaded_file)
                    st.session_state["auto_batch_meta"] = _build_auto_batch_metadata(
                        file_signature=file_signature,
                        uploaded_name=uploaded_file.name,
                    )

            tmp_path = st.session_state.get("uploaded_sample_path")
            file_signature = st.session_state.get("uploaded_signature")
            auto_meta = st.session_state.get("auto_batch_meta")

            if tmp_path and Path(tmp_path).exists():
                img = Image.open(tmp_path)
                render_framed_image(img, "Current lot image")
                with st.expander("Input check", expanded=False):
                    img_arr = cv2.imread(tmp_path)
                    if img_arr is None:
                        st.warning("Could not read this image for input checks. Replace the file and try again.")
                    else:
                        h, w = img_arr.shape[:2]
                        validation_cols = st.columns(3)
                        validation_cols[0].metric("Resolution", f"{w}×{h}")

                        gray = cv2.cvtColor(img_arr, cv2.COLOR_BGR2GRAY)
                        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                        blur_threshold = 100.0
                        validation_cols[1].metric("Sharpness", f"{laplacian_var:.1f}")

                        avg_luminance = float(np.mean(gray))
                        validation_cols[2].metric("Luminance", f"{avg_luminance:.1f}")

                        if laplacian_var < blur_threshold:
                            st.warning("Blur is high enough to distort texture signals. Retake this lot image if the decision is operationally important.")
                        else:
                            st.success("Sharpness is acceptable for proxy extraction.")

                        if avg_luminance < 50:
                            st.warning("The frame is underexposed. Moisture-related darkness may be overstated.")
                        elif avg_luminance > 200:
                            st.warning("The frame is overexposed. Fine foreign matter may wash out.")
                        else:
                            st.success("Exposure is in a usable range.")
            else:
                st.markdown(
                    """
                    <div class="insight-card" style="margin-top:0.75rem;">
                        <div class="section-eyebrow">Ready For Intake</div>
                        <div class="section-copy" style="margin-top:0.2rem;">
                            Upload one lot image to unlock input checks, rule grading, storage guidance, and correction capture in the same workspace.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with col2:
        with st.container(border=True):
            analysis_preview = st.session_state.get("current_analysis")
            if (
                tmp_path
                and analysis_preview
                and analysis_preview.get("file_signature") == file_signature
            ):
                render_visual_detection_panel(analysis_preview)
            elif tmp_path:
                st.subheader("Visual detection")
                st.markdown(
                    """
                    <div class="visual-copy">
                        The detected grain view will appear here beside the lot image after analysis.
                    </div>
                    <div class="visual-placeholder">
                        Run Analyze to draw grain boxes, calibration field, and mask coverage.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                render_capture_tips()
                st.caption("Batch info is auto-detected from the upload.")

            if tmp_path and Path(tmp_path).exists():
                st.markdown('<div class="visual-action-divider"></div>', unsafe_allow_html=True)
                analyze_col, analyze_hint_col = st.columns([0.32, 0.68], gap="medium")
                with analyze_col:
                    analyze_requested = st.button(
                        "Analyze",
                        key="analyze_btn",
                        use_container_width=True,
                        disabled=not runtime_status["model_ready"],
                    )
                with analyze_hint_col:
                    run_title = "Grading complete" if analysis_completed else "Ready to run"
                    run_class = "run-status complete" if analysis_completed else "run-status"
                    st.markdown(
                        f"""
                        <div class="{run_class}">
                            <div class="run-status-title">{run_title}</div>
                            <div class="run-status-copy">
                                Runs proxy extraction, rule retrieval, Qwen-VL evidence, and final grading.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    if tmp_path and Path(tmp_path).exists():
        if analyze_requested:
            with st.spinner("Starting RAG and vision stack..."):
                extractor, pipeline = init_local_stack()

            with st.spinner("Extracting physics proxies..."):
                try:
                    proxies = extractor.extract_all_proxies(tmp_path)
                except Exception as e:
                    st.error(f"Physics extraction failed: {e}")
                    logger.error(f"Extraction error: {e}", exc_info=True)
                    proxies = None

            if proxies is not None:
                proxy_placeholder = st.empty()
                with proxy_placeholder.container():
                    render_live_physics_proxy_snapshot(proxies, pipeline)

                ai_placeholder = st.empty()
                streamed_text = {"value": ""}

                def update_ai_reasoning(partial_json: str) -> None:
                    streamed_text["value"] = partial_json
                    with ai_placeholder.container():
                        st.markdown("#### AI Reasoning...")
                        st.code(partial_json or "{", language="json")

                with ai_placeholder.container():
                    st.markdown("#### AI Reasoning...")
                    st.code("{", language="json")

                with st.spinner("AI Reasoning..."):
                    try:
                        grading_result = run_streamlit_async_inference(
                            pipeline,
                            tmp_path,
                            proxies,
                            update_ai_reasoning,
                        )
                        streamed_text["value"] = format_live_ai_reasoning_result(
                            grading_result
                        )
                        with ai_placeholder.container():
                            st.markdown("#### AI Reasoning Complete")
                            st.code(streamed_text["value"], language="json")

                        uploaded_name = st.session_state.get("uploaded_name", Path(tmp_path).name)
                        auto_meta = auto_meta or _build_auto_batch_metadata(
                            file_signature=file_signature,
                            uploaded_name=uploaded_name,
                        )
                        st.session_state["current_analysis"] = {
                            "file_signature": file_signature,
                            "image_path": tmp_path,
                            "farm_id": auto_meta["farm_id"],
                            "batch_id": auto_meta["batch_id"],
                            "device_model": auto_meta["device_model"],
                            "capture_distance_estimate_cm": proxies.get("capture_distance_estimate_cm"),
                            "capture_distance_source": proxies.get("capture_distance_source", "auto"),
                            "auto_meta": auto_meta,
                            "proxies": proxies,
                            "grading_result": grading_result,
                        }
                        st.session_state["last_result"] = {
                            "timestamp": grading_result.timestamp,
                            "image_path": tmp_path,
                            "farm_id": auto_meta["farm_id"],
                            "batch_id": auto_meta["batch_id"],
                            "device_model": auto_meta["device_model"],
                            "predicted_grade": grading_result.quality_grade.value,
                            "predicted_moisture": grading_result.moisture_risk.value,
                            "confidence": grading_result.overall_confidence,
                            "proxies": proxies,
                            "grading_result": grading_result,
                            "capture_distance_estimate_cm": proxies.get("capture_distance_estimate_cm"),
                            "capture_distance_source": proxies.get("capture_distance_source", "auto"),
                            "auto_meta": auto_meta,
                        }
                        st.session_state["analysis_completed_notice"] = True
                        st.rerun()

                    except Exception as e:
                        st.error(f"Inference failed: {e}")
                        logger.error(f"Inference error: {e}", exc_info=True)

        analysis_payload = st.session_state.get("current_analysis")
        if analysis_payload and analysis_payload.get("file_signature") == file_signature:
            grading_result = analysis_payload["grading_result"]
            proxies = analysis_payload["proxies"]
            st.markdown('<div class="result-transition"></div>', unsafe_allow_html=True)
            decision_action_left, decision_action_right = st.columns([0.78, 0.22], gap="medium")
            with decision_action_left:
                st.markdown(
                    """
                    <div class="result-intro-shell">
                        <div class="section-eyebrow">Lot Decision</div>
                        <div class="result-intro-title">Result</div>
                        <div class="result-intro-copy">
                            Final grade, storage risk, confidence, and the strongest decision signals.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with decision_action_right:
                result_detail_label = (
                    "Hide Trace"
                    if st.session_state["show_workflow_details"]
                    else "Trace"
                )
                if st.button(result_detail_label, key="workflow_details_result_btn"):
                    st.session_state["show_workflow_details"] = not st.session_state["show_workflow_details"]
                    st.rerun()
            render_result_banner(grading_result, confidence_threshold)

            if grading_result.overall_confidence < confidence_threshold:
                st.warning(
                    f"Confidence is {grading_result.overall_confidence}%, below your review floor of {confidence_threshold}%. "
                    "Treat this lot as manual-review required."
                )

            result_col1, result_col2 = st.columns([1, 1], gap="large")
            with result_col1:
                with st.container(border=True):
                    st.subheader("Batch quality")
                    metric_cols = st.columns(3)
                    metric_cols[0].metric("Grade", grading_result.quality_grade.value)
                    metric_cols[1].metric("Score", f"{grading_result.quality_score}/100")
                    metric_cols[2].metric("Confidence", f"{grading_result.overall_confidence}%")
                    st.caption(
                        f"Uniformity {grading_result.uniformity_score:.1f}/100 • "
                        f"Broken {grading_result.broken_grain_percent:.1f}% • "
                        f"Foreign {grading_result.foreign_matter_percent:.1f}%"
                    )
            with result_col2:
                with st.container(border=True):
                    st.subheader("Storage action")
                    st.metric(
                        "Moisture Estimate",
                        (
                            f"{grading_result.moisture_percent_estimate:.1f}%"
                            if grading_result.moisture_percent_estimate is not None
                            else "Uncalibrated"
                        ),
                    )
                    st.caption(
                        f"Risk {grading_result.moisture_risk.value} • "
                        f"Calibrated {'Yes' if grading_result.moisture_estimate_calibrated else 'No'}"
                    )
                    if grading_result.reject_reasons:
                        reject_items = "".join(
                            f"<li>{html.escape(reason)}</li>"
                            for reason in grading_result.reject_reasons
                        )
                        st.markdown(
                            f"""
                            <div class="reject-list">
                                <div class="reject-list-title">Release blockers</div>
                                <ul>{reject_items}</ul>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info(grading_result.operator_summary)

            st.markdown(
                """
                <div class="signal-section-head">
                    <div>
                        <div class="section-eyebrow">Model signals</div>
                        <div class="signal-section-title">Proxy evidence summary</div>
                    </div>
                    <div class="signal-section-note">
                        Local image signals used by the grade, moisture, and confidence gate.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_signal_summary(proxies)
            st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
            signal_cols = st.columns(3, gap="small")
            signal_cols[0].metric("Surface roughness", f"{proxies['roughness_score']:.1f}")
            signal_cols[1].metric("Specular highlights", f"{proxies['specular_highlights_ratio']:.2%}")
            signal_cols[2].metric("Mask coverage", f"{proxies['grain_mask_coverage']:.1%}")

            with st.expander("Audit trace", expanded=False):
                auto_distance = analysis_payload.get("capture_distance_estimate_cm")
                auto_source = analysis_payload.get("capture_distance_source", "auto")
                audit_df = pd.DataFrame(
                    {
                        "Field": [
                            "Timestamp",
                            "Model Version",
                            "Pass 1 Confidence",
                            "Pass 2 Confidence",
                            "RAG Chunks Used",
                            "Farm ID",
                            "Batch ID",
                            "Device",
                            "Auto Distance",
                            "Distance Source",
                        ],
                        "Value": [
                            grading_result.timestamp,
                            grading_result.model_version,
                            f"{grading_result.pass1_confidence}%",
                            f"{grading_result.pass2_confidence}%",
                            str(grading_result.rag_chunks_used),
                            analysis_payload["farm_id"],
                            analysis_payload["batch_id"],
                            analysis_payload["device_model"],
                            (
                                f"{auto_distance:.1f} cm"
                                if isinstance(auto_distance, (int, float))
                                else "Auto"
                            ),
                            auto_source,
                        ],
                    }
                )
                st.dataframe(audit_df, use_container_width=True, hide_index=True)

            # --- INTEGRATED CORRECTION FLOW ---
            st.divider()
            with st.container(border=True):
                st.subheader("Operator correction")
                st.caption("If the cloud model decision is incorrect, record the fix here. Similar future samples will include this correction context.")
                
                with st.form("integrated_correction"):
                    f_col1, f_col2 = st.columns(2)
                    with f_col1:
                        c_grade = st.selectbox("Correct Grade", ["A", "B", "C"], index=["A", "B", "C"].index(grading_result.quality_grade.value))
                        c_moisture = st.selectbox("Correct Moisture Risk", ["LOW", "MODERATE", "HIGH", "CRITICAL"], index=["LOW", "MODERATE", "HIGH", "CRITICAL"].index(grading_result.moisture_risk.value))
                    with f_col2:
                        c_notes = st.text_area("Observation Notes", placeholder="e.g., Visible mold not detected, or color is actually Grade A.")
                    
                    if st.form_submit_button("Submit correction", use_container_width=True):
                        feedback_item = GradingFeedbackItem(
                            sample_id=analysis_payload["batch_id"],
                            image_path=analysis_payload["image_path"],
                            farm_id=analysis_payload["farm_id"],
                            batch_id=analysis_payload["batch_id"],
                            predicted_grade=grading_result.quality_grade.value,
                            true_grade=c_grade,
                            predicted_moisture_risk=grading_result.moisture_risk.value,
                            true_moisture_risk=c_moisture,
                            image_features=proxies,
                            confidence=grading_result.overall_confidence,
                            timestamp=grading_result.timestamp,
                            device_model=analysis_payload["device_model"],
                            notes=c_notes,
                        )
                        if feedback_collector.submit_feedback(feedback_item):
                            st.success("Correction recorded. Re-analysis of this batch will now consider this signal.")
                            st.rerun()
                        else:
                            st.error("Failed to save correction.")

elif workspace == "Review Corrections":
    render_section_intro(
        "Review Corrections",
        "Correction queue",
        "Review the latest decision, save operator corrections, and track cloud-runtime feedback.",
    )

    control_left, control_center, control_right = st.columns([0.18, 0.64, 0.18])
    with control_center:
        with st.container(border=True):
            st.markdown(
                """
                <div class="control-title">Analysis controls</div>
                <div class="control-subtitle">Set the review floor before running cloud grading.</div>
                """,
                unsafe_allow_html=True,
            )
            slider_left, slider_center, slider_right = st.columns([0.08, 0.84, 0.08])
            with slider_center:
                confidence_threshold = st.slider("Confidence floor", 0, 100, 60, key="confidence_threshold")

            metric_cols = st.columns([1, 1, 1], gap="medium")
            with metric_cols[0]:
                st.metric("Runtime", runtime_status["runtime_label"])
            with metric_cols[1]:
                st.metric("Rules", f"{runtime_status['chunk_count']}")
            with metric_cols[2]:
                st.metric("Corrections", f"{pending_feedback}")

    st.markdown('<div style="height: 0.4rem;"></div>', unsafe_allow_html=True)

    if "last_result" in st.session_state:
        st.success("The latest lot decision is ready for correction")

        result = st.session_state["last_result"]

        col_f1, col_f2 = st.columns([0.95, 1.05], gap="large")

        with col_f1:
            with st.container(border=True):
                st.subheader("Model Decision")
                st.write(f"**Grade:** {result['predicted_grade']}")
                st.write(f"**Moisture Risk:** {result['predicted_moisture']}")
                st.write(f"**Confidence:** {result['confidence']}%")

        with col_f2:
            with st.container(border=True):
                st.subheader("Operator Correction")
                corrected_grade = st.selectbox(
                    "Correct Grade", ["A", "B", "C"], key="correct_grade"
                )
                corrected_moisture = st.selectbox(
                    "Correct Moisture Risk",
                    ["LOW", "MODERATE", "HIGH", "CRITICAL"],
                    key="correct_moisture",
                )
                farmer_note = st.text_area(
                    "Why was the model wrong?", key="farmer_note"
                )

        if st.button("Submit feedback", use_container_width=True):
            feedback_item = GradingFeedbackItem(
                sample_id=result.get("farm_id", "UNKNOWN"),
                image_path=result["image_path"],
                farm_id=result.get("farm_id", "UNKNOWN"),
                batch_id=result.get("batch_id", "UNKNOWN"),
                predicted_grade=result["predicted_grade"],
                true_grade=corrected_grade,
                predicted_moisture_risk=result["predicted_moisture"],
                true_moisture_risk=corrected_moisture,
                image_features=result["proxies"],
                confidence=result["confidence"],
                timestamp=result["timestamp"],
                device_model=result.get("device_model", "unknown"),
                notes=farmer_note,
            )

            if feedback_collector.submit_feedback(feedback_item):
                st.success("Correction saved")
                st.info(
                    f"Pending corrections: {feedback_collector.get_pending_count()}/500 before queue review"
                )
            else:
                st.error("Failed to submit feedback")

    else:
        st.info("Run a batch through `Inspect Batch` first, then come back here to correct the model.")

    st.divider()

    st.subheader("Correction Queue")

    pending_count = feedback_collector.get_pending_count()
    review_threshold = 500

    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Pending Corrections", pending_count)
    with col_stat2:
        st.metric("Review Threshold", review_threshold)
    with col_stat3:
        progress = min(100, int(pending_count / review_threshold * 100))
        st.metric("Progress to Review", f"{progress}%")

    # Progress bar
    st.progress(progress / 100.0)

    if progress >= 100:
        st.warning(
            "Review threshold reached. Export or review the correction queue before the next deployment."
        )

    correction_patterns = feedback_collector.summarize_feedback_patterns(limit=4)
    if correction_patterns:
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Recurring Correction Patterns")
            for pattern in correction_patterns:
                st.markdown(f"- {pattern}")

else:
    render_section_intro(
        "Operations",
        "System performance and reference notes",
        "Operational metrics, example history, and system notes live here so the main lot-inspection workflow stays clean.",
    )
    ops_tabs = st.tabs(["Performance", "History", "System Notes"])

    with ops_tabs[0]:
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
        col_d1.metric("Total Lots Reviewed", "142", delta="5 today")
        col_d2.metric("Grade A Share", "45%", delta="+2%")
        col_d3.metric("Average Confidence", "82%", delta="-1%")
        col_d4.metric("Estimated Accuracy", "87%", delta="+3%")

        st.divider()

        col_dash1, col_dash2 = st.columns(2)
        with col_dash1:
            st.subheader("Grade Distribution")
            grade_dist = pd.DataFrame({"Grade": ["A", "B", "C"], "Count": [64, 63, 15]})
            st.bar_chart(grade_dist.set_index("Grade"))
        with col_dash2:
            st.subheader("Moisture Risk Distribution")
            moisture_dist = pd.DataFrame(
                {"Risk": ["LOW", "MODERATE", "HIGH", "CRITICAL"], "Count": [45, 60, 28, 9]}
            )
            st.bar_chart(moisture_dist.set_index("Risk"))

        st.divider()
        st.subheader("Per-Device Performance")
        device_perf = pd.DataFrame(
            {
                "Device": ["iPhone 12", "Samsung Galaxy A50", "Redmi Note 9", "Generic Android"],
                "Samples": [32, 28, 52, 30],
                "Avg Grade A %": [48, 42, 44, 46],
                "Avg Confidence %": [85, 80, 81, 79],
            }
        )
        with st.container(border=True):
            st.dataframe(device_perf, use_container_width=True, hide_index=True)

    with ops_tabs[1]:
        st.info("This history view is still sample data. Connect a persistent store when you want a real audit log.")
        history_df = pd.DataFrame(
            {
                "Sample ID": ["RAG-001", "RAG-002", "RAG-003"],
                "Grade": ["A", "B", "C"],
                "Quality Score": [92, 78, 45],
                "Moisture Risk": ["LOW", "MODERATE", "HIGH"],
                "Timestamp": [
                    "2026-04-29 10:15:00",
                    "2026-04-29 10:22:00",
                    "2026-04-29 10:30:00",
                ],
                "Confidence": [92, 85, 72],
            }
        )
        with st.container(border=True):
            st.dataframe(history_df, use_container_width=True, hide_index=True)

    with ops_tabs[2]:
        st.markdown(
            """
        ## System Layout

        **Millets Now** is a cloud-Qwen ragi lot grading system built around:

        1. **Physics Proxies Extraction**
           - Texture entropy
           - Derived darkness index
           - Capillary clumping
           - Surface roughness

        2. **Vision-RAG Grading**
           - Pass 1: safety hazard gate
           - Pass 2: rule-guided grade assignment
           - Deterministic fallback when the model response is weak

        3. **Moisture Calibration**
           - Maps raw optical signals to calibrated storage-risk bands

        4. **Correction Loop**
           - Stores operator fixes
           - Reuses similar fixes during later inference
           - Keeps a JSON audit queue for later review
        """
        )

        with st.expander("Technical Notes"):
            st.code(
                """
# Physics proxies
- Texture entropy: Shannon entropy of Laplacian magnitude
- Darkness index: derived from LAB lightness
- Clumping density: largest cluster / grain coverage
- Roughness: Laplacian variance

# Vision-RAG grading
- Configured Qwen-VL call with compressed rule context
- Text-only JSON repair pass when the model spends tokens in reasoning
- Deterministic grade logic layered on top of model output

# Feedback loop
- Corrections stored as JSON records
- Similar corrections retrieved during later cloud inference
- Correction volume is tracked for audit review
                """,
                language="python",
            )

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 12px;'>
    <p>Millets Now © 2026 | Powered by Vision-RAG + configurable Qwen-VL | 
    <a href="https://github.com/Atharva-007/GrainGrade-Detection">GitHub Repo</a></p>
    </div>
    """,
    unsafe_allow_html=True,
)
