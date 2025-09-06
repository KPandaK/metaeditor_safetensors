set dotenv-filename := ".env.development"
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Variables

python := if os_family() == "windows" { "./venv/Scripts/python.exe" } else { "./venv/bin/python" }
rcc := if os_family() == "windows" { require("pyside6-rcc.exe") } else { require("pyside6-rcc") }
uic := if os_family() == "windows" { require("pyside6-uic.exe") } else { require("pyside6-uic") }

rcc_input_path := env("RCC_INPUT_PATH")
rcc_output_path := env("RCC_OUTPUT_PATH")
uic_input_dir := env("UIC_INPUT_DIR")
uic_output_dir := env("UIC_OUTPUT_DIR")

default: run

# Install dependencies
install:
    {{ python }} -m pip install --upgrade pip
    {{ python }} -m pip install -e .[dev]

# Compile Qt resources
compile-resources: _compile-resources

# Compiles Qt ui files
compile-ui: _compile-ui

# Compile all Qt files
compile: _compile-resources && _compile-ui

# Format code with Ruff
fmt:
    @echo "Formatting code with Ruff..."
    @{{ python }} -m ruff format --check --diff .

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

# Run unit tests
test:
    @echo "Running unit tests..."
    @{{ python }} -m coverage run -m unittest discover tests -v


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

[windows]
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
