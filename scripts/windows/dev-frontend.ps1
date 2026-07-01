# Start Next.js frontend on http://localhost:3000
# Usage: .\scripts\windows\dev-frontend.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$frontend = Join-Path $Root "frontend"

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    throw "node_modules missing. Run .\scripts\windows\setup.ps1 first."
}

Push-Location $frontend
npm run dev -- --hostname 0.0.0.0 --port 3000
