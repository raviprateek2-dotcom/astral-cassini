# Backend verification only. Run from repo root: .\scripts\verify-backend.ps1
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonCmd = @("py", "-3.11")

try {
    & $PythonCmd[0] $PythonCmd[1] --version | Out-Null
} catch {
    Write-Error "Python 3.11 is required. Install Python 3.11 and re-run this script."
    exit 1
}

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

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & $PythonCmd[0] $PythonCmd[1] @Args
}

Write-Host "== Backend: install =="
Set-Location (Join-Path $Root "backend")
Invoke-Python -m pip install -q -r requirements.txt
Invoke-CheckLastExit "pip install requirements.txt"
Invoke-Python -m pip install -q -r requirements-tools.txt
Invoke-CheckLastExit "pip install requirements-tools.txt"

Write-Host "== Backend: Ruff =="
Invoke-Python -m ruff check app tests
Invoke-CheckLastExit "ruff"

Write-Host "== Backend: Mypy (core) =="
Invoke-Python -m mypy
Invoke-CheckLastExit "mypy"

Write-Host "== Backend: Alembic upgrade head =="
Invoke-Python -m alembic -c alembic.ini upgrade head
Invoke-CheckLastExit "alembic upgrade head"

Write-Host "== Backend: Pytest =="
Invoke-Python -m pytest tests -q --tb=short
Invoke-CheckLastExit "pytest"

Write-Host "== Backend verification passed =="
