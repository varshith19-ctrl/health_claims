"""
Hybrid Retriever — Combines BM25 (keyword) + FAISS (semantic) with
Reciprocal Rank Fusion for policy retrieval.
"""
import json
import math
from collections import defaultdict
from pathlib import Path
from rank_bm25 import BM25Okapi

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from config.settings import TOP_K_RETRIEVAL
from rag.embeddings import embed_single
from rag.vector_store import search as faiss_search
from storage.storage_backend import storage

log = get_logger("rag.retriever")

METADATA_KEY = "data/vector_store/chunk_metadata.json"
_bm25 = None
_corpus_texts = None


def _load_bm25():
    """
    Loads the chunk metadata and initializes the BM25 index for keyword search.
    Caches the index in memory to avoid reloading on every query.
    """
    global _bm25, _corpus_texts
    if _bm25 is not None:
        return

    if not storage.file_exists(METADATA_KEY):
        log.warning("Chunk metadata not found for BM25")
        return

    metadata = storage.read_json(METADATA_KEY)
    _corpus_texts = [m["text"] for m in metadata]
    tokenized = [text.lower().split() for text in _corpus_texts]
    _bm25 = BM25Okapi(tokenized)
    log.info("BM25 index loaded: %d documents", len(_corpus_texts))


def _bm25_search(query: str, top_k: int) -> list[dict]:
    """
    Performs a keyword-based search using BM25.
    
    Args:
        query (str): The search query string.
        top_k (int): Number of top results to return.
        
    Returns:
        list[dict]: A list of metadata dictionaries representing the top retrieved chunks.
    """
    _load_bm25()
    if _bm25 is None or _corpus_texts is None:
        return []

    tokens = query.lower().split()
    scores = _bm25.get_scores(tokens)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    metadata = storage.read_json(METADATA_KEY)
    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            result = metadata[idx].copy()
            result["bm25_score"] = float(scores[idx])
            results.append(result)
    return results


def _reciprocal_rank_fusion(semantic: list[dict], keyword: list[dict], k: int = 60) -> list[dict]:
    """
    Combines results from semantic and keyword searches using Reciprocal Rank Fusion (RRF).
    RRF scores documents based on their inverse rank across different retrieval lists.
    
    Args:
        semantic (list[dict]): Results from FAISS semantic search.
        keyword (list[dict]): Results from BM25 keyword search.
        k (int): A constant to mitigate the impact of very high rankings.
        
    Returns:
        list[dict]: A single ranked list of merged documents.
    """
    scores = defaultdict(float)
    doc_map = {}

    for rank, doc in enumerate(semantic):
        text_key = doc["text"][:100]
        scores[text_key] += 1.0 / (k + rank + 1)
        doc_map[text_key] = doc

    for rank, doc in enumerate(keyword):
        text_key = doc["text"][:100]
        scores[text_key] += 1.0 / (k + rank + 1)
        doc_map[text_key] = doc

    sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [doc_map[key] for key in sorted_keys]


def retrieve(query: str, top_k: int = TOP_K_RETRIEVAL) -> list[dict]:
    """
    Main retrieval function performing hybrid search (FAISS + BM25) and RRF fusion.
    
    Args:
        query (str): The user query, typically constructed from claim details and ML reasons.
        top_k (int): Number of final combined results to return.
        
    Returns:
        list[dict]: A list of policy chunk dictionaries relevant to the query.
    """
    try:
        query_embedding = embed_single(query)
        semantic_results = faiss_search(query_embedding, top_k=top_k * 2)
    except Exception as exc:
        log.warning("Semantic search failed: %s", exc)
        semantic_results = []

    # Perform BM25 keyword search
    keyword_results = _bm25_search(query, top_k=top_k * 2)

    # Fuse the two result sets using Reciprocal Rank Fusion
    fused = _reciprocal_rank_fusion(semantic_results, keyword_results)
    final = fused[:top_k]
    log.info("Hybrid retrieval: %d results (semantic=%d, keyword=%d)", len(final), len(semantic_results), len(keyword_results))
    return final
