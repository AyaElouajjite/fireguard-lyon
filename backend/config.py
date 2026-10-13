import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "fire_detection_lyon")
COLLECTION_INCIDENTS = "incidents"
COLLECTION_PREDICTIONS = "predictions"

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

DATASET_PATH = DATA_DIR / "incendies_lyon.csv"
PREDICTIONS_HISTORY_PATH = DATA_DIR / "predictions_history.json"
MODEL_PATH = MODELS_DIR / "fire_risk_model.joblib"
SCALER_PATH = MODELS_DIR / "scaler.joblib"
ENCODERS_PATH = MODELS_DIR / "encoders.joblib"
