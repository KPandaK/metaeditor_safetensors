#!/bin/bash
# Pre-submission script for metaeditor_safetensors
# Runs all quality checks, formatting, and tests before submitting code

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default options
FIX=false
SKIP_SECURITY=false
SKIP_TESTS=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --fix           Automatically fix issues where possible"
            echo "  --skip-security Skip security scanning"
            echo "  --skip-tests    Skip running tests"
            echo "  --verbose       Verbose test output"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

function print_status() {
    echo -e "${CYAN}==> $1${NC}"
}

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

function command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Change to project root (script directory parent)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

print_status "Starting pre-submission checks for metaeditor_safetensors"
echo ""

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "Virtual environment not detected. Attempting to activate..."
    if [[ -f "venv/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [[ -f "venv/Scripts/activate" ]]; then
        # Windows Git Bash
        # shellcheck disable=SC1091
        source venv/Scripts/activate
        print_success "Virtual environment activated"
    else
        print_error "No virtual environment found. Please create and activate a virtual environment first."
        exit 1
    fi
fi

EXIT_CODE=0

# Step 1: Code Formatting and Quality
print_status "1. Running code formatting and quality checks"

if $FIX; then
    print_status "  Fixing formatting issues with Ruff..."
    if python -m ruff check --fix . --unsafe-fixes; then
        print_success "  Code formatting fixed"
    else
        print_error "  Code formatting fix failed"
        EXIT_CODE=1
    fi
else
    print_status "  Checking code formatting with Ruff..."
    if python -m ruff check . --output-format=github; then
        print_success "  Code formatting is clean"
    else
        print_error "  Code formatting issues found. Run with --fix to automatically fix them."
        EXIT_CODE=1
    fi
fi

# Step 2: Type Checking
print_status "2. Running type checks"

print_status "  Checking types with mypy..."
if python -m mypy metaeditor_safetensors/ --show-error-codes --no-error-summary; then
    print_success "  Type checking passed"
else
    print_error "  Type checking failed"
    EXIT_CODE=1
fi

# Step 3: Security Scanning
if ! $SKIP_SECURITY; then
    print_status "3. Running security scans"
    
    # Bandit security scan
    print_status "  Scanning for security issues with Bandit..."
    if python -m bandit -r metaeditor_safetensors/ --severity-level medium --confidence-level medium; then
        print_success "  No security issues found"
    else
        print_error "  Security issues found"
        EXIT_CODE=1
    fi
    
    # pip-audit dependency scan
    print_status "  Scanning dependencies with pip-audit..."
    if python -m pip_audit --progress-spinner=off; then
        print_success "  No vulnerable dependencies found"
    else
        print_error "  Vulnerable dependencies found"
        EXIT_CODE=1
    fi
else
    print_status "3. Security scanning skipped"
fi

# Step 4: Tests
if ! $SKIP_TESTS; then
    print_status "4. Running tests"
    
    print_status "  Running unit tests..."
    if $VERBOSE; then
        TEST_CMD="python -m unittest discover tests -v"
    else
        TEST_CMD="python -m unittest discover tests"
    fi
    
    if $TEST_CMD; then
        print_success "  All tests passed"
    else
        print_error "  Tests failed"
        EXIT_CODE=1
    fi
    
    # Coverage report (optional)
    if command_exists coverage; then
        print_status "  Generating coverage report..."
        coverage run -m unittest discover tests
        coverage report --show-missing --skip-covered
        print_success "  Coverage report generated"
    fi
else
    print_status "4. Tests skipped"
fi

# Summary
echo ""
print_status "Pre-submission check summary"

if [[ $EXIT_CODE -eq 0 ]]; then
    print_success "All checks passed! Code is ready for submission."
    echo ""
    print_status "Next steps:"
    echo "  1. Review your changes: git diff"
    echo "  2. Stage your changes: git add ."
    echo "  3. Commit your changes: git commit -m 'Your message'"
    echo "  4. Push your changes: git push"
else
    print_error "Some checks failed. Please fix the issues before submitting."
    echo ""
    print_status "Common fixes:"
    echo "  • Run with --fix to automatically fix formatting"
    echo "  • Check type hints in flagged files"  
    echo "  • Review and fix failing tests"
    echo "  • Address security findings if any"
fi

exit $EXIT_CODE
