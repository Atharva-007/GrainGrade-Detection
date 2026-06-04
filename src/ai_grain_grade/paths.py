"""Central project paths for runtime code and tests."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAG_DATA_DIR = DATA_DIR / "rag"
RAG_INDEX_PATH = RAG_DATA_DIR / "rag_index.json"
RAG_EMBEDDINGS_PATH = RAG_DATA_DIR / "rag_index.embeddings.npz"

FEEDBACK_DIR = DATA_DIR / "feedback" / "feedback_data"
SESSION_UPLOADS_DIR = FEEDBACK_DIR / "session_uploads"

DOCS_DIR = PROJECT_ROOT / "docs"
RAG_DOCS_DIR = DOCS_DIR / "rag"
EXAMPLES_DIR = PROJECT_ROOT / "examples"


def ensure_runtime_dirs() -> None:
    """Create writable runtime directories used by the app."""
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)
