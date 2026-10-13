from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import API_HOST, API_PORT
from data_store import DataStore
from ml_model import FireRiskModel
from pdf_export import history_pdf, prediction_pdf

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="FireGuard Lyon - API Détection Incendies",
    description="Tableau de bord ML pour la détection et prédiction des incendies à Lyon",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = DataStore()
model = FireRiskModel()


class PredictionRequest(BaseModel):
    quartier: str
    type_incendie: str
    origine: str
    mois: int = Field(ge=1, le=12)
    jour_semaine: int = Field(ge=0, le=6)
    heure: int = Field(ge=0, le=23)
    temperature_c: float
    humidite_pct: float
    vent_vitesse_kmh: float
    indice_secheresse: float
    surface_m2: float = 50
    duree_intervention_min: float = 30


@app.on_event("startup")
def startup():
    store.ensure_indexes()
    try:
        model.load()
    except FileNotFoundError:
        pass


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "mongodb": store.ping(),
        "data_mode": store.mode(),
        "model_loaded": model.pipeline is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/stats")
def get_stats():
    return store.get_stats()


@app.get("/api/incidents")
def get_incidents(
    limit: int = Query(50, ge=1, le=500),
    quartier: str | None = None,
    niveau_risque: str | None = None,
    type_incendie: str | None = None,
):
    incidents = store.get_incidents(limit, quartier, niveau_risque, type_incendie)
    return {"count": len(incidents), "incidents": incidents}


@app.get("/api/trends/monthly")
def monthly_trends():
    return store.get_monthly_trend()


@app.get("/api/heatmap")
def heatmap():
    return store.get_heatmap_data()


@app.get("/api/quartiers")
def quartiers():
    return store.get_quartiers()


@app.get("/api/hourly-distribution")
def hourly_distribution():
    return store.get_hourly_distribution()


@app.get("/api/ml/metrics")
def ml_metrics():
    if model.pipeline is None:
        try:
            model.load()
        except FileNotFoundError:
            raise HTTPException(404, "Modèle non entraîné")
    return model.metrics


@app.post("/api/ml/predict")
def predict(request: PredictionRequest):
    if model.pipeline is None:
        try:
            model.load()
        except FileNotFoundError:
            raise HTTPException(404, "Modèle non entraîné. Lancez train_model.py")

    result = model.predict(request.model_dump())
    result["timestamp"] = datetime.now().isoformat()
    record = store.save_prediction({**request.model_dump(), **result})
    return record


@app.get("/api/ml/history")
def prediction_history(limit: int = Query(50, ge=1, le=200)):
    predictions = store.get_predictions(limit)
    return {"count": len(predictions), "predictions": predictions}


@app.get("/api/ml/export/all/pdf")
def export_all_predictions_pdf():
    predictions = store.get_predictions(200)
    if not predictions:
        raise HTTPException(404, "Aucune analyse à exporter")
    content = history_pdf(predictions)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="fireguard_historique.pdf"'},
    )


@app.get("/api/ml/export/{prediction_id}/pdf")
def export_prediction_pdf(prediction_id: str):
    predictions = store.get_predictions(500)
    pred = next((p for p in predictions if p.get("id") == prediction_id), None)
    if not pred:
        raise HTTPException(404, "Analyse introuvable")
    content = prediction_pdf(pred)
    filename = f"fireguard_{prediction_id}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/ml/feature-importance")
def feature_importance():
    if model.pipeline is None:
        try:
            model.load()
        except FileNotFoundError:
            raise HTTPException(404, "Modèle non entraîné")
    return model.metrics.get("feature_importance", [])


@app.get("/")
def serve_dashboard():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Dashboard non trouvé. Vérifiez le dossier frontend/"}


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=False)
