"""
Modèle ML pour la prédiction du niveau de risque d'incendie.
Utilise Random Forest + Gradient Boosting (voting classifier).
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from config import DATASET_PATH, ENCODERS_PATH, MODEL_PATH, MODELS_DIR, SCALER_PATH


FEATURE_COLS = [
    "mois", "jour_semaine", "heure",
    "temperature_c", "humidite_pct", "vent_vitesse_kmh", "indice_secheresse",
    "surface_m2", "duree_intervention_min",
]
CATEGORICAL_COLS = ["quartier", "type_incendie", "origine"]
TARGET_COL = "niveau_risque"


class FireRiskModel:
    def __init__(self):
        self.pipeline: Pipeline | None = None
        self.label_encoders: dict[str, LabelEncoder] = {}
        self.feature_names: list[str] = []
        self.metrics: dict[str, Any] = {}

    def _encode_categoricals(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        encoded = df.copy()
        for col in CATEGORICAL_COLS:
            if fit:
                le = LabelEncoder()
                encoded[col] = le.fit_transform(encoded[col].astype(str))
                self.label_encoders[col] = le
            else:
                le = self.label_encoders[col]
                encoded[col] = encoded[col].astype(str).map(
                    {cls: i for i, cls in enumerate(le.classes_)}
                ).fillna(-1).astype(int)
        return encoded

    def prepare_features(self, df: pd.DataFrame, fit: bool = False) -> tuple[np.ndarray, np.ndarray | None]:
        encoded = self._encode_categoricals(df, fit=fit)
        self.feature_names = FEATURE_COLS + CATEGORICAL_COLS
        X = encoded[self.feature_names].values
        y = None
        if TARGET_COL in df.columns:
            if "target_encoder" not in self.label_encoders:
                self.label_encoders["target_encoder"] = LabelEncoder()
            if fit:
                y = self.label_encoders["target_encoder"].fit_transform(df[TARGET_COL])
            else:
                y = self.label_encoders["target_encoder"].transform(df[TARGET_COL])
        return X, y

    def train(self, df: pd.DataFrame | None = None) -> dict[str, Any]:
        if df is None:
            df = pd.read_csv(DATASET_PATH)

        X, y = self.prepare_features(df, fit=True)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        rf = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
        gb = GradientBoostingClassifier(n_estimators=100, max_depth=6, random_state=42)
        classifier = VotingClassifier(
            estimators=[("rf", rf), ("gb", gb)],
            voting="soft",
        )

        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", classifier),
        ])
        self.pipeline.fit(X_train, y_train)

        y_pred = self.pipeline.predict(X_test)
        y_proba = self.pipeline.predict_proba(X_test)

        classes = self.label_encoders["target_encoder"].classes_
        self.metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "classification_report": classification_report(y_test, y_pred, target_names=classes, output_dict=True),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "classes": classes.tolist(),
            "feature_importance": self._get_feature_importance(),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "trained_at": datetime.now().isoformat(),
        }
        return self.metrics

    def _get_feature_importance(self) -> list[dict]:
        rf_model = self.pipeline.named_steps["classifier"].named_estimators_["rf"]
        importances = rf_model.feature_importances_
        return sorted(
            [{"feature": f, "importance": round(float(v), 4)} for f, v in zip(self.feature_names, importances)],
            key=lambda x: x["importance"],
            reverse=True,
        )

    def predict(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.pipeline is None:
            self.load()

        df = pd.DataFrame([data])
        X, _ = self.prepare_features(df, fit=False)
        pred_idx = int(self.pipeline.predict(X)[0])
        proba = self.pipeline.predict_proba(X)[0]
        classes = self.label_encoders["target_encoder"].classes_

        return {
            "niveau_risque_predit": classes[pred_idx],
            "confiance": round(float(max(proba)), 4),
            "probabilites": {
                cls: round(float(p), 4) for cls, p in zip(classes, proba)
            },
        }

    def predict_batch(self, records: list[dict]) -> list[dict]:
        return [self.predict(r) for r in records]

    def save(self) -> None:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, MODEL_PATH)
        joblib.dump(self.label_encoders, ENCODERS_PATH)
        if self.metrics:
            joblib.dump(self.metrics, MODELS_DIR / "metrics.joblib")

    def load(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError("Modèle non entraîné. Exécutez train_model.py d'abord.")
        self.pipeline = joblib.load(MODEL_PATH)
        self.label_encoders = joblib.load(ENCODERS_PATH)
        metrics_path = MODELS_DIR / "metrics.joblib"
        if metrics_path.exists():
            self.metrics = joblib.load(metrics_path)


def train_and_save() -> dict[str, Any]:
    model = FireRiskModel()
    metrics = model.train()
    model.save()
    return metrics
