# Full project: verify-backend + verify-frontend
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "verify-backend.ps1")
& (Join-Path $PSScriptRoot "verify-frontend.ps1")
Write-Host "== All verification steps passed =="
