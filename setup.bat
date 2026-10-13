@echo off
echo ============================================
echo   FireGuard Lyon - Installation
echo ============================================
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [1/4] Creation du venv...
    python -m venv venv
)

echo [2/4] Installation des dependances...
"venv\Scripts\python.exe" -m pip install -r requirements.txt

echo [3/4] Dataset + MongoDB...
cd backend
"..\venv\Scripts\python.exe" generate_dataset.py
"..\venv\Scripts\python.exe" seed_mongodb.py

echo [4/4] Entrainement ML...
"..\venv\Scripts\python.exe" train_model.py
cd ..

echo Installation terminee ! Lancez LANCER.bat
pause
