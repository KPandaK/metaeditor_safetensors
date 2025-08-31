@echo off
REM Create virtual environment if it doesn't exist
if not exist venv (
    python -m venv venv
    venv\Scripts\pip install --upgrade pip
    venv\Scripts\pip install -r requirements.txt
)

REM Activate the virtual environment
call venv\Scripts\activate

REM Run the main entry point
python src\metaeditor_safetensors\main.py %*

pause
