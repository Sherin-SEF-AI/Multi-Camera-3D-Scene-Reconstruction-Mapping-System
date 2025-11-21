# User Manual
## Multi-Camera 3D Scene Reconstruction & Mapping System

Version 1.0.0

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Interface Overview](#user-interface-overview)
4. [Camera Management](#camera-management)
5. [Calibration](#calibration)
6. [3D Reconstruction](#3d-reconstruction)
7. [Visualization](#visualization)
8. [Export and Recording](#export-and-recording)
9. [Advanced Features](#advanced-features)
10. [Keyboard Shortcuts](#keyboard-shortcuts)
11. [Tips and Best Practices](#tips-and-best-practices)

---

## Introduction

This manual provides comprehensive instructions for using the Multi-Camera 3D Scene Reconstruction & Mapping System. The system enables real-time 3D reconstruction of scenes using multiple USB webcams.

### System Overview

- **Multiple Camera Support**: Simultaneous capture from 3 cameras
- **Real-time Processing**: Live 3D reconstruction and visualization
- **Professional Tools**: Calibration, stereo vision, SLAM
- **Export Capabilities**: Multiple format support for data export

---

## Getting Started

### First-Time Setup

1. **Install Software** (see README.md for installation instructions)
2. **Connect Cameras**: Attach 3 USB webcams to your computer
3. **Launch Application**:
   ```bash
   python src/main.py
   ```
4. **Verify Camera Detection**: Check that all 3 cameras appear in the left panel

### System Requirements Check

Before starting, ensure:
- ✓ All cameras are detected
- ✓ Camera feeds are displaying
- ✓ Sufficient system resources (check status bar)

---

## User Interface Overview

### Main Window Layout

The application window is divided into three main panels with menu bar, toolbar, and status bar.

#### Left Panel: Camera Feeds (30%)
- Live video feeds from all cameras
- Camera status indicators
- Individual camera controls
- Frame timestamps

#### Center Panel: 3D Visualization (50%)
- Real-time 3D point cloud display
- Interactive view controls (rotate, pan, zoom)
- Visualization modes (point cloud, mesh, occupancy)
- Camera frustum display

#### Right Panel: Controls (20%)
- Tabbed interface for different functions
- Parameter adjustment
- Real-time metrics
- Export options

---

## Camera Management

### Auto-Detection

The system automatically detects connected USB cameras on startup.

**If cameras are not detected:**
1. Check USB connections
2. Verify camera permissions
3. Restart the application

### Camera Settings

Each camera has individual controls for resolution, FPS, exposure, brightness, and contrast.

### Camera Status Indicators

- 🟢 Green: Camera active and capturing
- 🔴 Red: Camera disconnected or error
- 🟡 Yellow: Camera connected but not capturing

---

## Calibration

Calibration is required before 3D reconstruction. See [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) for detailed instructions.

### Quick Calibration Steps

1. **Prepare Pattern**: Print 9x6 chessboard (25mm squares)
2. **Start Calibration**: Calibration > Calibrate Intrinsic
3. **Capture Images**: Present pattern from 20+ different angles per camera
4. **Automatic Processing**: System computes calibration parameters
5. **Save**: Calibration > Save Calibration

---

## 3D Reconstruction

### Starting Reconstruction

1. **Ensure Calibration**: Cameras must be calibrated
2. **Click Start**: Toolbar > Start button or Ctrl+R
3. **View Results**: 3D point cloud appears in center panel

### Processing Modes

- **Fast Mode**: Lower quality, higher FPS
- **Balanced Mode**: Good balance (default)
- **Quality Mode**: Maximum quality, slower

---

## Visualization

### 3D View Controls

**Mouse Controls**:
- **Left Click + Drag**: Rotate view
- **Right Click + Drag**: Pan view
- **Scroll Wheel**: Zoom in/out
- **Double Click**: Reset view

---

## Export and Recording

### Exporting Point Clouds

1. Go to **Export > Export Point Cloud**
2. Choose format: PLY, PCD, or XYZ
3. Select location and save

### Recording Sessions

- Click **Record** button to start
- Click again to stop
- Videos saved to `recordings/` directory

---

## Keyboard Shortcuts

- `Ctrl+Q`: Quit application
- `Ctrl+S`: Save session
- `Ctrl+R`: Start/Resume processing
- `Ctrl+T`: Stop processing
- `Space`: Pause/Resume

---

## Tips and Best Practices

### For Best Results

**Camera Placement**:
- Mount cameras rigidly
- Arrange with overlapping field of view
- Typical separation: 10-20cm for desktop scenes

**Lighting**:
- Use diffuse, even lighting
- Avoid direct sunlight
- Prevent shadows on scene

---

**Last Updated**: 2024
**Version**: 1.0.0
