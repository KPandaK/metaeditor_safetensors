<div align="left">

[![CI](https://github.com/KPandaK/metaeditor_safetensors/actions/workflows/ci.yml/badge.svg)](https://github.com/KPandaK/metaeditor_safetensors/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/KPandaK/metaeditor_safetensors/python-coverage-comment-action-data/endpoint.json)](https://github.com/KPandaK/metaeditor_safetensors/tree/python-coverage-comment-action-data)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
</div>

# MetaEditor Safetensors

A lightweight Python tool and GUI for inspecting and editing `.safetensors` files, commonly used in AI and ML model storage.

## Features
- View and edit metadata in safetensors files
- Implements the [Stability AI ModelSpec](https://github.com/Stability-AI/ModelSpec) version 1.0.1 for standardized metadata.

## Installation

1. **Clone the repository:**
  ```sh
  git clone <your-repo-url>
  cd metaeditor_safetensors
  ```

2. **(Optional) Create a virtual environment:**
  ```sh
  python -m venv venv
  venv\Scripts\activate  # Windows
  ```

3. **Install dependencies:**
  ```sh
  pip install -r requirements.txt
  ```

## Usage
Run the main application:
```sh
python main.py
```

## Development Setup

Follow these steps to set up MetaEditor SafeTensors for development:

**Install Just task runner**  
  - **Windows:**  
    Run in terminal:  
    ```powershell
    winget install casey.just
    ```
  - **macOS/Linux:**  
    See [Just installation instructions](https://github.com/casey/just#installation).

**Install Python 3.10+**  
  - Download from [python.org](https://www.python.org/downloads/).
  - Make sure Python is added to your system PATH.
  - Verify in terminal:
    ```powershell
    python --version
    ```

**Install dependencies**  
  - In your project folder, run:
    ```powershell
    just install
    ```
  - This will create a virtual environment and install all required packages.

You’re now ready to build, test, and run the application!

## License
MIT License