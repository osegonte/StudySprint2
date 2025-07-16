#!/bin/bash

# StudySprint 2.0 - Development Setup Script

echo "🚀 Setting up StudySprint 2.0 development environment..."

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [[ $(echo "$python_version >= 3.11" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.11+ required. Current version: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

echo "✅ Development environment ready!"
echo ""
echo "To start development:"
echo "1. cd backend && source venv/bin/activate"
echo "2. uvicorn app.main:app --reload"
echo ""
echo "Or use Docker:"
echo "docker-compose up"
