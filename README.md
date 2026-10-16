# FireGuard Lyon — Détection et prédiction des risques d'incendie

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white)

Application d'analyse de données et de Machine Learning qui étudie les incendies survenus à Lyon entre 2022 et 2024 et prédit le niveau de risque d'un nouvel incident. Les résultats sont présentés dans un tableau de bord web alimenté par une API REST.

## Sommaire

- [Présentation](#présentation)
- [Fonctionnalités](#fonctionnalités)
- [Points techniques](#points-techniques)
- [Stack technique](#stack-technique)
- [Architecture](#architecture)
- [Installation](#installation)
- [API](#api)
- [Contact](#contact)

## Présentation

Le projet couvre l'ensemble de la chaîne de traitement de la donnée :

- **Données** : jeu de 2 500 incidents décrits par 24 variables (quartier, coordonnées GPS, type et origine de l'incendie, conditions météorologiques, indice de sécheresse, surface touchée, durée d'intervention, dégâts estimés).
- **Modélisation** : classification du niveau de risque par un modèle d'ensemble atteignant environ **81 % de précision**.
- **Restitution** : tableau de bord interactif avec indicateurs, cartographie, prédiction et rapports exportables.

## Fonctionnalités

- Indicateurs globaux et tendances mensuelles
- Carte de chaleur et analyse par quartier
- Distribution horaire des incendies
- Prédiction du niveau de risque à partir d'un formulaire
- Métriques du modèle et importance des variables
- Historique des analyses avec export PDF, CSV et JSON
- Bascule automatique sur un stockage CSV lorsque MongoDB n'est pas disponible

## Points techniques

- Modèle d'ensemble `VotingClassifier` combinant **Random Forest** et **Gradient Boosting**, avec encodage des variables catégorielles et persistance via `joblib`
- API REST développée avec **FastAPI** et validation des données avec **Pydantic**
- Couche d'accès aux données abstraite permettant d'utiliser MongoDB ou des fichiers CSV sans modifier le reste de l'application
- Génération de rapports PDF côté serveur avec **fpdf2**
- Script de lancement automatisé (installation, démarrage du serveur, ouverture du navigateur)

## Stack technique

| Domaine | Technologies |
|---|---|
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Machine Learning | scikit-learn, pandas, NumPy, joblib |
| Base de données | MongoDB (PyMongo), CSV en mode dégradé |
| Reporting | fpdf2 |
| Frontend | HTML, CSS, JavaScript |

## Architecture

```
fireguard-lyon/
├── backend/
│   ├── app.py               # API FastAPI
│   ├── ml_model.py          # Modèle de prédiction
│   ├── train_model.py       # Entraînement du modèle
│   ├── generate_dataset.py  # Génération du jeu de données
│   ├── database.py          # Connexion MongoDB
│   ├── data_store.py        # Accès aux données (MongoDB ou CSV)
│   └── pdf_export.py        # Génération des rapports PDF
├── frontend/                # Tableau de bord (HTML, CSS, JavaScript)
├── data/                    # Jeu de données et historique des prédictions
├── models/                  # Modèle entraîné
├── launch.py                # Lanceur automatique
└── LANCER.bat               # Lancement sous Windows
```

## Installation

**Prérequis :** Python 3.10 ou supérieur. MongoDB est facultatif.

```bash
git clone https://github.com/AyaElouajjite/fireguard-lyon.git
cd fireguard-lyon

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
cp .env.example .env         # facultatif : configuration MongoDB

python launch.py
```

Sous Windows, le fichier `LANCER.bat` effectue les mêmes étapes.

Le tableau de bord est accessible sur `http://localhost:8000` et la documentation Swagger de l'API sur `http://localhost:8000/docs`.

## API

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/stats` | Indicateurs globaux |
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

## Contact

**Aya Elouajjite** — [github.com/AyaElouajjite](https://github.com/AyaElouajjite)
