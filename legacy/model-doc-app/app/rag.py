"""
Lightweight RAG over the ragi grading knowledge base.

Corpus (built by `build_rag_index.py`):
  - All grading markdown docs in docs/prompts/model-doc/ (finger_millet_ai_grading.md,
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
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

APP_DIR = Path(__file__).resolve().parent
INDEX_PATH = APP_DIR / "rag_index.npz"
CHUNKS_PATH = APP_DIR / "rag_chunks.jsonl"

EMBEDDING_MODEL = "models/gemini-embedding-2"
TOKEN_RE = re.compile(r"[a-z0-9]+")


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
    with CHUNKS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            chunks.append(Chunk(id=d["id"], source=d["source"],
                                title=d["title"], text=d["text"]))
    return chunks


def _tokenize(text: str) -> list[str]:
    return [tok for tok in TOKEN_RE.findall(text.lower()) if len(tok) > 1]


@lru_cache(maxsize=1)
def _local_retrieval_docs() -> list[dict]:
    docs: list[dict] = []
    chunks = _load_chunks()
    if not chunks:
        return docs

    num_docs = len(chunks)
    doc_freq: dict[str, int] = {}
    tokenized: list[list[str]] = []

    for chunk in chunks:
        tokens = _tokenize(f"{chunk.title}\n{chunk.text}")
        tokenized.append(tokens)
        for token in set(tokens):
            doc_freq[token] = doc_freq.get(token, 0) + 1

    for chunk, tokens in zip(chunks, tokenized):
        tf: dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        docs.append({
            "chunk": chunk,
            "tokens": tokens,
            "tf": tf,
            "doc_freq": doc_freq,
            "num_docs": num_docs,
            "title_lc": chunk.title.lower(),
            "text_lc": chunk.text.lower(),
        })
    return docs


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


def _retrieve_local(query: str, k: int = 5) -> list[tuple[Chunk, float]]:
    docs = _local_retrieval_docs()
    if not docs:
        return []

    query_terms = _tokenize(query)
    if not query_terms:
        return []

    scored: list[tuple[Chunk, float]] = []
    for doc in docs:
        score = 0.0
        term_hits = 0
        tf = doc["tf"]
        doc_freq = doc["doc_freq"]
        num_docs = doc["num_docs"]
        title_lc = doc["title_lc"]
        text_lc = doc["text_lc"]
        token_count = max(1, len(doc["tokens"]))

        for term in query_terms:
            freq = tf.get(term, 0)
            if not freq:
                continue
            term_hits += 1
            idf = math.log(1.0 + (num_docs + 1) / (1 + doc_freq.get(term, 0)))
            score += (1.0 + math.log(freq)) * idf
            if term in title_lc:
                score += 0.35 * idf
            if f" {term} " in f" {text_lc} ":
                score += 0.10 * idf

        if not term_hits:
            continue

        coverage = term_hits / max(1, len(set(query_terms)))
        score *= (0.65 + 0.35 * coverage)
        score /= token_count ** 0.18
        scored.append((doc["chunk"], float(score)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


def retrieve_with_mode(
    client: genai.Client | None,
    query: str,
    k: int = 5,
) -> tuple[list[tuple[Chunk, float]], str]:
    """Return top-k chunks plus the retrieval mode used."""
    if client is None:
        return _retrieve_local(query, k=k), "local-keyword"

    chunks = _load_chunks()
    embeds = _load_index()
    if not chunks or embeds is None or len(chunks) != len(embeds):
        return _retrieve_local(query, k=k), "local-keyword"

    try:
        q = _embed_query(client, query)
        # embeds already L2-normalized during build; cosine == dot product
        scores = embeds @ q
        top_idx = np.argsort(-scores)[:k]
        return [(chunks[i], float(scores[i])) for i in top_idx], "cloud-embedding"
    except Exception:
        return _retrieve_local(query, k=k), "local-keyword"


def retrieve(client: genai.Client | None, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
    """Return top-k chunks with similarity scores. Falls back to local lexical retrieval."""
    hits, _ = retrieve_with_mode(client, query, k=k)
    return hits


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

