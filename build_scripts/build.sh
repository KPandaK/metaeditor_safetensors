#!/bin/bash
# Build script for creating standalone binary

set -e

echo "Building MetaEditor SafeTensors standalone binary..."

# Install development dependencies if not already installed
pip install -r requirements-dev.txt

# Clean previous builds
rm -rf dist/ build/

# Build with PyInstaller
pyinstaller build_scripts/build.spec

echo "Build complete! Binary located in dist/"

# Make executable on Unix systems
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    chmod +x dist/MetaEditor-SafeTensors
fi

echo "Standalone binary ready for distribution!"
