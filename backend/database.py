from typing import Any

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from config import (
    COLLECTION_INCIDENTS,
    COLLECTION_PREDICTIONS,
    MONGO_DB,
    MONGO_URI,
)


class MongoDB:
    def __init__(self, uri: str = MONGO_URI, db_name: str = MONGO_DB):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db: Database = self.client[db_name]

    @property
    def incidents(self) -> Collection:
        return self.db[COLLECTION_INCIDENTS]

    @property
    def predictions(self) -> Collection:
        return self.db[COLLECTION_PREDICTIONS]

    def ensure_indexes(self) -> None:
        self.incidents.create_index([("date_heure", ASCENDING)])
        self.incidents.create_index([("quartier", ASCENDING)])
        self.incidents.create_index([("niveau_risque", ASCENDING)])
        self.incidents.create_index([("type_incendie", ASCENDING)])
        self.predictions.create_index([("created_at", ASCENDING)])

    def ping(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def get_stats(self) -> dict[str, Any]:
        pipeline = [
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "par_risque": [
                        {"$group": {"_id": "$niveau_risque", "count": {"$sum": 1}}}
                    ],
                    "par_type": [
                        {"$group": {"_id": "$type_incendie", "count": {"$sum": 1}}}
                    ],
                    "par_quartier": [
                        {"$group": {"_id": "$quartier", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 12},
                    ],
                    "gravite_moy": [
                        {"$group": {"_id": None, "avg": {"$avg": "$gravite"}}}
                    ],
                    "surface_totale": [
                        {"$group": {"_id": None, "total": {"$sum": "$surface_m2"}}}
                    ],
                    "degats_totaux": [
                        {"$group": {"_id": None, "total": {"$sum": "$degats_estimes_eur"}}}
                    ],
                }
            }
        ]
        result = list(self.incidents.aggregate(pipeline))
        if not result:
            return {}

        data = result[0]
        return {
            "total_incidents": data["total"][0]["count"] if data["total"] else 0,
            "par_risque": {r["_id"]: r["count"] for r in data["par_risque"]},
            "par_type": {r["_id"]: r["count"] for r in data["par_type"]},
            "par_quartier": {r["_id"]: r["count"] for r in data["par_quartier"]},
            "gravite_moyenne": round(data["gravite_moy"][0]["avg"], 2) if data["gravite_moy"] else 0,
            "surface_totale_m2": data["surface_totale"][0]["total"] if data["surface_totale"] else 0,
            "degats_totaux_eur": data["degats_totaux"][0]["total"] if data["degats_totaux"] else 0,
        }

    def get_monthly_trend(self) -> list[dict]:
        pipeline = [
            {
                "$group": {
                    "_id": {"annee": "$annee", "mois": "$mois"},
                    "count": {"$sum": 1},
                    "gravite_moy": {"$avg": "$gravite"},
                }
            },
            {"$sort": {"_id.annee": 1, "_id.mois": 1}},
        ]
        return [
            {
                "periode": f"{r['_id']['annee']}-{r['_id']['mois']:02d}",
                "incidents": r["count"],
                "gravite_moyenne": round(r["gravite_moy"], 2),
            }
            for r in self.incidents.aggregate(pipeline)
        ]

    def get_heatmap_data(self) -> list[dict]:
        return list(
            self.incidents.find(
                {},
                {"_id": 0, "latitude": 1, "longitude": 1, "gravite": 1, "niveau_risque": 1, "quartier": 1},
            ).limit(500)
        )
