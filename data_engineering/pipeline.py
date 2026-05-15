"""
Pipeline orchestrator — runs Bronze -> Silver -> Gold in sequence.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger

log = get_logger("pipeline")


def run_pipeline():
    log.info("========== ETL PIPELINE START ==========")

    log.info("--- Stage 1: Bronze ---")
    from data_engineering.bronze.bronze_layer import ingest_to_bronze
    ingest_to_bronze()

    log.info("--- Stage 2: Silver ---")
    from data_engineering.silver.silver_layer import build_silver
    build_silver()

    log.info("--- Stage 3: Gold ---")
    from data_engineering.gold.gold_layer import build_gold
    build_gold()

    log.info("========== ETL PIPELINE COMPLETE ==========")


if __name__ == "__main__":
    run_pipeline()
