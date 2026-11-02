import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings(BaseModel):
    PROJECT_NAME: str = "AI Production Incident Investigator"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Database config: default to robust SQLite if PostgreSQL is not specified
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'incident_investigator.db'}"
    )
    
    # Retrieval Hyperparameters
    BASELINE_TOP_K: int = 3
    ADAPTIVE_THRESHOLD: float = 0.55
    ADAPTIVE_MAX_K: int = 5
    
    # Remediation Safety Limits
    MAX_REMEDIATION_RETRIES: int = 3
    VERIFICATION_WAIT_SECONDS: float = 1.0
    
    # ShopEase Integration & Automatic Background Monitoring Config
    SHOP_EASE_BASE_URL: str = os.getenv("SHOP_EASE_BASE_URL", "http://localhost:5000")
    POLL_INTERVAL_SECONDS: int = 5
    ENABLE_BACKGROUND_MONITORING: bool = os.getenv("ENABLE_BACKGROUND_MONITORING", "true").lower() in ("true", "1", "yes")
    MONITORING_INTERVAL_SECONDS: float = float(os.getenv("MONITORING_INTERVAL_SECONDS", "3.0"))
    CONSECUTIVE_ANOMALIES_THRESHOLD: int = int(os.getenv("CONSECUTIVE_ANOMALIES_THRESHOLD", "2"))

    # Paths
    DATA_DIR: Path = DATA_DIR
    HISTORICAL_INCIDENTS_PATH: Path = DATA_DIR / "historical_incidents.json"
    EVAL_DATASET_PATH: Path = DATA_DIR / "eval_labeled_dataset.json"
    SAMPLE_KAGGLE_PATH: Path = DATA_DIR / "sample_kaggle_aiops.csv"

settings = Settings()
