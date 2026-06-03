"""
Build the RAG index for the ragi grading knowledge base.

Run this once (and any time the source docs change):
    cd "Grain Quality- Pankaj/docs/prompts/model-doc/app"
    python build_rag_index.py

Outputs:
    rag_chunks.jsonl  — one chunk per line
    rag_index.npz     — float32 embedding matrix [N, D]
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parent / ".env")

APP_DIR = Path(__file__).resolve().parent
MODEL_DOC_DIR = APP_DIR.parent
HANDBOOK_PDF = MODEL_DOC_DIR.parent / "Doc" / "Handbook of Millets - Processing, Quality,.pdf"

MARKDOWN_SOURCES = [
    "finger_millet_ai_grading.md",
    "grade_a_ragi_vision_prompt.md",
    "grade_b_ragi_vision_prompt.md",
    "grade_c_ragi_vision_prompt.md",
    "grades_comparison.md",
]

EMBEDDING_MODEL = "models/gemini-embedding-2"
MAX_CHARS_PER_CHUNK = 1500  # ~400 tokens; within embedding model limits
OVERLAP_CHARS = 150


def read_markdown_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252", errors="replace")


def get_api_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "") or os.environ.get("VERTEX_API_KEY", "")


def use_vertex_ai() -> bool:
    value = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def create_genai_client(api_key: str, vertex_mode: bool = False) -> genai.Client:
    if vertex_mode:
        return genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT") or None,
            location=os.environ.get("GOOGLE_CLOUD_LOCATION") or None,
        )
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY or VERTEX_API_KEY in .env.")
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def chunk_markdown(path: Path, source_label: str) -> list[dict]:
    """Split a markdown file by H1/H2 sections, then by size cap."""
    text = read_markdown_text(path)
    sections = re.split(r"(?m)^(#{1,2} .+)$", text)
    chunks: list[dict] = []
    current_title = path.stem
    buf = ""

    def flush(title: str, body: str):
        body = body.strip()
        if not body:
            return
        # If body exceeds cap, sub-split with overlap
        if len(body) <= MAX_CHARS_PER_CHUNK:
            chunks.append({"source": source_label, "title": title, "text": body})
            return
        i = 0
        while i < len(body):
            sub = body[i:i + MAX_CHARS_PER_CHUNK]
            chunks.append({"source": source_label, "title": title, "text": sub})
            i += MAX_CHARS_PER_CHUNK - OVERLAP_CHARS

    for piece in sections:
        if not piece:
            continue
        if re.match(r"^#{1,2} ", piece):
            flush(current_title, buf)
            current_title = piece.strip("# ").strip()
            buf = ""
        else:
            buf += piece
    flush(current_title, buf)
    return chunks


def chunk_pdf(path: Path, source_label: str) -> list[dict]:
    import pypdf

    reader = pypdf.PdfReader(str(path))
    chunks: list[dict] = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        title = f"Handbook p.{page_num}"
        if len(text) <= MAX_CHARS_PER_CHUNK:
            chunks.append({"source": source_label, "title": title, "text": text})
            continue
        i = 0
        while i < len(text):
            chunks.append({
                "source": source_label,
                "title": title,
                "text": text[i:i + MAX_CHARS_PER_CHUNK],
            })
            i += MAX_CHARS_PER_CHUNK - OVERLAP_CHARS
    return chunks


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
def embed_documents(client: genai.Client, texts: list[str]) -> np.ndarray:
    vectors: list[np.ndarray] = []
    # google-genai embeds one doc per call for stability
    for i, t in enumerate(texts):
        resp = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=t,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        v = np.asarray(resp.embeddings[0].values, dtype=np.float32)
        v /= np.linalg.norm(v) + 1e-12  # L2-normalize for cosine = dot
        vectors.append(v)
        if (i + 1) % 5 == 0 or i + 1 == len(texts):
            print(f"  embedded {i + 1}/{len(texts)}")
    return np.stack(vectors)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    api_key = get_api_key()
    vertex_mode = use_vertex_ai()
    if not vertex_mode and not api_key:
        raise SystemExit("Set GEMINI_API_KEY or VERTEX_API_KEY in .env before building the index.")

    client = create_genai_client(api_key, vertex_mode)

    all_chunks: list[dict] = []

    print("Chunking markdown docs…")
    for fname in MARKDOWN_SOURCES:
        p = MODEL_DOC_DIR / fname
        if not p.exists():
            print(f"  SKIP (missing): {fname}")
            continue
        part = chunk_markdown(p, source_label=fname)
        print(f"  {fname}: {len(part)} chunks")
        all_chunks.extend(part)

    if HANDBOOK_PDF.exists():
        print(f"Chunking handbook PDF: {HANDBOOK_PDF.name}")
        part = chunk_pdf(HANDBOOK_PDF, source_label=HANDBOOK_PDF.name)
        print(f"  {HANDBOOK_PDF.name}: {len(part)} chunks")
        all_chunks.extend(part)
    else:
        print(f"Handbook PDF not found at {HANDBOOK_PDF}")

    # Assign ids
    for i, c in enumerate(all_chunks):
        c["id"] = f"chunk_{i:04d}"

    print(f"\nTotal chunks: {len(all_chunks)}")
    if not all_chunks:
        raise SystemExit("No markdown or PDF chunks found; restore the source documents first.")
    print("Embedding…")
    embeddings = embed_documents(client, [c["text"] for c in all_chunks])

    # Persist
    chunks_path = APP_DIR / "rag_chunks.jsonl"
    index_path = APP_DIR / "rag_index.npz"
    with chunks_path.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    np.savez(index_path, embeddings=embeddings)

    print(f"\nWrote {chunks_path.name} ({chunks_path.stat().st_size:,} bytes)")
    print(f"Wrote {index_path.name} ({index_path.stat().st_size:,} bytes)")
    print(f"Embedding shape: {embeddings.shape}")


if __name__ == "__main__":
    main()

