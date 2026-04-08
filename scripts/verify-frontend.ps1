# Frontend + Playwright full-stack E2E. Run from repo root: .\scripts\verify-frontend.ps1
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if (-not $env:SECRET_KEY) {
    $env:SECRET_KEY = "ci-test-secret-key-must-be-32chars-minimum"
}

function Invoke-CheckLastExit {
    param([string]$Step)
    if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        Write-Error "$Step failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

Write-Host "== Backend deps for E2E (uvicorn) =="
Set-Location (Join-Path $Root "backend")
python -m pip install -q -r requirements.txt
Invoke-CheckLastExit "pip install (backend for E2E)"

Write-Host "== Frontend: install =="
Set-Location (Join-Path $Root "frontend")
npm ci
Invoke-CheckLastExit "npm ci"

Write-Host "== Frontend: ESLint =="
npm run lint
Invoke-CheckLastExit "npm run lint"

Write-Host "== Frontend: Jest =="
npm test -- --ci --passWithNoTests
Invoke-CheckLastExit "npm test"

Write-Host "== Frontend: production build =="
npm run build
Invoke-CheckLastExit "npm run build"

Write-Host "== Frontend: Playwright + full-stack E2E =="
npx playwright install --with-deps chromium
Invoke-CheckLastExit "playwright install"
if (-not $env:CI) { $env:CI = "" }
npm run test:e2e:full
Invoke-CheckLastExit "npm run test:e2e:full"

Write-Host "== Frontend verification passed =="
