#!/bin/bash
# Launch script for Multi-Camera 3D Reconstruction System

echo "Starting Multi-Camera 3D Reconstruction System..."
echo "========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if dependencies are installed
python -c "import cv2, open3d, PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Dependencies missing. Installing..."
    pip install -r requirements.txt
fi

# Launch application
echo "Launching application..."
python src/main.py

# Deactivate virtual environment on exit
deactivate
