"""
FireGuard Lyon — Lanceur automatique.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / "venv"
VENV_PY = VENV_DIR / "Scripts" / "python.exe"
BACKEND = ROOT / "backend"
REQUIREMENTS = ROOT / "requirements.txt"
DATASET = ROOT / "data" / "incendies_lyon.csv"
MODEL = ROOT / "models" / "fire_risk_model.joblib"
URL = "http://localhost:8000"


def log(msg: str) -> None:
    print(f"[FireGuard] {msg}")


def run(cmd: list[str], cwd: Path | None = None, optional: bool = False) -> bool:
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0 and not optional:
        sys.exit(result.returncode)
    return result.returncode == 0


def ensure_venv() -> Path:
    if VENV_PY.exists():
        return VENV_PY
    log("Création de l'environnement virtuel...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])
    return VENV_PY


def ensure_dependencies(py: Path) -> None:
    for module in ("fastapi", "fpdf"):
        check = subprocess.run([str(py), "-c", f"import {module}"], capture_output=True)
        if check.returncode != 0:
            log("Installation des dépendances...")
            run([str(py), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
            return


def ensure_dataset(py: Path) -> None:
    if not DATASET.exists():
        log("Génération du dataset...")
        run([str(py), "generate_dataset.py"], cwd=BACKEND)


def ensure_model(py: Path) -> None:
    if not MODEL.exists():
        log("Entraînement du modèle ML...")
        run([str(py), "train_model.py"], cwd=BACKEND)


def try_seed_mongodb(py: Path) -> None:
    run([str(py), "seed_mongodb.py"], cwd=BACKEND, optional=True)


def server_ready() -> bool:
    try:
        with urlopen(f"{URL}/api/health", timeout=2) as response:
            return response.status == 200
    except (URLError, TimeoutError, OSError):
        return False


def stop_existing_servers() -> None:
    if os.name != "nt":
        return
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, check=False,
        )
        pids = set()
        for line in result.stdout.splitlines():
            if ":8000" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    pids.add(parts[-1])
        for proc_id in pids:
            subprocess.run(["taskkill", "/F", "/PID", proc_id], capture_output=True)
        if pids:
            log(f"Ancien serveur arrêté (port 8000)")
            time.sleep(1)
    except Exception:
        pass


def start_server(py: Path) -> subprocess.Popen | None:
    stop_existing_servers()
    log("Démarrage du serveur...")
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen([str(py), "app.py"], cwd=BACKEND, creationflags=flags)
    for _ in range(30):
        if server_ready():
            log("Serveur prêt.")
            return process
        time.sleep(1)
    log("Serveur en cours de démarrage...")
    return process


def main() -> None:
    print("=" * 50)
    print("  FireGuard Lyon — Lancement automatique")
    print("=" * 50)
    py = ensure_venv()
    ensure_dependencies(py)
    ensure_dataset(py)
    ensure_model(py)
    try_seed_mongodb(py)
    process = start_server(py)
    log(f"Ouverture du dashboard : {URL}")
    webbrowser.open(URL)
    print(f"\n  Dashboard : {URL}")
    print("  Ctrl+C pour arrêter\n" + "=" * 50)
    if process:
        try:
            process.wait()
        except KeyboardInterrupt:
            process.terminate()


if __name__ == "__main__":
    main()
