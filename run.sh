#!/bin/bash
set -e

# Run MetaEditor SafeTensors using packaged Python environment
if [ -f "venv/bin/python" ]; then
    venv/bin/python main.py "$@"
else
    echo "ERROR: Packaged Python not found in venv/bin/python"
    echo "Please ensure you have unzipped the full package and venv is present."
    exit 1
fi
