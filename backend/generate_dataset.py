"""
Génération d'un dataset synthétique d'incendies pour la ville de Lyon.
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from config import DATASET_PATH

random.seed(42)
np.random.seed(42)

QUARTIERS = {
    "Presqu'île": (45.7578, 4.8320),
    "Vieux Lyon": (45.7622, 4.8270),
    "Part-Dieu": (45.7606, 4.8494),
    "Confluence": (45.7410, 4.8180),
    "Croix-Rousse": (45.7750, 4.8320),
    "Guillotière": (45.7480, 4.8450),
    "Vaise": (45.7750, 4.8050),
    "Gerland": (45.7260, 4.8320),
    "Monplaisir": (45.7380, 4.8720),
    "Brotteaux": (45.7680, 4.8550),
    "États-Unis": (45.7450, 4.8650),
    "Mermoz": (45.7350, 4.8850),
}

TYPES_INCENDIE = [
    "Domestique",
    "Industriel",
    "Véhicule",
    "Végétation",
    "Électrique",
    "Commercial",
]

ORIGINES = [
    "Cuisine",
    "Court-circuit",
    "Cigarette",
    "Chauffage",
    "Incendie criminel",
    "Foudre",
    "Accident routier",
    "Inconnu",
]

MOIS_RISQUE = {
    1: 0.9, 2: 0.85, 3: 0.8, 4: 0.75, 5: 0.7,
    6: 0.95, 7: 1.2, 8: 1.3, 9: 1.0, 10: 0.85,
    11: 0.9, 12: 1.1,
}


def generate_incidents(n: int = 2500) -> pd.DataFrame:
    start = datetime(2022, 1, 1)
    end = datetime(2024, 12, 31)
    delta_days = (end - start).days

    records = []
    for i in range(n):
        day_offset = random.randint(0, delta_days)
        hour_weights = np.array([
            2, 2, 2, 2, 3, 4, 5, 6, 7, 6, 5, 5,
            6, 6, 5, 5, 5, 6, 7, 8, 9, 8, 6, 4
        ], dtype=float)
        hour_weights /= hour_weights.sum()
        hour = int(np.random.choice(range(24), p=hour_weights))
        minute = random.randint(0, 59)
        date_heure = start + timedelta(days=day_offset, hours=hour, minutes=minute)

        quartier = random.choice(list(QUARTIERS.keys()))
        lat_base, lon_base = QUARTIERS[quartier]
        latitude = lat_base + np.random.normal(0, 0.004)
        longitude = lon_base + np.random.normal(0, 0.004)

        mois = date_heure.month
        saison_factor = MOIS_RISQUE[mois]
        type_inc = random.choices(
            TYPES_INCENDIE,
            weights=[35, 12, 15, 10, 18, 10],
            k=1
        )[0]

        temperature = np.clip(
            5 + 20 * np.sin((mois - 1) * np.pi / 6) + np.random.normal(0, 4),
            -5, 42
        )
        humidite = np.clip(80 - temperature * 0.8 + np.random.normal(0, 10), 15, 98)
        vent_vitesse = max(0, np.random.exponential(8) * (1.3 if mois in [6, 7, 8] else 1.0))
        indice_secheresse = np.clip(
            (temperature - 15) * 2 + (100 - humidite) * 0.3 + vent_vitesse * 0.5,
            0, 100
        )

        base_gravite = random.choices([1, 2, 3, 4, 5], weights=[25, 30, 25, 15, 5], k=1)[0]
        gravite = min(5, max(1, int(base_gravite + indice_secheresse / 40 + random.randint(-1, 1))))

        surface = max(1, int(np.random.lognormal(2.5, 1.2) * (gravite / 3) * saison_factor))
        duree = max(5, int(np.random.lognormal(3.5, 0.6) * gravite))

        risque_score = (
            indice_secheresse * 0.35
            + vent_vitesse * 2
            + gravite * 8
            + (1 if type_inc in ("Végétation", "Industriel") else 0) * 15
            + (1 if hour in range(18, 23) else 0) * 10
        )
        niveau_risque = "Élevé" if risque_score > 70 else ("Modéré" if risque_score > 40 else "Faible")

        detection_auto = random.random() < (0.35 + gravite * 0.08)
        alerte_preventive = random.random() < (indice_secheresse / 120)

        records.append({
            "id": f"INC-{date_heure.strftime('%Y%m%d')}-{i+1:04d}",
            "ville": "Lyon",
            "date_heure": date_heure.isoformat(),
            "annee": date_heure.year,
            "mois": mois,
            "jour_semaine": date_heure.weekday(),
            "heure": hour,
            "quartier": quartier,
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "type_incendie": type_inc,
            "origine": random.choice(ORIGINES),
            "gravite": gravite,
            "temperature_c": round(temperature, 1),
            "humidite_pct": round(humidite, 1),
            "vent_vitesse_kmh": round(vent_vitesse, 1),
            "indice_secheresse": round(indice_secheresse, 1),
            "niveau_risque": niveau_risque,
            "surface_m2": surface,
            "duree_intervention_min": duree,
            "detection_automatique": detection_auto,
            "alerte_preventive": alerte_preventive,
            "victimes": random.choices([0, 1, 2, 3], weights=[88, 8, 3, 1], k=1)[0],
            "degats_estimes_eur": int(surface * random.randint(80, 350) * gravite),
        })

    df = pd.DataFrame(records)
    df = df.sort_values("date_heure").reset_index(drop=True)
    return df


def main():
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = generate_incidents(2500)
    df.to_csv(DATASET_PATH, index=False, encoding="utf-8")
    print(f"Dataset généré : {len(df)} incidents -> {DATASET_PATH}")


if __name__ == "__main__":
    main()
