#!/bin/bash

echo "========================================="
echo "SearX Multi-Keyword Scraper API"
echo "========================================="
echo ""
echo "Starting FastAPI server with ProcessPoolExecutor..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created"
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "Installing Playwright browsers..."
playwright install chromium
echo "Dependencies installed"
echo ""

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ".env file created"
    echo ""
fi

# Run server
echo "Starting server on http://0.0.0.0:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000