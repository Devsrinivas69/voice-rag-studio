# HHGOA Voice RAG System Setup Script (Windows PowerShell)

Write-Host "=== HHGOA Voice RAG System Setup ===" -ForegroundColor Green

# 1. Check Python installation
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Error: Python is required but not installed." -ForegroundColor Red
    exit 1
}

# 2. Virtual environment setup
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment 'venv'..." -ForegroundColor Cyan
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

# 3. Environment configuration setup
if (-not (Test-Path "backend\.env")) {
    Write-Host "Copying backend\.env.example to backend\.env..." -ForegroundColor Cyan
    Copy-Item "backend\.env.example" "backend\.env"
}

if (-not (Test-Path ".env.local")) {
    Write-Host "Copying .env.example to .env.local..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env.local"
}

# 4. Frontend dependencies
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if ($npmCmd) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    npm install
}

Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host "Run backend tests: pytest backend/tests/"
Write-Host "Run backend dev server: uvicorn backend.app.main:app --reload"
Write-Host "Run frontend dev server: npm run dev"
