# Run FastAPI Backend Server
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting AI Incident Investigator Backend (FastAPI)     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"

Set-Location $BackendDir

Write-Host "Backend directory: $BackendDir" -ForegroundColor Gray
Write-Host "Starting Uvicorn server on http://127.0.0.1:8000..." -ForegroundColor Green
Write-Host "Swagger Documentation available at: http://127.0.0.1:8000/docs" -ForegroundColor Yellow

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
