# Run React + Vite Frontend
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting AI Incident Investigator Frontend (Vite React)  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"

Set-Location $FrontendDir

Write-Host "Frontend directory: $FrontendDir" -ForegroundColor Gray
Write-Host "Starting Vite development server on http://localhost:5173..." -ForegroundColor Green

npm run dev
