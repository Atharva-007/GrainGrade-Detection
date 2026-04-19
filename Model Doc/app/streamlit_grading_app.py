"""
Finger Millet (Ragi) Grading — Streamlit + Gemini Vision + RAG

Features:
  - 3-tier grading (A / B / C), per-grade detailed prompts
  - Multi-region bounding boxes always shown (annotated overlay)
  - RAG retrieval over grading docs + Handbook PDF (build once via build_rag_index.py)
  - Comparison view with A/B/C threshold matrix
  - Few-shot reference images (toggle)
"""

from __future__ import annotations

import io
import json
import mimetypes
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from google import genai
from google.genai import types

import rag

# Load .env from this app's directory
load_dotenv(Path(__file__).resolve().parent / ".env")


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
MODEL_DOC_DIR = APP_DIR.parent
RAGI_IMAGE_DIR = MODEL_DOC_DIR.parent / "Ragi Image"

PROMPT_DOCS = {
    "grading_spec":  MODEL_DOC_DIR / "finger_millet_ai_grading.md",
    "grade_a":       MODEL_DOC_DIR / "grade_a_ragi_vision_prompt.md",
    "grade_b":       MODEL_DOC_DIR / "grade_b_ragi_vision_prompt.md",
    "grade_c":       MODEL_DOC_DIR / "grade_c_ragi_vision_prompt.md",
    "comparison":    MODEL_DOC_DIR / "grades_comparison.md",
}

REFERENCE_IMAGES = [
    ("A", "Dense uniform reddish-brown, tight size, <5% off-tone.",
     RAGI_IMAGE_DIR / "GRADE A" / "IMG_4383.JPG"),
    ("A", "Macro view: plump spherical grains, clean surface.",
     RAGI_IMAGE_DIR / "GRADE A" / "IMG_4491.JPG"),
    ("B", "Mostly uniform, minor dark minority (<10%); still B.",
     RAGI_IMAGE_DIR / "GRADE B" / "IMG_4397.JPG"),
    ("B", "Upper bound of B: trace darker grains, minimal shrivel.",
     RAGI_IMAGE_DIR / "GRADE B" / "IMG_4403.JPG"),
    ("C", "Bimodal: ~20-25% dark grains mixed through red-brown.",
     RAGI_IMAGE_DIR / "GRADE C" / "IMG_4411.JPG"),
    ("C", "Dense C batch: bimodal tone and size variance.",
     RAGI_IMAGE_DIR / "GRADE C" / "IMG_4415.JPG"),
    ("C", "Canonical C: scattered dark pockets + shrivel tails.",
     RAGI_IMAGE_DIR / "GRADE C" / "IMG_4421.JPG"),
]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """You are a food-quality inspector with deep training in
post-harvest millet science (Handbook of Millets – Processing, Quality and
Nutrition). You evaluate macro photographs of finger millet (ragi, Eleusine
coracana) and assign a grade on a THREE-TIER scale:

  A — Premium (score 90-100): uniform, clean, direct human consumption
  B — Commercial (score 75-89): minor variance, suitable for retail food
  C — Processing / catch-all (score <75): visible defects OR any hazard

There is NO Grade D in this deployment. Hazardous batches stay at C with
reject_recommended=true.

Be conservative. When evidence is ambiguous, downgrade. Never upgrade on
uncertainty. Return ONLY strict JSON matching the provided schema — no prose."""


