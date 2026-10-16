# 🔥 FireGuard Lyon — Détection et prédiction des risques d'incendie

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-optionnel-47A248?logo=mongodb&logoColor=white)

Tableau de bord interactif qui analyse les incendies survenus à **Lyon** et prédit le **niveau de risque** d'un nouvel incident grâce à un modèle de Machine Learning.

---

## 📋 Sommaire

- [Aperçu](#-aperçu)
- [Fonctionnalités](#-fonctionnalités)
- [Technologies](#-technologies)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [API](#-api)
- [Auteur](#-auteur)

## 🎯 Aperçu

Le projet combine :

- un **jeu de données de 2 500 incendies** à Lyon (2022‑2024) : quartier, coordonnées GPS, type d'incendie, météo (température, humidité, vent, indice de sécheresse), surface, durée d'intervention, dégâts estimés…
- un **modèle d'ensemble** (*Random Forest* + *Gradient Boosting* via un `VotingClassifier`) qui classe le niveau de risque, avec **~81 % de précision** ;
- un **dashboard web** avec graphiques, carte de chaleur et formulaire de prédiction.

## ✨ Fonctionnalités

- 📊 Statistiques globales et tendances mensuelles
- 🗺️ Carte de chaleur et répartition par quartier
- 🕒 Distribution horaire des incendies
- 🤖 Prédiction du niveau de risque par le modèle ML
- 📈 Métriques du modèle et importance des variables
- 🗂️ Historique des analyses avec **export PDF, CSV et JSON**
- 💾 Fonctionne avec **MongoDB** ou, à défaut, en **mode CSV** automatique

## 🛠️ Technologies

| Couche | Outils |
|---|---|
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Machine Learning | scikit-learn, pandas, NumPy, joblib |
| Base de données | MongoDB (PyMongo) — optionnel |
| Export | fpdf2 |
| Frontend | HTML, CSS, JavaScript |

## 🏗️ Architecture

```
fireguard-lyon/
├── backend/
│   ├── app.py               # API FastAPI
│   ├── ml_model.py          # Modèle de prédiction
│   ├── train_model.py       # Entraînement du modèle
│   ├── generate_dataset.py  # Génération du jeu de données
│   ├── database.py          # Connexion MongoDB
│   ├── data_store.py        # Accès aux données (MongoDB ou CSV)
│   └── pdf_export.py        # Export PDF
├── frontend/                # Dashboard (HTML / CSS / JS)
├── data/                    # Dataset + historique des prédictions
├── models/                  # Modèle entraîné (.joblib)
├── launch.py                # Lanceur automatique
└── LANCER.bat               # Lancement par double-clic (Windows)
```

## 🚀 Installation

**Prérequis :** Python 3.10+ (MongoDB facultatif)

```bash
git clone https://github.com/AyaElouajjite/fireguard-lyon.git
cd fireguard-lyon

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
cp .env.example .env         # optionnel : configuration MongoDB

python launch.py
```

Sous Windows, vous pouvez aussi double-cliquer sur **`LANCER.bat`**.

Le dashboard est disponible sur **http://localhost:8000**.

## 🔌 API

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/stats` | Statistiques globales |
| GET | `/api/incidents` | Liste des incidents |
| GET | `/api/trends/monthly` | Tendances mensuelles |
| GET | `/api/heatmap` | Données de la carte de chaleur |
| GET | `/api/quartiers` | Statistiques par quartier |
| GET | `/api/hourly-distribution` | Répartition horaire |
| GET | `/api/ml/metrics` | Métriques du modèle |
| POST | `/api/ml/predict` | Prédiction du niveau de risque |
| GET | `/api/ml/history` | Historique des prédictions |
| GET | `/api/ml/feature-importance` | Importance des variables |
| GET | `/api/ml/export/all/pdf` | Export PDF de l'historique |

La documentation interactive Swagger est disponible sur `http://localhost:8000/docs`.

## 👩‍💻 Auteur

**Aya Elouajjite** — [@AyaElouajjite](https://github.com/AyaElouajjite)
