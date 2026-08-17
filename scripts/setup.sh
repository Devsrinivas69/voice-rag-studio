#!/usr/bin/env bash
set -e

echo "=== HHGOA Voice RAG System Setup ==="

# 1. Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# 2. Set up Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment 'venv'..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing backend dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Environment variable files
if [ ! -f "backend/.env" ]; then
    echo "Copying backend/.env.example to backend/.env..."
    cp backend/.env.example backend/.env
fi

if [ ! -f ".env.local" ]; then
    echo "Copying .env.example to .env.local..."
    cp .env.example .env.local
fi

# 4. Install frontend npm dependencies
if command -v npm &> /dev/null; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "=== Setup complete! ==="
echo "Run backend tests: pytest backend/tests/"
echo "Run backend dev server: uvicorn backend.app.main:app --reload"
echo "Run frontend dev server: npm run dev"