USER_PROMPT_INSTRUCTIONS = """Analyze the TARGET image and produce a grading JSON.

## 8-Step Procedure
1. Frame validity (focus, lighting, >200 grains visible).
2. Color distribution — ragi is reddish-brown to dark brown; record off-tone %.
3. Size uniformity — deviation from modal diameter (1-2 mm).
4. Shape integrity — shriveled / flattened / broken fraction.
5. Foreign matter — dust OK <3%; stones or debris >3% → reject.
6. Biological hazards (HARD GATE) — mold, webbing, insects, holes, clumping.
7. Storage / oxidation signs — dullness, greying, moisture clumping.
8. Weighted score -> grade. Hazards force grade=C with reject_recommended=true.

## Grade Decision Flow (apply in order — first yes wins)
1. Any biological hazard OR stones OR foreign_matter >3%?
   → Grade C, reject_recommended=true
2. Is the color distribution BIMODAL (two clearly distinct tones coexisting)?
   → Grade C
3. off_tone <5% AND defects <5% AND foreign_matter <1% AND no hazards?
   → Grade A
4. Otherwise (no hazards, not bimodal) → Grade B

## REGION / BOUNDING BOX REQUIREMENTS (MANDATORY)
You MUST return at least ONE region. Use normalized coordinates in the 0-1000
range: [ymin, xmin, ymax, xmax].

  - If the batch is UNIFORM across the whole frame, return ONE region covering
    the full grain area (roughly the densely-populated portion of the image,
    not white background). Grade of that region = overall batch grade.
  - If the batch is MIXED, return 2-6 regions, each around a visibly distinct
    quality zone. Set is_mixed_batch=true.
  - Do NOT return empty regions[]. Do NOT tile the whole image; only box what
    you can justify.

## Output JSON Schema (return ONLY this, no prose)
{
  "grade": "A" | "B" | "C" | "unknown",
  "quality_score": 0-100,
  "is_mixed_batch": bool,
  "regions": [
    {
      "bbox": [ymin, xmin, ymax, xmax],
      "grade": "A" | "B" | "C",
      "reason": str,
      "confidence": 0-1
    }
  ],
  "color_analysis": {"dominant_tone": str, "secondary_tone": str,
                     "off_tone_percentage": number, "uniformity": "high"|"moderate"|"low"},
  "size_analysis": {"uniformity": "high"|"moderate"|"low", "shriveled_fraction": 0-1},
  "shape_analysis": {"defect_fraction": 0-1, "defect_types": [str, ...]},
  "foreign_matter": {"percentage": number, "types_detected": [str, ...],
                     "large_contaminants": bool},
  "biological_risk": {"fungus_detected": bool, "insect_damage": bool,
                      "webbing": bool, "clumping": bool},
  "storage_risk": "low"|"moderate"|"high",
  "reject_recommended": bool,
  "reject_reasons": [str, ...],
  "confidence": 0-1,
  "remarks": str,
  "recommended_use": str,
  "reasoning": {
    "grade_a_case": str,   // one-line: why A was / was not chosen
    "grade_b_case": str,   // one-line: why B was / was not chosen
    "grade_c_case": str    // one-line: why C was / was not chosen
  }
}
"""


RAG_QUERY = (
    "finger millet ragi grading quality defect detection color uniformity "
    "shape size biological hazard mold insect foreign matter bimodal grade A B C thresholds"
)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_prompt_doc(key: str) -> str:
    p = PROMPT_DOCS.get(key)
    if p and p.exists():
        return p.read_text()
    return ""


@st.cache_data(show_spinner=False)
def load_all_prompt_docs() -> str:
    parts = []
    for key, path in PROMPT_DOCS.items():
        if path.exists():
            parts.append(f"# === {path.name} ===\n{path.read_text()}")
    return "\n\n---\n\n".join(parts)


