#!/bin/bash

# DCF Calculator - Streamlit Run Script
# Finance Club Portfolio Analysis Tool

echo "Starting DCF Calculator..."

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Set Python path for imports
export PYTHONPATH=.

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit not found. Installing..."
    pip install streamlit
fi

# Run the Streamlit app
echo "Launching DCF Calculator interface..."
echo "Access at: http://localhost:8504"
echo "Press Ctrl+C to stop"

streamlit run main.py --server.port 8504 --server.headless true