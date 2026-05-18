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
from config.settings import EMBEDDING_DIMENSION
from storage.storage_backend import storage

log = get_logger("rag.vector_store")

INDEX_KEY = "data/vector_store/faiss.index"
METADATA_KEY = "data/vector_store/chunk_metadata.json"


def build_index(embeddings: list[list[float]], chunks: list[dict]) -> None:
    vectors = np.array(embeddings, dtype="float32")
    index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    index.add(vectors)

    # FAISS requires a file path — write to local then upload
    local_path = storage.abs_path(INDEX_KEY)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(local_path))

    # If using S3, upload the written file
    from config.settings import STORAGE_BACKEND
    if STORAGE_BACKEND == "s3":
        from storage.s3_client import upload_file
        upload_file(local_path, INDEX_KEY)

    metadata = [{"text": c["text"], "document": c["document"], "section": c["section"]} for c in chunks]
    storage.write_json(metadata, METADATA_KEY)
    log.info("FAISS index built: %d vectors, dim=%d", index.ntotal, EMBEDDING_DIMENSION)


def search(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    if not storage.file_exists(INDEX_KEY):
        log.warning("FAISS index not found")
        return []

    # FAISS needs a local file path
    local_index_path = storage.abs_path(INDEX_KEY)
    index = faiss.read_index(str(local_index_path))
    metadata = storage.read_json(METADATA_KEY)

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