@st.cache_data(show_spinner=False)
def retrieve_rag_context(query: str, k: int) -> tuple[str, list[dict]]:
    """Returns (formatted_context, metadata_list). Cached per query+k."""
    if not rag.index_exists():
        return "", []
    # Local import avoids creating a client outside cache scope
    api_key = os.environ.get("VERTEX_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "", []
    client = genai.Client(vertexai=True, api_key=api_key)
    hits = rag.retrieve(client, query, k=k)
    formatted = rag.format_retrieved(hits)
    meta = [{"source": h[0].source, "title": h[0].title, "score": h[1],
             "preview": h[0].text[:200]} for h in hits]
    return formatted, meta


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------
GRADE_COLORS = {
    "A": (34, 197, 94),    # green
    "B": (234, 179, 8),    # yellow
    "C": (249, 115, 22),   # orange
}


def image_part_from_path(path: Path) -> types.Part:
    mime, _ = mimetypes.guess_type(str(path))
    return types.Part.from_bytes(data=path.read_bytes(), mime_type=mime or "image/jpeg")


def image_part_from_bytes(data: bytes, mime: str) -> types.Part:
    return types.Part.from_bytes(data=data, mime_type=mime)


def draw_region_boxes(image_bytes: bytes, regions: list[dict]) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if not regions:
        return img
    draw = ImageDraw.Draw(img)
    w, h = img.size
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", max(18, h // 35))
    except Exception:
        font = ImageFont.load_default()
    line_width = max(4, min(w, h) // 180)

    for r in regions:
        bbox = r.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4):
            continue
        ymin, xmin, ymax, xmax = bbox
        x1 = int(xmin / 1000 * w)
        y1 = int(ymin / 1000 * h)
        x2 = int(xmax / 1000 * w)
        y2 = int(ymax / 1000 * h)
        grade = r.get("grade", "?")
        color = GRADE_COLORS.get(grade, (200, 200, 200))
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

        reason = r.get("reason", "")
        label = f"{grade}" if not reason else f"{grade} · {reason[:50]}"
        try:
            lbox = draw.textbbox((x1, max(0, y1 - font.size - 8)), label, font=font)
            draw.rectangle(lbox, fill=color)
            draw.text((x1 + 4, max(0, y1 - font.size - 8)), label, fill=(0, 0, 0), font=font)
        except Exception:
            draw.text((x1 + 4, max(0, y1 - 20)), label, fill=color)

    return img


def ensure_at_least_one_region(result: dict) -> dict:
    """Guarantee the overlay is non-empty. Model should comply; this is a safety net."""
    regions = result.get("regions") or []
    if regions:
        return result
    result["regions"] = [{
        "bbox": [50, 50, 950, 950],
        "grade": result.get("grade", "C"),
        "reason": "overall batch",
        "confidence": result.get("confidence", 0.5),
    }]
    return result


# ---------------------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> genai.Client:
    return genai.Client(vertexai=True, api_key=api_key)


def build_contents(
    target_bytes: bytes,
    target_mime: str,
    use_references: bool,
    rag_context: str,
) -> list:
    parts: list = []
    # 1) All prompt docs (grading spec + per-grade + comparison)
    all_docs = load_all_prompt_docs()
    parts.append(types.Part.from_text(text=USER_PROMPT_INSTRUCTIONS))
    parts.append(types.Part.from_text(text="\n\n# === GRADING KNOWLEDGE BASE ===\n" + all_docs))
    # 2) RAG-retrieved passages
    if rag_context:
        parts.append(types.Part.from_text(text="\n\n" + rag_context))
    # 3) Labeled reference images
    if use_references:
        parts.append(types.Part.from_text(text="\n\n--- LABELED REFERENCES ---"))
        for grade, note, path in REFERENCE_IMAGES:
            if not path.exists():
                continue
            parts.append(types.Part.from_text(text=f"\nREFERENCE — GRADE: {grade} — {note}"))
            parts.append(image_part_from_path(path))
    # 4) Target
    parts.append(types.Part.from_text(text="\n\n--- TARGET — GRADE: ? — apply decision flow and return JSON only ---"))
    parts.append(image_part_from_bytes(target_bytes, target_mime))
    return parts


def grade_image(client: genai.Client, model_name: str, parts: list) -> dict:
    response = client.models.generate_content(
        model=model_name,
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Ragi Grading — RAG + Vision", page_icon="🌾", layout="wide")
st.title("🌾 Finger Millet (Ragi) Grading System")
st.caption("Gemini Vision · RAG over grading docs + Handbook · 3-tier scale · bounding-box regions")

api_key = os.environ.get("VERTEX_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("Configuration")
    if api_key:
        st.success(f"API key loaded (…{api_key[-6:]})")
    else:
        st.error("VERTEX_API_KEY missing in .env")

    if rag.index_exists():
        n_chunks = sum(1 for _ in open(APP_DIR / "rag_chunks.jsonl"))
        st.success(f"RAG index: {n_chunks} chunks")
    else:
        st.warning("RAG index missing. Run `python build_rag_index.py` first.")

    model_name = st.selectbox(
        "Model",
        options=["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash-001"],
        index=0,
    )
    use_references = st.toggle("Few-shot reference images", value=True,
                               help="7 labeled images (2×A, 2×B, 3×C). ~5-8k image tokens.")
    use_rag = st.toggle("Use RAG retrieval", value=True,
                        help="Retrieve top-k relevant passages from the knowledge base.")
    rag_k = st.slider("RAG top-k", 3, 15, 8, disabled=not use_rag)

tab_grade, tab_compare, tab_docs = st.tabs(["Grade an image", "Grade comparison", "Knowledge base"])


# ---------------------------------------------------------------------------
# TAB 1: Grade an image
# ---------------------------------------------------------------------------
with tab_grade:
    col_in, col_out = st.columns([1, 1])

    with col_in:
        st.subheader("1 · Upload image")
        uploaded = st.file_uploader("Macro photo of ragi grains",
                                     type=["jpg", "jpeg", "png"])
        if uploaded is not None:
            st.image(uploaded, caption=uploaded.name, use_container_width=True)
        run = st.button("🔍 Grade this batch", type="primary",
                        disabled=uploaded is None or not api_key,
                        use_container_width=True)

    with col_out:
        st.subheader("2 · Grading result")
        if run and uploaded is not None:
            target_bytes = uploaded.getvalue()
            target_mime = uploaded.type or "image/jpeg"

            rag_context, rag_meta = ("", [])
            if use_rag:
                with st.spinner("Retrieving from knowledge base…"):
                    rag_context, rag_meta = retrieve_rag_context(RAG_QUERY, rag_k)

            try:
                with st.spinner(f"Calling {model_name}…"):
                    client = get_client(api_key)
                    parts = build_contents(target_bytes, target_mime,
                                           use_references, rag_context)
                    result = grade_image(client, model_name, parts)
                    result = ensure_at_least_one_region(result)
            except Exception as e:
                st.error(f"Grading failed: {e}")
                st.stop()

            grade = result.get("grade", "?")
            score = result.get("quality_score", "?")
            reject = result.get("reject_recommended", False)
            is_mixed = result.get("is_mixed_batch", False)
            regions = result.get("regions", []) or []

            icon = {"A": "✅", "B": "🟡", "C": "🟠", "unknown": "⚪"}.get(grade, "⚪")
            header = f"{icon} Grade **{grade}** · Score **{score}**"
            if is_mixed:
                header += " · 🧩 **MIXED BATCH**"
            if reject:
                header += " · 🚫 **REJECT**"
            st.markdown(f"### {header}")

            annotated = draw_region_boxes(target_bytes, regions)
            st.image(
                annotated,
                caption=f"{len(regions)} region(s) detected — 🟢 A · 🟡 B · 🟠 C",
                use_container_width=True,
            )

            if result.get("remarks"):
                st.info(result["remarks"])
            if reject and result.get("reject_reasons"):
                st.warning("Reject reasons: " + ", ".join(result["reject_reasons"]))

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Off-tone %",
                          result.get("color_analysis", {}).get("off_tone_percentage", "—"))
                st.metric("Foreign matter %",
                          result.get("foreign_matter", {}).get("percentage", "—"))
            with m2:
                st.metric("Shriveled fraction",
                          result.get("size_analysis", {}).get("shriveled_fraction", "—"))
                st.metric("Shape defect fraction",
                          result.get("shape_analysis", {}).get("defect_fraction", "—"))
            with m3:
                st.metric("Storage risk", result.get("storage_risk", "—"))
                st.metric("Confidence", result.get("confidence", "—"))

            bio = result.get("biological_risk", {}) or {}
            flags = [k for k, v in bio.items() if v]
            if flags:
                st.error("Biological hazards: " + ", ".join(flags))
            else:
                st.success("No biological hazards detected")

            reasoning = result.get("reasoning", {}) or {}
            if reasoning:
                with st.expander("Per-grade reasoning (why A / B / C)"):
                    for key, label in [("grade_a_case", "Grade A case"),
                                        ("grade_b_case", "Grade B case"),
                                        ("grade_c_case", "Grade C case")]:
                        text = reasoning.get(key, "")
                        if text:
                            st.markdown(f"**{label}:** {text}")

            if regions:
                with st.expander(f"Region details ({len(regions)})"):
                    for i, r in enumerate(regions, 1):
                        st.markdown(
                            f"**{i}. Grade {r.get('grade','?')}** "
                            f"(conf {r.get('confidence','—')}) — "
                            f"{r.get('reason','')}  `bbox={r.get('bbox')}`"
                        )

            if rag_meta:
                with st.expander(f"RAG context used ({len(rag_meta)} passages)"):
                    for m in rag_meta:
                        st.markdown(
                            f"**[{m['source']}] {m['title']}** — score {m['score']:.2f}\n\n"
                            f"> {m['preview']}…"
                        )

            with st.expander("Raw JSON response"):
                st.json(result)
        elif not api_key:
            st.info("Set VERTEX_API_KEY in `.env` and restart.")
        else:
            st.info("Upload an image and click **Grade this batch**.")


# ---------------------------------------------------------------------------
# TAB 2: Grade comparison
# ---------------------------------------------------------------------------
with tab_compare:
    st.subheader("Grade A / B / C — side-by-side criteria")
    cmp = load_prompt_doc("comparison")
    if cmp:
        st.markdown(cmp)
    else:
        st.warning("grades_comparison.md not found.")

    st.divider()
    st.subheader("Per-grade detailed prompts")
    ga, gb, gc = st.tabs(["Grade A", "Grade B", "Grade C"])
    with ga:
        st.markdown(load_prompt_doc("grade_a") or "_Grade A prompt doc not found._")
    with gb:
        st.markdown(load_prompt_doc("grade_b") or "_Grade B prompt doc not found._")
    with gc:
        st.markdown(load_prompt_doc("grade_c") or "_Grade C prompt doc not found._")


# ---------------------------------------------------------------------------
# TAB 3: Knowledge base
# ---------------------------------------------------------------------------
with tab_docs:
    st.subheader("Master grading specification")
    st.markdown(load_prompt_doc("grading_spec") or "_Grading spec not found._")

    st.divider()
    st.subheader("RAG index status")
    if rag.index_exists():
        with open(APP_DIR / "rag_chunks.jsonl") as f:
            all_chunks = [json.loads(line) for line in f if line.strip()]
        st.write(f"**{len(all_chunks)}** indexed chunks across "
                 f"**{len(set(c['source'] for c in all_chunks))}** sources.")

        query = st.text_input("Try a retrieval query",
                              value="biological hazards fungus mold detection")
        k = st.slider("Top-k", 3, 15, 5, key="rag_browse_k")
        if st.button("Search", key="rag_search_btn"):
            _, meta = retrieve_rag_context(query, k)
            for m in meta:
                st.markdown(
                    f"**[{m['source']}] {m['title']}** — score {m['score']:.3f}\n\n"
                    f"> {m['preview']}…"
                )
                st.divider()
    else:
        st.warning("Run `python build_rag_index.py` in the app directory to build the index.")
