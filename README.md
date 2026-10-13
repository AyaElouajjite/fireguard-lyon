# FireGuard Lyon — Détection des Incendies par Machine Learning

Tableau de bord pour la détection et prédiction des risques d'incendie à **Lyon**.

## Lancement

```powershell
cd c:\Users\SuperElectro\PFA_FIRE
python launch.py
```

Ou double-cliquez sur **`LANCER.bat`**.

Dashboard : **http://localhost:8000**

## Structure

```
PFA_FIRE/
├── backend/          API FastAPI, ML, MongoDB
├── frontend/         Dashboard animé
├── data/             Dataset + historique analyses
├── models/           Modèle ML entraîné
├── launch.py         Lanceur automatique
├── LANCER.bat        Double-clic Windows
└── setup.bat         Installation
```

## Fonctionnalités

- Dataset de 2 500 incendies à Lyon (2022-2024)
- Modèle ML : Random Forest + Gradient Boosting (~81% précision)
- Dashboard avec graphiques, carte, prédiction ML
- Historique des analyses avec export PDF/CSV/JSON

## MongoDB (optionnel)

Sans MongoDB, le projet fonctionne en mode CSV automatiquement.
