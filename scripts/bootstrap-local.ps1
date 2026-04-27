$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

Write-Host "== PRO HR local bootstrap (Windows) =="
Write-Host "Root: $Root"

if (-not (Test-Path (Join-Path $BackendDir ".env"))) {
    Copy-Item (Join-Path $BackendDir ".env.example") (Join-Path $BackendDir ".env")
    Write-Host "Created backend/.env from .env.example"
} else {
    Write-Host "backend/.env already exists"
}

if (-not (Test-Path (Join-Path $FrontendDir ".env.local"))) {
    Copy-Item (Join-Path $FrontendDir ".env.example") (Join-Path $FrontendDir ".env.local")
    Write-Host "Created frontend/.env.local from .env.example"
} else {
    Write-Host "frontend/.env.local already exists"
}

Write-Host "== Backend dependencies =="
Set-Location $BackendDir
try {
    & py -3.11 -m pip install -r requirements.txt
} catch {
    Write-Warning "py -3.11 failed, trying python -m pip"
    & python -m pip install -r requirements.txt
}

Write-Host "== Frontend dependencies =="
Set-Location $FrontendDir
npm ci

Write-Host ""
Write-Host "Bootstrap complete."
Write-Host "Run backend:  cd backend;  py -3.11 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host "Run frontend: cd frontend; npm run dev -- -p 3000"
Write-Host "Open: http://localhost:3000"
