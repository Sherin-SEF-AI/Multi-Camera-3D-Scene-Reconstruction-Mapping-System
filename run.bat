@echo off
REM Launch script for Multi-Camera 3D Reconstruction System (Windows)

echo Starting Multi-Camera 3D Reconstruction System...
echo =========================================

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Installing dependencies...
    call venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Check if dependencies are installed
python -c "import cv2, open3d, PyQt6" 2>nul
if errorlevel 1 (
    echo Dependencies missing. Installing...
    pip install -r requirements.txt
)

REM Launch application
echo Launching application...
python src\main.py

REM Deactivate virtual environment on exit
deactivate
