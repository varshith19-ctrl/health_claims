import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "raw_data"
DATA_DIR = BASE_DIR / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
MODEL_DIR = BASE_DIR / "ml" / "models"
LOG_DIR = BASE_DIR / "logs"

for d in [DATA_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, CHECKPOINT_DIR, VECTOR_STORE_DIR, MODEL_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

RAW_FILES = {
    "claims": RAW_DATA_DIR / "claims_1000.csv",
    "providers": RAW_DATA_DIR / "providers_1000.csv",
    "diagnosis": RAW_DATA_DIR / "diagnosis.csv",
    "cost": RAW_DATA_DIR / "cost.csv",
}

POLICY_PDFS = list(RAW_DATA_DIR.glob("policy_pdf_*.pdf"))

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"
EMBEDDING_DIMENSION = 1536

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K_RETRIEVAL = 5

TEST_SPLIT_RATIO = 0.2
RANDOM_STATE = 42

API_HOST = "0.0.0.0"
API_PORT = 8000
API_TOKEN = os.getenv("API_TOKEN", "health-claims-secret-token")
