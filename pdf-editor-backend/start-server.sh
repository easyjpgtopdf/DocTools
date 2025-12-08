#!/bin/bash
# PDF Editor Backend Server Startup Script
# Linux/Mac script to start the FastAPI backend server

echo "========================================"
echo "PDF Editor Backend Server"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "app/main.py" ]; then
    echo "ERROR: Please run this script from pdf-editor-backend directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Set environment variables
export PORT=8080
export API_BASE_URL=https://easyjpgtopdf.com

echo ""
echo "Starting server on http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

