"""
Vector Store — FAISS index for semantic search over policy chunks.
"""
import json
import numpy as np
import faiss
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from config.settings import VECTOR_STORE_DIR, EMBEDDING_DIMENSION

log = get_logger("rag.vector_store")

INDEX_PATH = VECTOR_STORE_DIR / "faiss.index"
METADATA_PATH = VECTOR_STORE_DIR / "chunk_metadata.json"


def build_index(embeddings: list[list[float]], chunks: list[dict]) -> None:
    vectors = np.array(embeddings, dtype="float32")
    index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    index.add(vectors)
    faiss.write_index(index, str(INDEX_PATH))

    metadata = [{"text": c["text"], "document": c["document"], "section": c["section"]} for c in chunks]
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    log.info("FAISS index built: %d vectors, dim=%d", index.ntotal, EMBEDDING_DIMENSION)


def search(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    if not INDEX_PATH.exists():
        log.warning("FAISS index not found")
        return []

    index = faiss.read_index(str(INDEX_PATH))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))

    query_vec = np.array([query_embedding], dtype="float32")
    distances, indices = index.search(query_vec, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(metadata):
            result = metadata[idx].copy()
            result["score"] = float(dist)
            results.append(result)

    log.info("FAISS search: %d results returned", len(results))
    return results
