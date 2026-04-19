"""
Lightweight RAG over the ragi grading knowledge base.

Corpus (built by `build_rag_index.py`):
  - All grading markdown docs in Model Doc/ (finger_millet_ai_grading.md,
    grade_a/b/c_ragi_vision_prompt.md, grades_comparison.md)
  - Handbook of Millets PDF text

Storage:
  - index.npz   — numpy array of float32 embeddings, shape [N, D]
  - chunks.jsonl — one JSON per line: {id, source, title, text}

Embedding model: Google `text-embedding-004` (via google-genai client).
Retrieval: cosine similarity, top-k.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

APP_DIR = Path(__file__).resolve().parent
INDEX_PATH = APP_DIR / "rag_index.npz"
CHUNKS_PATH = APP_DIR / "rag_chunks.jsonl"

EMBEDDING_MODEL = "text-embedding-004"


@dataclass
class Chunk:
    id: str
    source: str
    title: str
    text: str


def _load_chunks() -> list[Chunk]:
    if not CHUNKS_PATH.exists():
        return []
    chunks: list[Chunk] = []
    with CHUNKS_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            chunks.append(Chunk(id=d["id"], source=d["source"],
                                title=d["title"], text=d["text"]))
    return chunks


def _load_index() -> np.ndarray | None:
    if not INDEX_PATH.exists():
        return None
    data = np.load(INDEX_PATH)
    return data["embeddings"].astype(np.float32)


def _embed_query(client: genai.Client, query: str) -> np.ndarray:
    resp = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    vec = np.asarray(resp.embeddings[0].values, dtype=np.float32)
    return vec / (np.linalg.norm(vec) + 1e-12)


def retrieve(client: genai.Client, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
    """Return top-k chunks with cosine similarity scores. Empty list if no index."""
    chunks = _load_chunks()
    embeds = _load_index()
    if not chunks or embeds is None or len(chunks) != len(embeds):
        return []
    q = _embed_query(client, query)
    # embeds already L2-normalized during build; cosine == dot product
    scores = embeds @ q
    top_idx = np.argsort(-scores)[:k]
    return [(chunks[i], float(scores[i])) for i in top_idx]


def format_retrieved(items: list[tuple[Chunk, float]]) -> str:
    """Format retrieved chunks into a prompt-ready context block."""
    if not items:
        return ""
    parts = ["# RETRIEVED CONTEXT (from knowledge base)"]
    for chunk, score in items:
        parts.append(f"\n## [{chunk.source}] {chunk.title}  (relevance {score:.2f})")
        parts.append(chunk.text)
    return "\n".join(parts)


def index_exists() -> bool:
    return INDEX_PATH.exists() and CHUNKS_PATH.exists()
