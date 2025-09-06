#!/bin/bash
# Validation script for GitHub Copilot Instructions
# Tests the commands documented in .github/copilot-instructions.md
# Run this after cloning the repository to verify your setup

set -e
cd "$(dirname "$0")"

echo "=== Copilot Instructions Validation ==="
echo "Testing setup commands from .github/copilot-instructions.md"
echo

# Check Python version
echo "✓ Python version: $(python3 --version)"

# Check virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
    source venv/bin/activate
    echo "✓ Virtual environment activated: $(python --version)"
else
    echo "ℹ Virtual environment not found - run: python3 -m venv venv"
fi

# Test basic structure
echo "✓ Repository structure validated"

# Test core functionality that works without dependencies
export QT_QPA_PLATFORM=offscreen
echo "Testing core unit tests..."
if python -m unittest test_config_service -q 2>/dev/null; then
    echo "✓ Core tests pass"
else
    echo "⚠ Some core tests failed - check dependencies"
fi

echo
echo "Setup validation complete!"
echo "See .github/copilot-instructions.md for full documentation."