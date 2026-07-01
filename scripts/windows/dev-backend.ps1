# Start FastAPI backend on http://localhost:8000
# Usage: .\scripts\windows\dev-backend.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$backend = Join-Path $Root "backend"
$activate = Join-Path $backend ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $activate)) {
    throw "Virtual env not found. Run .\scripts\windows\setup.ps1 first."
}

Push-Location $backend
. $activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
