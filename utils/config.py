"""
Configuration Module for Database Data-Quality Analyzer
Handles environment variables, Oracle DB credentials, ML hyperparameters,
and scoring constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Oracle Database Configuration
ORACLE_USER = os.getenv("ORACLE_USER", "admin")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_HOST = os.getenv("ORACLE_HOST", "localhost")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))
ORACLE_SERVICE_NAME = os.getenv("ORACLE_SERVICE_NAME", "XEPDB1")
ORACLE_DSN = os.getenv("ORACLE_DSN", None)

# Runtime / Demonstration Mode
ALLOW_DEMO_MODE = os.getenv("ALLOW_DEMO_MODE", "True").lower() in ("true", "1", "yes")

# Machine Learning Defaults
ML_CONTAMINATION = float(os.getenv("ML_CONTAMINATION", "0.08"))
ML_RANDOM_STATE = int(os.getenv("ML_RANDOM_STATE", "42"))
DBSCAN_EPS = float(os.getenv("DBSCAN_EPS", "0.5"))
DBSCAN_MIN_SAMPLES = int(os.getenv("DBSCAN_MIN_SAMPLES", "5"))

# Scoring Weights
SEVERITY_WEIGHTS = {
    "HIGH": float(os.getenv("WEIGHT_HIGH_SEVERITY", "1.0")),
    "MEDIUM": float(os.getenv("WEIGHT_MEDIUM_SEVERITY", "0.6")),
    "LOW": float(os.getenv("WEIGHT_LOW_SEVERITY", "0.2")),
}

# Directories
DATA_DIR = BASE_DIR / "data"
CLEAN_DATA_DIR = DATA_DIR / "clean"
CORRUPTED_DATA_DIR = DATA_DIR / "corrupted"
REPORTS_DIR = BASE_DIR / "generated_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

