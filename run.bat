@echo off
REM Create virtual environment if it doesn't exist
if not exist venv (
    python -m venv venv
    venv\Scripts\pip install --upgrade pip
    venv\Scripts\pip install -r requirements.txt
)

REM Run the main entry point
venv\Scripts\python -m metaeditor_safetensors %*

pause
