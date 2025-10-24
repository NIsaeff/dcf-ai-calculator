#!/bin/bash

# DCF Calculator - Dash Run Script
# Finance Club Portfolio Analysis Tool

echo "Starting DCF Calculator (Dash version)..."

# Change to project directory
cd "$(dirname "$0")"

# Ensure dependencies are installed
echo "Syncing dependencies with UV..."
uv sync

# Set Python path for imports
export PYTHONPATH=.

# Run the Dash app using UV
echo "Launching DCF Calculator (Dash)..."
echo "Access at: http://localhost:8508"
echo "Press Ctrl+C to stop"
echo ""

uv run python app.py
