# PRO HR Complete Testing Framework Execution Script
# Purpose: Run backend and frontend suites in sequence

$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "🚀 INITIALIZING PRO HR AUTOMATED TEST SUITE" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Backend Tests (pytest)
Write-Host "`n🧪 Step 1: Running Backend Unit, Integration, & API Tests..." -ForegroundColor Yellow
cd backend
python -m pytest tests/ --verbose --disable-warnings
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Backend tests failed. Aborting." -ForegroundColor Red
    exit $LASTEXITCODE
}
cd ..

# 2. Frontend Tests (Jest)
Write-Host "`n🖥️ Step 2: Running Frontend UI & Component Tests..." -ForegroundColor Yellow
cd frontend
npm test -- --watchAll=false
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Frontend tests failed. Aborting." -ForegroundColor Red
    exit $LASTEXITCODE
}
cd ..

Write-Host "`n====================================================" -ForegroundColor Green
Write-Host "✅ ALL SYSTEMS OPERATIONAL: Pipeline Validated" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
