@echo off
echo MetaEditor SafeTensors - Starting...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or newer from https://python.org
    pause
    exit /b 1
)

REM Check Python version (must be 3.10 or newer)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Detected Python version: %PYTHON_VERSION%

REM Parse major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

REM Enable delayed variable expansion for the version checks
setlocal enabledelayedexpansion

if !MAJOR! LSS 3 (
    echo ERROR: Python version %PYTHON_VERSION% is too old
    echo Please install Python 3.10 or newer from https://python.org
    pause
    exit /b 1
)

if !MAJOR! EQU 3 if !MINOR! LSS 10 (
    echo ERROR: Python version %PYTHON_VERSION% is too old  
    echo Please install Python 3.10 or newer from https://python.org
    pause
    exit /b 1
)

echo Python version check passed: %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    
    echo Installing dependencies...
    venv\Scripts\pip install --upgrade pip
    venv\Scripts\pip install -e .
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Activate virtual environment and run
echo Starting MetaEditor SafeTensors...
call venv\Scripts\activate && python main.py %*

pause
