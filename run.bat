@echo off
REM Run MetaEditor SafeTensors using packaged Python environment
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe main.py %*
) else (
    echo ERROR: Packaged Python not found in venv\Scripts\python.exe
    echo Please ensure you have unzipped the full package and venv is present.
    pause
    exit /b 1
)
