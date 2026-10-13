# FireGuard Lyon - Lanceur PowerShell
Set-Location $PSScriptRoot
if (Test-Path "venv\Scripts\python.exe") {
    & "venv\Scripts\python.exe" launch.py
} else {
    python launch.py
}
