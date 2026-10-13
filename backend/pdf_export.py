"""Génération PDF côté serveur pour les analyses ML."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from fpdf import FPDF


def _safe(text: Any) -> str:
    if text is None:
        return "-"
    s = str(text)
    return (
        s.replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ù", "u")
        .replace("ô", "o")
        .replace("î", "i")
        .replace("ç", "c")
        .replace("É", "E")
        .replace("È", "E")
        .replace("ê", "e")
        .replace("ë", "e")
        .replace("°", " deg")
    )


def _rows(pred: dict) -> list[tuple[str, str]]:
    proba = pred.get("probabilites") or {}
    return [
        ("ID", _safe(pred.get("id"))),
        ("Date", _safe(pred.get("timestamp"))),
        ("Quartier", _safe(pred.get("quartier"))),
        ("Type incendie", _safe(pred.get("type_incendie"))),
        ("Origine", _safe(pred.get("origine"))),
        ("Mois", _safe(pred.get("mois"))),
        ("Heure", f"{_safe(pred.get('heure'))} h"),
        ("Temperature", f"{_safe(pred.get('temperature_c'))} C"),
        ("Humidite", f"{_safe(pred.get('humidite_pct'))} %"),
        ("Vent", f"{_safe(pred.get('vent_vitesse_kmh'))} km/h"),
        ("Indice secheresse", _safe(pred.get("indice_secheresse"))),
        ("Risque predit", _safe(pred.get("niveau_risque_predit"))),
        ("Confiance", f"{float(pred.get('confiance', 0)) * 100:.1f} %"),
        ("Prob. Faible", f"{float(proba.get('Faible', 0)) * 100:.1f} %"),
        ("Prob. Modere", f"{float(proba.get('Modéré', proba.get('Modere', 0))) * 100:.1f} %"),
        ("Prob. Eleve", f"{float(proba.get('Élevé', proba.get('Eleve', 0))) * 100:.1f} %"),
    ]


def prediction_pdf(pred: dict) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(200, 60, 20)
    pdf.cell(0, 12, "FireGuard Lyon - Rapport d'analyse", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Prediction du risque d'incendie (Machine Learning)", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(255, 107, 53)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(90, 8, "Parametre", border=1, fill=True)
    pdf.cell(0, 8, "Valeur", border=1, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 30, 30)
    for i, (label, value) in enumerate(_rows(pred)):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(245, 245, 245)
        pdf.cell(90, 7, label, border=1, fill=fill)
        pdf.cell(0, 7, value, border=1, fill=fill, ln=True)

    return bytes(pdf.output())


def history_pdf(predictions: list[dict]) -> bytes:
    pdf = FPDF(orientation="L")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(200, 60, 20)
    pdf.cell(0, 10, "FireGuard Lyon - Historique des analyses ML", ln=True)
    pdf.ln(4)

    col_widths = [45, 40, 35, 35, 30, 25, 25]
    headers = ["ID", "Date", "Quartier", "Type", "Risque", "Confiance", "Origine"]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(255, 107, 53)
    pdf.set_text_color(255, 255, 255)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(30, 30, 30)
    for i, p in enumerate(predictions):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(245, 245, 245)
        row = [
            _safe(p.get("id")),
            _safe(p.get("timestamp", ""))[:16],
            _safe(p.get("quartier")),
            _safe(p.get("type_incendie")),
            _safe(p.get("niveau_risque_predit")),
            f"{float(p.get('confiance', 0)) * 100:.1f}%",
            _safe(p.get("origine")),
        ]
        for w, val in zip(col_widths, row):
            pdf.cell(w, 7, val[:28], border=1, fill=fill)
        pdf.ln()

    return bytes(pdf.output())
