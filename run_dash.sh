#!/bin/bash

# DCF Calculator - Dash Run Script
# Finance Club Portfolio Analysis Tool

echo "Starting DCF Calculator (Dash version)..."

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment not found. Creating..."
    python -m venv .venv
    source .venv/bin/activate
fi

# Set Python path for imports
export PYTHONPATH=.

# Check if Dash is installed
if ! python -c "import dash" 2>/dev/null; then
    echo "Dash not found. Installing dependencies..."
    uv add dash dash-bootstrap-components plotly gunicorn
fi

# Run the Dash app
echo "Launching DCF Calculator (Dash)..."
echo "Access at: http://localhost:8508"
echo "Press Ctrl+C to stop"
echo ""

python app.py
