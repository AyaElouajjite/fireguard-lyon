"""
Couche d'accès aux données : MongoDB en priorité, fallback CSV.
"""

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

import pandas as pd

from config import DATASET_PATH, PREDICTIONS_HISTORY_PATH
from database import MongoDB


class DataStore:
    def __init__(self):
        self.mongo = MongoDB()
        self._df: pd.DataFrame | None = None
        self.use_mongo = self.mongo.ping()

    def _load_csv(self) -> pd.DataFrame:
        if self._df is None:
            self._df = pd.read_csv(DATASET_PATH)
            self._df["detection_automatique"] = self._df["detection_automatique"].astype(bool)
            self._df["alerte_preventive"] = self._df["alerte_preventive"].astype(bool)
        return self._df

    def ping(self) -> bool:
        return self.use_mongo

    def mode(self) -> str:
        return "mongodb" if self.use_mongo else "csv"

    def ensure_indexes(self) -> None:
        if self.use_mongo:
            self.mongo.ensure_indexes()

    def get_stats(self) -> dict[str, Any]:
        if self.use_mongo:
            return self.mongo.get_stats()
        df = self._load_csv()
        return {
            "total_incidents": len(df),
            "par_risque": df["niveau_risque"].value_counts().to_dict(),
            "par_type": df["type_incendie"].value_counts().to_dict(),
            "par_quartier": df["quartier"].value_counts().head(12).to_dict(),
            "gravite_moyenne": round(df["gravite"].mean(), 2),
            "surface_totale_m2": int(df["surface_m2"].sum()),
            "degats_totaux_eur": int(df["degats_estimes_eur"].sum()),
        }

    def get_monthly_trend(self) -> list[dict]:
        if self.use_mongo:
            return self.mongo.get_monthly_trend()
        df = self._load_csv()
        grouped = df.groupby(["annee", "mois"]).agg(
            incidents=("id", "count"),
            gravite_moyenne=("gravite", "mean"),
        ).reset_index()
        return [
            {
                "periode": f"{r.annee}-{r.mois:02d}",
                "incidents": int(r.incidents),
                "gravite_moyenne": round(r.gravite_moyenne, 2),
            }
            for r in grouped.itertuples()
        ]

    def get_heatmap_data(self) -> list[dict]:
        if self.use_mongo:
            return self.mongo.get_heatmap_data()
        df = self._load_csv()
        cols = ["latitude", "longitude", "gravite", "niveau_risque", "quartier"]
        return df[cols].head(500).to_dict(orient="records")

    def get_incidents(
        self,
        limit: int = 50,
        quartier: str | None = None,
        niveau_risque: str | None = None,
        type_incendie: str | None = None,
    ) -> list[dict]:
        if self.use_mongo:
            query: dict[str, Any] = {}
            if quartier:
                query["quartier"] = quartier
            if niveau_risque:
                query["niveau_risque"] = niveau_risque
            if type_incendie:
                query["type_incendie"] = type_incendie
            return list(
                self.mongo.incidents.find(query, {"_id": 0})
                .sort("date_heure", -1)
                .limit(limit)
            )

        df = self._load_csv()
        if quartier:
            df = df[df["quartier"] == quartier]
        if niveau_risque:
            df = df[df["niveau_risque"] == niveau_risque]
        if type_incendie:
            df = df[df["type_incendie"] == type_incendie]
        return df.sort_values("date_heure", ascending=False).head(limit).to_dict(orient="records")

    def get_quartiers(self) -> list[dict]:
        if self.use_mongo:
            pipeline = [
                {"$group": {"_id": "$quartier", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
            return [{"quartier": r["_id"], "count": r["count"]} for r in self.mongo.incidents.aggregate(pipeline)]

        df = self._load_csv()
        counts = df["quartier"].value_counts()
        return [{"quartier": k, "count": int(v)} for k, v in counts.items()]

    def get_hourly_distribution(self) -> list[dict]:
        if self.use_mongo:
            pipeline = [
                {"$group": {"_id": "$heure", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
            return [{"heure": r["_id"], "count": r["count"]} for r in self.mongo.incidents.aggregate(pipeline)]

        df = self._load_csv()
        counts = df["heure"].value_counts().sort_index()
        return [{"heure": int(h), "count": int(c)} for h, c in counts.items()]

    def save_prediction(self, data: dict) -> dict:
        record = {k: v for k, v in data.items() if k != "_id"}
        if "id" not in record:
            ts = datetime.now()
            record["id"] = f"PRED-{ts.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"

        if self.use_mongo:
            self.mongo.predictions.insert_one(record.copy())

        history = self._load_predictions_file()
        history.insert(0, record)
        self._save_predictions_file(history[:500])
        return record

    def get_predictions(self, limit: int = 50) -> list[dict]:
        if self.use_mongo:
            return list(
                self.mongo.predictions.find({}, {"_id": 0})
                .sort("timestamp", -1)
                .limit(limit)
            )
        return self._load_predictions_file()[:limit]

    def _load_predictions_file(self) -> list[dict]:
        if not PREDICTIONS_HISTORY_PATH.exists():
            return []
        try:
            with open(PREDICTIONS_HISTORY_PATH, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_predictions_file(self, history: list[dict]) -> None:
        PREDICTIONS_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PREDICTIONS_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
