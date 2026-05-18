"""
Pipeline orchestrator — runs Bronze -> Silver -> Gold in sequence.
Each stage returns a status dict for compatibility with Apache Airflow PythonOperator.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger

log = get_logger("pipeline")


def run_bronze() -> dict:
    """Stage 1: Ingest raw CSV -> Bronze parquet."""
    log.info("--- Stage 1: Bronze ---")
    from data_engineering.bronze.bronze_layer import ingest_to_bronze
    tables = ingest_to_bronze()
    return {"stage": "bronze", "tables": len(tables), "status": "success"}


def run_silver() -> dict:
    """Stage 2: Clean Bronze -> Silver parquet."""
    log.info("--- Stage 2: Silver ---")
    from data_engineering.silver.silver_layer import build_silver
    tables = build_silver()
    return {"stage": "silver", "tables": len(tables), "status": "success"}


def run_gold() -> dict:
    """Stage 3: Feature engineering Silver -> Gold parquet."""
    log.info("--- Stage 3: Gold ---")
    from data_engineering.gold.gold_layer import build_gold
    gold = build_gold()
    return {"stage": "gold", "rows": len(gold), "status": "success"}


def run_ml_training() -> dict:
    """Stage 4: Train ML models on Gold features."""
    log.info("--- Stage 4: ML Training ---")
    from ml.train import train_all
    train_all()
    return {"stage": "ml_training", "status": "success"}


def run_rag_indexing() -> dict:
    """Stage 5: Build FAISS vector index from policy PDFs."""
    log.info("--- Stage 5: RAG Indexing ---")
    from rag.chunker import hierarchical_chunk
    from rag.embeddings import embed_texts
    from rag.vector_store import build_index
    chunks = hierarchical_chunk()
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    build_index(embeddings, chunks)
    return {"stage": "rag_indexing", "chunks": len(chunks), "status": "success"}


def run_pipeline() -> dict:
    """Full pipeline: Bronze -> Silver -> Gold -> ML -> RAG."""
    log.info("========== ETL PIPELINE START ==========")
    results = {}
    results["bronze"] = run_bronze()
    results["silver"] = run_silver()
    results["gold"] = run_gold()
    results["ml"] = run_ml_training()
    # RAG indexing is optional (requires OpenAI API key)
    try:
        results["rag"] = run_rag_indexing()
    except Exception as exc:
        log.warning("RAG indexing skipped: %s", exc)
        results["rag"] = {"stage": "rag_indexing", "status": "skipped", "reason": str(exc)}
    log.info("========== ETL PIPELINE COMPLETE ==========")
    return results


if __name__ == "__main__":
    run_pipeline()
