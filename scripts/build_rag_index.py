import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitoring.logger import get_logger
from rag.chunker import hierarchical_chunk
from rag.embeddings import embed_texts
from rag.vector_store import build_index

log = get_logger("rag.build_index")

def run():
    log.info("Starting RAG index build")
    chunks = hierarchical_chunk()
    if not chunks:
        log.warning("No chunks generated. Check if PDFs exist.")
        return
        
    texts_to_embed = [c["text"] for c in chunks]
    embeddings = embed_texts(texts_to_embed)
    build_index(embeddings, chunks)
    log.info("RAG index build complete.")

if __name__ == "__main__":
    run()
