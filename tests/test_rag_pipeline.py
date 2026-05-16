"""
Test Suite 3 — RAG Pipeline Validation.
Checks that the vector store exists, retrieval returns relevant results,
and different queries produce different outputs.
NOTE: LLM generation is NOT tested here (requires paid API key).
"""
import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import VECTOR_STORE_DIR


# ── Vector Store File Tests ─────────────────────────────────────────

class TestVectorStoreFiles:
    """Verify FAISS index and chunk metadata exist."""

    def test_faiss_index_exists(self):
        path = VECTOR_STORE_DIR / "faiss.index"
        assert path.exists(), "FAISS index file missing"

    def test_chunk_metadata_exists(self):
        path = VECTOR_STORE_DIR / "chunk_metadata.json"
        assert path.exists(), "Chunk metadata file missing"

    def test_chunk_metadata_is_valid_json(self):
        path = VECTOR_STORE_DIR / "chunk_metadata.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, list), "Chunk metadata should be a JSON array"
        assert len(data) > 0, "Chunk metadata is empty"

    def test_chunks_have_text_field(self):
        path = VECTOR_STORE_DIR / "chunk_metadata.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for i, chunk in enumerate(data[:5]):
            assert "text" in chunk, f"Chunk {i} missing 'text' field"
            assert len(chunk["text"]) > 0, f"Chunk {i} has empty text"


# ── Retrieval Tests ─────────────────────────────────────────────────

class TestRetrieval:
    """Verify hybrid retrieval returns relevant, non-empty results."""

    def test_retrieval_returns_results(self):
        from rag.retriever import retrieve
        results = retrieve("billing amount exceeds regional average")
        assert len(results) > 0, "Retriever returned no results"

    def test_retrieved_chunks_have_text(self):
        from rag.retriever import retrieve
        results = retrieve("billing amount exceeds regional average")
        for i, chunk in enumerate(results):
            assert "text" in chunk, f"Result {i} missing 'text' field"
            assert len(chunk["text"]) > 10, f"Result {i} has suspiciously short text"

    def test_different_queries_return_different_results(self):
        from rag.retriever import retrieve
        results_cost = retrieve("billed amount higher than average cost")
        results_auth = retrieve("prior authorization required for procedure")

        # Extract first chunk text from each
        text_cost = results_cost[0]["text"][:100] if results_cost else ""
        text_auth = results_auth[0]["text"][:100] if results_auth else ""
        assert text_cost != text_auth, "Different queries returned identical top results"

    def test_retrieval_works_for_claim_like_query(self):
        """Simulate the actual query format used by claim_agent.py."""
        from rag.retriever import retrieve
        query = "Policy rules for Procedure PROC1 and Diagnosis D10 regarding: Billed vs Regional Average (45.2% contribution)"
        results = retrieve(query)
        assert len(results) > 0, "Retriever failed on a real claim-style query"
