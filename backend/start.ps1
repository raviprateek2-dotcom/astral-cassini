# PRO HR Backend Startup Script
# Loads .env into the OS environment then starts uvicorn so child processes inherit all vars

Write-Host "Loading .env into environment..." -ForegroundColor Cyan

Get-Content ".env" | Where-Object { 
    $_.Trim() -ne "" -and 
    -not $_.StartsWith("#") -and 
    $_ -match "^[A-Za-z_][A-Za-z0-9_]*="
} | ForEach-Object {
    $parts = $_ -split "=", 2
    $key = $parts[0].Trim()
    $value = $parts[1].Trim()
    [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
}

Write-Host "Environment loaded. SECRET_KEY present: $([bool]$env:SECRET_KEY)" -ForegroundColor Green
Write-Host "Starting uvicorn on port 8000..." -ForegroundColor Cyan

py -3.11 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
