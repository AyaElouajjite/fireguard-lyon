"""
Importe le dataset CSV dans MongoDB.
"""

import sys

import pandas as pd
from pymongo import UpdateOne

from config import DATASET_PATH
from database import MongoDB
from generate_dataset import main as generate_main


def seed():
    if not DATASET_PATH.exists():
        print("Dataset introuvable, génération en cours...")
        generate_main()

    df = pd.read_csv(DATASET_PATH)
    db = MongoDB()

    if not db.ping():
        print("MongoDB inaccessible — le projet utilisera le mode CSV.")
        return False

    records = df.to_dict(orient="records")
    for r in records:
        r["detection_automatique"] = bool(r["detection_automatique"])
        r["alerte_preventive"] = bool(r["alerte_preventive"])

    db.incidents.delete_many({})
    operations = [
        UpdateOne({"id": r["id"]}, {"$set": r}, upsert=True)
        for r in records
    ]
    if operations:
        db.incidents.bulk_write(operations)

    db.ensure_indexes()
    print(f"MongoDB alimenté : {len(records)} incidents dans '{db.db.name}.incidents'")
    return True


if __name__ == "__main__":
    ok = seed()
    sys.exit(0 if ok else 1)
