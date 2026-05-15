"""
Embeddings — Uses OpenAI text-embedding-3-small to embed text chunks.
"""
from openai import OpenAI
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from config.settings import OPENAI_API_KEY, EMBEDDING_MODEL

log = get_logger("rag.embeddings")

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    client = _get_client()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            log.info("Embedded batch %d-%d (%d texts)", i, i + len(batch), len(batch))
        except Exception as exc:
            log.error("Embedding failed for batch %d: %s", i, exc)
            raise

    return all_embeddings


def embed_single(text: str) -> list[float]:
    return embed_texts([text])[0]
