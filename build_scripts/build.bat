@echo off
REM Build script for creating standalone binary on Windows

echo Building MetaEditor SafeTensors standalone binary...

REM Install development dependencies if not already installed
pip install -r requirements-dev.txt

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Build with PyInstaller
pyinstaller build_scripts\build.spec

echo Build complete! Binary located in dist\
echo Standalone binary ready for distribution!
