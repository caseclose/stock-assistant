# One-time setup for Windows (PowerShell 5.1+).
# Usage: .\scripts\windows\setup.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")

function Require-Command($Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

Require-Command python
Require-Command npm

$pyVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pyVersion -lt [version]"3.11" -or [version]$pyVersion -ge [version]"3.13") {
    throw "Python 3.11 or 3.12 required (found $pyVersion)"
}

$envFile = Join-Path $Root ".env"
$envExample = Join-Path $Root ".env.example"
if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "Created .env from .env.example — add your Alpaca keys before running."
}

$backend = Join-Path $Root "backend"
$venvPython = Join-Path $backend ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Push-Location $backend
    python -m venv .venv
    Pop-Location
}

Push-Location $backend
& $venvPython -m pip install -e ".[dev]"
Pop-Location

Push-Location (Join-Path $Root "frontend")
npm install
Pop-Location

Write-Host ""
Write-Host "Setup complete."
Write-Host "  Backend:  .\scripts\windows\dev-backend.ps1"
Write-Host "  Frontend: .\scripts\windows\dev-frontend.ps1"
Write-Host "  Tests:    .\scripts\windows\test.ps1"
