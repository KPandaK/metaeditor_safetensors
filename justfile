set dotenv-filename := ".env.development"
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Variables

# Use python from PATH (works in both venv and CI)
python := "python"
rcc := "pyside6-rcc"
uic := "pyside6-uic"

rcc_input_path := env("RCC_INPUT_PATH")
rcc_output_path := env("RCC_OUTPUT_PATH")
uic_input_dir := env("UIC_INPUT_DIR")
uic_output_dir := env("UIC_OUTPUT_DIR")

default: run

# Install dependencies
install: _install

# Compile Qt resources
compile-resources: _compile-resources

# Compiles Qt ui files
compile-ui: _compile-ui

# Compile all Qt files
compile:
    @just _compile-resources
    @just _compile-ui

# Format code with Ruff
fmt *ARGS:
    @echo "Formatting code with Ruff..."
    @{{ python }} -m ruff format {{ ARGS }} .

# Lint code with Ruff
lint:
    @echo "Linting code with Ruff..."
    @{{ python }} -m ruff check --fix .

# Type checking with mypy
mypy:
    @echo "Running mypy type checks..."
    @{{ python }} -m mypy .

# Security checks with Bandit
bandit:
    @echo "Running bandit security checks..."
    @{{ python }} -m bandit -r metaeditor_safetensors/ -ll

# Run unit tests with coverage
test:
    @echo "Running unit tests with pytest and coverage..."
    @{{ python }} -m pytest --cov=metaeditor_safetensors --cov-report=term-missing -v --tb=short

# Run the MetaEditor application
run: compile
    {{ python }} main.py

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
_compile-ui:
    @just directory-exists {{ uic_input_dir }}
    @just directory-exists {{ uic_output_dir }}
    @Get-ChildItem -Path {{ uic_input_dir }} -Filter "*.ui" | ForEach-Object { \
        $output_file = "{{ uic_output_dir }}/$($_.BaseName)_ui.py"; \
        Write-Host "Compiling $($_.Name) -> $($_.BaseName)_ui.py"; \
        & {{ uic }} --from-imports $_.FullName -o $output_file \
    }

[linux]
[macos]
_compile-ui:
    @just directory-exists {{ uic_input_dir }}
    @just directory-exists {{ uic_output_dir }}
    @for ui_file in {{ uic_input_dir }}/*.ui; do \
        base_name=$$(basename $$ui_file .ui); \
        output_file="{{ uic_output_dir }}/$${base_name}_ui.py"; \
        echo "Compiling $$(basename $$ui_file) -> $$(base_name)_ui.py"; \
        {{ uic }} --from-imports $$ui_file -o $$output_file; \
    done

[windows]
_install:
    @if (Test-Path "./venv/") { \
        Write-Host "Virtual environment already exists. Skipping creation." -ForegroundColor Yellow; \
    } else { \
        Write-Host "Creating virtual environment..."; \
        & {{ python }} -m venv venv; \
        Write-Host "Installing dependencies from requirements.txt..."; \
        & {{ python }} -m pip install --upgrade pip; \
    }

    @{{ python }} -m pip install -e .[dev]

[linux]
[macos]
_install:
    @if [ -d "./venv/" ]; then \
        echo "Virtual environment already exists. Skipping creation."; \
    else \
        echo "Creating virtual environment..."; \
        {{ python }} -m venv venv; \
        echo "Installing dependencies from requirements.txt..."; \
        {{ python }} -m pip install --upgrade pip; \
    fi

    @{{ python }} -m pip install -e .[dev]

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
