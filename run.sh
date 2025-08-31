#!/bin/bash
set -e

echo "MetaEditor SafeTensors - Starting..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.10 or newer"
    exit 1
fi

# Check Python version (must be 3.10 or newer)
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Detected Python version: $PYTHON_VERSION"

# Parse major and minor version numbers
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ]; then
    echo "ERROR: Python version $PYTHON_VERSION is too old"
    echo "Please install Python 3.10 or newer"
    exit 1
fi

if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; then
    echo "ERROR: Python version $PYTHON_VERSION is too old"
    echo "Please install Python 3.10 or newer"
    exit 1
fi

echo "Python version check passed: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    echo "Installing dependencies..."
    venv/bin/pip install --upgrade pip
    venv/bin/pip install -r requirements.txt
fi

# Activate virtual environment and run
echo "Starting MetaEditor SafeTensors..."
source venv/bin/activate
cd src/metaeditor_safetensors
python main.py "$@"
