# Quick Start Guide

Get up and running with the Multi-Camera 3D Scene Reconstruction System in 15 minutes!

## Prerequisites

### Hardware
- Computer with USB 3.0 ports (3 available)
- 3× USB Webcams (Logitech C270 recommended)
- 8GB+ RAM
- Multi-core CPU (4+ cores recommended)

### Software
- Python 3.8 or higher
- Git (for cloning repository)

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/Sherin-SEF-AI/Multi-Camera-3D-Scene-Reconstruction-Mapping-System.git
cd Multi-Camera-3D-Scene-Reconstruction-Mapping-System
```

### Step 2: Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- PyQt6 (GUI framework)
- OpenCV (computer vision)
- Open3D (3D processing)
- NumPy, SciPy (scientific computing)
- And other required packages

### Step 4: Verify Installation

```bash
python -c "import cv2, open3d, PyQt6; print('✓ All dependencies installed!')"
```

If this prints the success message, you're ready to go!

---

## First Run

### 1. Connect Cameras

1. Plug in 3 USB webcams to your computer
2. Use separate USB ports/controllers if possible (for bandwidth)
3. On Linux, you may need to add your user to the `video` group:
   ```bash
   sudo usermod -a -G video $USER
   # Log out and back in
   ```

### 2. Launch Application

```bash
python src/main.py
```

The main window should appear with three panels:
- **Left**: Camera feeds
- **Center**: 3D visualization
- **Right**: Controls

### 3. Connect Cameras

1. Click **"Connect Cameras"** button in the Camera Panel (left)
2. Wait a few seconds for auto-detection
3. You should see 3 live camera feeds appear

**Troubleshooting**: If cameras don't appear, check:
- Cameras are plugged in and powered
- No other application is using the cameras
- On Linux, check permissions (`ls -l /dev/video*`)

### 4. Start Basic 3D Reconstruction

1. Click the **"Start"** button in the toolbar
2. Move an object in front of cameras 0 and 1
3. Watch the 3D point cloud appear in the center panel!

**Note**: Without calibration, the reconstruction will use default parameters (lower quality).

---

## Your First Calibration

For better quality reconstruction, calibrate your cameras!

### What You Need

- **Chessboard Pattern**: Print `docs/chessboard_9x6.pdf` (or use any 9×6 chessboard)
- **Size**: Measure the square size in mm (typically 25mm)
- **Flat Surface**: Mount pattern on cardboard or foam board

### Calibrate Camera 0

1. Go to **Calibration > Calibrate Intrinsic**
2. Select **Camera 0** from dropdown
3. Set **Target Images** to 20
4. Click **"Start Capture"**
5. Present chessboard pattern to camera:
   - Hold pattern flat and visible
   - When corners detected (green text), click **"Capture Image"**
   - Vary angle, rotation, distance (20 different views)
6. Once 20 images captured, click **"Calibrate"**
7. Check **Reprojection Error** < 0.5 pixels (good quality)
8. Click **"Close"**

### Calibrate Camera 1

Repeat the same process for Camera 1.

### Calibrate Stereo Pair (0-1)

1. Go to **Calibration > Calibrate Stereo**
2. Select **Camera 0** and **Camera 1**
3. Click **"Check Prerequisites"** (should show ✓)
4. Click **"Calibrate Stereo Pair"**
5. Wait for calibration to complete
6. Note the **Baseline** distance (physical camera separation)

### Save Calibration

1. Go to **Calibration > Save Calibration**
2. Save to `calibrations/my_calibration.json`

**Done!** Your cameras are now calibrated for accurate 3D reconstruction.

---

## Enable Visual SLAM

SLAM tracks camera motion and builds a 3D map.

### Prerequisites

- Camera 0 must be intrinsically calibrated (see above)

### Steps

1. Go to **SLAM tab** (right panel)
2. Check **"Enable SLAM"**
3. If not calibrated, you'll see a warning
4. Once enabled, status shows: "Status: Active"

### Use SLAM

1. Ensure SLAM is enabled
2. Click **"Start"** to begin processing
3. Switch view mode to **"SLAM Trajectory"** (center panel, top dropdown)
4. Move camera slowly or move objects
5. Watch:
   - **Red line**: Camera trajectory
   - **Colored points**: SLAM map points
   - **Status**: Shows pose and point count

**Tips**:
- Start with slow, smooth motion
- Work in well-lit, textured environments
- Avoid rapid movements

---

## Export Your First 3D Model

### Point Cloud

1. Start processing and capture a scene
2. Go to **Export tab** (right panel)
3. Click **"Export as PLY"**
4. Save to `exports/my_scene.ply`
5. Open in MeshLab, CloudCompare, or Blender!

### Mesh

1. Ensure point cloud is generated
2. Go to **Export tab**
3. Click **"Export as OBJ"** (under Mesh section)
4. System generates mesh using Poisson reconstruction
5. Save and view in Blender or MeshLab

### SLAM Trajectory

1. Enable SLAM and move around
2. Go to **Export tab**
3. Click **"Export Trajectory"**
4. Save as `.txt` or `.csv`
5. Visualize in Python/MATLAB or plotting tools

---

## Common Workflows

### Workflow 1: Quick 3D Scan

**Goal**: Fast 3D model of an object

1. Connect cameras
2. Click "Start"
3. Place object between cameras
4. Wait 5-10 seconds for good coverage
5. Click "Snapshot" (instant save)
6. Export point cloud or mesh

**Time**: 2 minutes

### Workflow 2: Calibrated High-Quality Scan

**Goal**: Accurate, detailed 3D model

1. Calibrate cameras (intrinsic + stereo)
2. Start processing
3. Adjust stereo parameters for quality (Stereo tab)
4. Place object, capture multiple views
5. Export mesh with high resolution

**Time**: 30 minutes (including calibration)

### Workflow 3: SLAM Room Mapping

**Goal**: Map a room with camera trajectory

1. Calibrate camera 0
2. Enable SLAM
3. Start processing
4. Walk slowly through room
5. View in "SLAM Trajectory" mode
6. Export trajectory and map points

**Time**: 5-10 minutes

### Workflow 4: Occupancy Map

**Goal**: 2D occupancy grid of environment

1. Start processing
2. Switch view to "Occupancy Map"
3. Move cameras or objects to build map
4. Export occupancy map as PNG or NumPy

**Time**: 5 minutes

---

## Next Steps

### Learn More

- **Full Feature Guide**: See `docs/FEATURES.md`
- **Calibration Details**: See `docs/CALIBRATION_GUIDE.md`
- **Troubleshooting**: See `docs/TROUBLESHOOTING.md`
- **Configuration**: Edit `config/default_config.json`

### Experiment

- Try different stereo algorithms (SGBM vs. Block Matching)
- Adjust point cloud filtering parameters
- Test different SLAM feature detectors (ORB, SIFT, AKAZE)
- Record sessions for later analysis

### Advanced

- Multi-view stereo (use all 3 cameras)
- Mesh refinement and texturing
- Loop closure for SLAM
- Integration with ROS or other frameworks

---

## Tips for Success

1. **Good Lighting**: Use bright, even lighting
2. **Textured Scenes**: Plain white walls don't work well
3. **Camera Placement**: Position cameras 20-30cm apart for good stereo
4. **Calibration**: Always calibrate for best results
5. **Start Simple**: Begin with objects before trying rooms
6. **Check FPS**: Monitor frame rate in status bar
7. **System Resources**: Close other apps for best performance

---

## Help & Support

### Documentation

- `README.md`: Project overview
- `docs/FEATURES.md`: Complete feature documentation
- `docs/CALIBRATION_GUIDE.md`: Detailed calibration help
- `docs/TROUBLESHOOTING.md`: Common issues and solutions

### Issues

Report bugs or request features:
https://github.com/Sherin-SEF-AI/Multi-Camera-3D-Scene-Reconstruction-Mapping-System/issues

### Community

Share your 3D scans and experiences!

---

## Quick Reference

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+R` | Start processing |
| `Ctrl+T` | Stop processing |
| `Ctrl+S` | Save session |
| `Ctrl+Q` | Quit |

### Menu Actions

- **File > Open/Save Session**: Load/save complete sessions
- **Calibration > Calibrate**: Open calibration dialogs
- **Processing > Start/Stop**: Control 3D reconstruction
- **View > Toggle Panels**: Show/hide UI panels
- **Export**: Various export options

### Panel Layout

```
┌─────────────┬──────────────────┬─────────────┐
│             │                  │             │
│   Camera    │   3D Viewer     │  Controls   │
│   Feeds     │  (Center)        │  (Tabs)     │
│   (Left)    │                  │             │
│             │                  │             │
└─────────────┴──────────────────┴─────────────┘
```

---

**Happy Scanning!** 🎉

If you encounter any issues, check `docs/TROUBLESHOOTING.md` or open an issue on GitHub.
