# Backend verification only. Run from repo root: .\scripts\verify-backend.ps1
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

Write-Host "== Backend: install =="
Set-Location (Join-Path $Root "backend")
python -m pip install -q -r requirements.txt
Invoke-CheckLastExit "pip install requirements.txt"
python -m pip install -q -r requirements-tools.txt
Invoke-CheckLastExit "pip install requirements-tools.txt"

Write-Host "== Backend: Ruff =="
python -m ruff check app tests
Invoke-CheckLastExit "ruff"

Write-Host "== Backend: Mypy (core) =="
python -m mypy
Invoke-CheckLastExit "mypy"

Write-Host "== Backend: Pytest =="
python -m pytest tests -q --tb=short
Invoke-CheckLastExit "pytest"

Write-Host "== Backend verification passed =="
