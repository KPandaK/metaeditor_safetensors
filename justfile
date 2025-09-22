set dotenv-filename := ".env.development"
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Variables

# Use poetry for Python commands
python := "poetry run python"
rcc := "poetry run pyside6-rcc"

rcc_input_path := env("RCC_INPUT_PATH")
rcc_output_path := env("RCC_OUTPUT_PATH")

default: run

# Install dependencies
install: _install

# Update dependencies
update:
    @poetry update

# Compile Qt resources
compile-resources: _compile-resources

# Compile Qt resources (alias for compatibility)
compile: _compile-resources

# Format code with Ruff
fmt *ARGS:
    @echo "Formatting code with Ruff..."
    @{{ python }} -m ruff format {{ ARGS }} .

# Lint code with Ruff
lint:
    @echo "Linting code with Ruff..."
    @poetry run ruff check --fix .

# Type checking with mypy
mypy:
    @echo "Running mypy type checks..."
    @poetry run mypy .

# Security checks with Bandit
bandit:
    @echo "Running bandit security checks..."
    @poetry run bandit -r metaeditor_safetensors/ -ll

# Run unit tests with coverage
test:
    @echo "Running unit tests with pytest and coverage..."
    @poetry run pytest --cov=metaeditor_safetensors --cov-report=term-missing -v --tb=short

# Run the MetaEditor application
run: compile
    poetry run python main.py

# Run presubmit checks (format, lint, mypy, test)
presub:
    @just fmt
    @just lint
    @just mypy
    @just test
    @echo "✅ All presubmit checks passed!"

# ============================================================================
# Platform specific recipe implementations
# ============================================================================

_compile-resources:
    @just file-exists {{ rcc_input_path }}
    @just file-exists {{ rcc_output_path }}
    @echo "Compiling {{ file_name(rcc_input_path) }} -> {{ file_name(rcc_output_path) }}"
    @{{ rcc }} {{ rcc_input_path }} -o {{ rcc_output_path }}

[windows]
_install:
    @Write-Host "Installing dependencies with Poetry..."
    @poetry install --with dev

[linux]
[macos]
_install:
    @echo "Installing dependencies with Poetry..."
    @poetry install --with dev

# ============================================================================
# Utility Recipes
# ============================================================================

[private]
[windows]
file-exists FILE_PATH:
    @if (!(Test-Path "{{ FILE_PATH }}" -PathType Leaf)) { \
        Write-Host "❌ Error: {{ FILE_PATH }} not found!" -ForegroundColor Red; \
        exit 1; \
    }

[private]
[unix]
file-exists FILE_PATH:
    @if [ ! -f "{{ FILE_PATH }}" ]; then \
        echo "❌ Error: {{ FILE_PATH }} not found!"; \
        exit 1; \
    fi

[private]
[windows]
directory-exists DIR_PATH:
    @if (!(Test-Path "{{ DIR_PATH }}" -PathType Container)) { \
        Write-Host "❌ Error: Directory {{ DIR_PATH }} not found!" -ForegroundColor Red; \
        exit 1; \
    }

[private]
[unix]
directory-exists DIR_PATH:
    @if [ ! -d "{{ DIR_PATH }}" ]; then \
        echo "❌ Error: Directory {{ DIR_PATH }} not found!"; \
        exit 1; \
    fi
