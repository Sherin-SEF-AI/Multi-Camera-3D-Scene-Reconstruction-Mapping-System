# Feature Documentation

Complete guide to all features in the Multi-Camera 3D Scene Reconstruction & Mapping System.

## Table of Contents

1. [Camera Management](#camera-management)
2. [Camera Calibration](#camera-calibration)
3. [3D Reconstruction](#3d-reconstruction)
4. [Visual SLAM](#visual-slam)
5. [Occupancy Mapping](#occupancy-mapping)
6. [Visualization](#visualization)
7. [Recording & Export](#recording--export)
8. [Configuration](#configuration)

---

## Camera Management

### Multi-Camera Support
- **3 USB Webcams**: Automatic detection and connection
- **Logitech C270 Optimized**: Specific support for Logitech C270 webcams
- **Live Feeds**: Real-time display from all cameras
- **Resolution Control**: Per-camera resolution settings (320x240 to 1280x720)
- **FPS Control**: Adjustable frame rate (15-30 FPS)

### Usage
1. Connect 3 USB webcams to your computer
2. Click **"Connect Cameras"** button in Camera Panel
3. System will auto-detect cameras at indices 2, 4, 6
4. Live feeds appear in the Camera Panel

### Features
- Independent camera workers for each camera
- Thread-safe frame capture
- FPS monitoring per camera
- Status indicators for each camera

---

## Camera Calibration

### Intrinsic Calibration

Calibrates individual camera parameters (focal length, principal point, distortion).

#### Steps:
1. Go to **Calibration > Calibrate Intrinsic**
2. Select camera to calibrate
3. Set target images (10-50, default 20)
4. Click **"Start Capture"**
5. Present chessboard pattern to camera from different angles
6. Click **"Capture Image"** when pattern is detected (green)
7. Continue until target reached
8. Click **"Calibrate"** to compute calibration

#### Features:
- **Real-time Detection**: Visual feedback when chessboard is detected
- **Progress Tracking**: Shows images captured vs. target
- **Quality Metrics**: Displays reprojection error
- **Results Display**: Shows focal length, principal point, distortion
- **Auto-save**: Calibration saved to intrinsic_calibrations dict
- **SLAM Integration**: Camera 0 calibration auto-configures SLAM

#### Best Practices:
- Use good lighting
- Keep pattern flat and visible
- Capture from various angles (tilted, rotated, near, far)
- Aim for reprojection error < 0.5 pixels

### Stereo Calibration

Calibrates the geometric relationship between two cameras.

#### Prerequisites:
- Both cameras must be intrinsically calibrated first

#### Steps:
1. Go to **Calibration > Calibrate Stereo**
2. Select camera pair (e.g., 0-1)
3. Click **"Check Prerequisites"**
4. If ready, click **"Calibrate Stereo Pair"**
5. System computes rotation, translation, and baseline

#### Results:
- Rotation matrix (R): How camera 2 is rotated relative to camera 1
- Translation vector (T): Position of camera 2 relative to camera 1
- Baseline: Physical distance between cameras
- Essential/Fundamental matrices

### Save/Load Calibration

- **Save**: Calibration > Save Calibration → Exports to JSON
- **Load**: Calibration > Load Calibration → Imports from JSON
- **Format**: JSON with camera matrices and distortion coefficients

---

## 3D Reconstruction

### Stereo Vision

Real-time 3D point cloud generation from two calibrated cameras.

#### Pipeline:
1. **Capture**: Frames from cameras 0 and 1
2. **Rectification** (if calibrated): Align image planes
3. **Disparity Computation**: SGBM or Block Matching
4. **Depth Estimation**: Convert disparity to depth
5. **Point Cloud Generation**: 3D points from depth + camera matrix
6. **Filtering**: Statistical outlier removal
7. **Downsampling**: Voxel grid downsampling if > 100k points

#### Parameters (Stereo Tab):
- **Algorithm**: SGBM (accurate) or Block Matching (fast)
- **Block Size**: Window size for matching (5-21)
- **Num Disparities**: Maximum disparity (16-256)
- **Min Disparity**: Starting disparity value

#### Point Cloud Processing (Point Cloud Tab):
- **Voxel Downsampling**: Reduce density
- **Statistical Outlier Removal**: Remove noise
- **Max Points**: Limit point cloud size

---

## Visual SLAM

### Overview

Visual SLAM (Simultaneous Localization and Mapping) tracks camera motion and builds a 3D map using feature detection and matching.

### Architecture

**SLAMWorker Thread**:
- Runs independently at 30 Hz
- Processes frames from camera 0
- Builds trajectory and map points
- Emits updates every 500ms

### Features

#### Feature Detection:
- **ORB**: Fast, rotation-invariant (default)
- **SIFT**: Accurate, scale-invariant
- **AKAZE**: Fast, scale and rotation invariant
- **Configurable**: 100-5000 features

#### Pose Estimation:
- Essential Matrix computation with RANSAC
- Camera pose recovery (R, t)
- Trajectory accumulation

#### Mapping:
- 3D point triangulation
- Color mapping from images
- Map point observations tracking

### Usage

#### Setup:
1. **Calibrate Camera 0**: SLAM requires intrinsic calibration
   - Go to Calibration > Calibrate Intrinsic
   - Select Camera 0
   - Complete calibration process

2. **Configure SLAM** (SLAM Tab):
   - Feature Type: ORB (recommended for real-time)
   - Num Features: 1000 (balance speed/accuracy)

3. **Enable SLAM**:
   - Check "Enable SLAM" in SLAM tab
   - System validates calibration
   - SLAM worker starts

4. **Start Processing**:
   - Click "Start" button
   - Move camera or objects in scene
   - Watch trajectory build in real-time

#### Visualization:
- Switch to **"SLAM Trajectory"** mode in Visualization panel
- Red line: Camera trajectory
- Colored points: SLAM map points
- Status shows: # poses, # map points

### Tips for Best Results:

1. **Good Lighting**: Ensure consistent, adequate lighting
2. **Textured Scenes**: SLAM works best with feature-rich environments
3. **Smooth Motion**: Avoid rapid camera movements
4. **Overlap**: Maintain visual overlap between frames
5. **Initialization**: Start with slow motion for good initialization

### Limitations:

- **Monocular**: Scale is ambiguous (relative, not absolute)
- **No Loop Closure**: Drift accumulates over time
- **Feature Dependency**: Fails in texture-less environments
- **Real-time Constraint**: May drop frames under heavy load

---

## Occupancy Mapping

### 2D Occupancy Grid

Real-time 2D occupancy map from 3D point clouds.

#### How It Works:
1. Point clouds are generated from stereo vision
2. Points are projected onto 2D grid (top-down view)
3. Occupied cells are marked
4. Visualization shows occupied (red) vs. free space

#### Features:
- **Real-time Updates**: Updates with each point cloud
- **Configurable Resolution**: Cell size adjustable
- **Visualization**: Color-coded occupancy probability
- **Export**: Save as NumPy array or PNG image

#### Usage:
1. Start processing (enables automatically)
2. Switch to **"Occupancy Map"** view mode
3. Red cells indicate occupied space
4. Export via Export tab

#### Configuration:
- Grid size: Configurable in config file
- Cell size: Typically 5cm per cell
- Update rate: Throttled to maintain performance

### 3D Occupancy Grid

(Available in code, visualization pending)
- Voxel-based 3D occupancy
- Full 3D environment representation

---

## Visualization

### 3D Viewer

PyQtGraph OpenGL-based 3D visualization widget.

#### View Modes:
1. **Point Cloud**: Stereo reconstruction results
2. **SLAM Trajectory**: Camera path + map points
3. **Occupancy Map**: 2D grid overlay
4. **Mesh**: (Future feature)

#### Controls:
- **Mouse Drag**: Rotate view
- **Mouse Wheel**: Zoom in/out
- **Right Click + Drag**: Pan
- **Reset View Button**: Return to default position

#### Elements:
- **Grid**: Ground plane reference
- **Axes**: XYZ coordinate system (RGB)
  - Red: X-axis
  - Green: Y-axis
  - Blue: Z-axis
- **Point Cloud**: Colored 3D points
- **Trajectory**: Red line showing camera path
- **Map Points**: SLAM features (colored)

### Display Options:
- **Mode Selector**: Dropdown to switch between views
- **Visibility Control**: Auto show/hide based on mode
- **Info Label**: Shows current data (# points, # poses, etc.)

---

## Recording & Export

### Session Recording

Record complete reconstruction sessions with metadata.

#### Features:
- **Timestamped Directories**: Each session in `recordings/session_YYYYMMDD_HHMMSS/`
- **Automatic Metadata**: Captures system state
- **SLAM Integration**: Records trajectory and map point counts

#### Usage:
1. Start processing first
2. Click **"Record"** button
3. Perform reconstruction
4. Click **"Stop Recording"**
5. Metadata saved to `session_info.txt`

#### Metadata Includes:
- Frame count
- SLAM status (enabled/disabled)
- Number of SLAM poses
- Number of SLAM map points
- Session timestamp

### Quick Snapshots

Instant point cloud capture.

#### Usage:
- Click **"Snapshot"** button anytime during processing
- Saves current point cloud with timestamp
- Files: `exports/snapshot_YYYYMMDD_HHMMSS.ply`

### Export Options

Comprehensive export system for all data types.

#### Point Cloud Export (Export Tab):
- **PLY**: Standard point cloud format (with colors)
- **PCD**: Point Cloud Data format (Open3D/PCL)
- **XYZ**: ASCII point coordinates

#### Mesh Export (Export Tab):
- **OBJ**: Wavefront object (with materials)
- **STL**: Stereolithography (for 3D printing)
- **PLY**: Polygon file format
- **Generation**: Poisson surface reconstruction from point cloud

#### Occupancy Map Export:
- **NumPy Array (.npy)**: Raw grid data for analysis
- **PNG Image**: Visual representation

#### SLAM Trajectory Export:
- **Text File (.txt)**: Space-separated coordinates (x y z)
- **CSV File (.csv)**: Comma-separated values
- **Format**: One pose per line

### File Locations:
- **Exports**: `exports/`
- **Calibrations**: `calibrations/`
- **Recordings**: `recordings/`
- **Snapshots**: `exports/snapshot_*.ply`

---

## Configuration

### Configuration File

Location: `config/default_config.json`

#### Key Settings:

```json
{
  "cameras": {
    "num_cameras": 3,
    "default_resolution": [640, 480],
    "default_fps": 30
  },
  "calibration": {
    "chessboard_size": [9, 6],
    "square_size": 25.0
  },
  "stereo": {
    "algorithm": "SGBM",
    "block_size": 11,
    "num_disparities": 128
  },
  "point_cloud": {
    "max_points": 100000,
    "voxel_size": 0.01
  },
  "slam": {
    "feature_type": "ORB",
    "num_features": 1000
  },
  "ui": {
    "window_size": [1920, 1080],
    "theme": "dark"
  }
}
```

### Runtime Configuration:

Most settings can be adjusted through the GUI:
- Camera settings: Camera Panel
- Stereo parameters: Stereo Tab
- Point cloud options: Point Cloud Tab
- SLAM settings: SLAM Tab

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+R` | Start/Resume processing |
| `Ctrl+T` | Stop processing |
| `Ctrl+S` | Save session |
| `Ctrl+O` | Open session |
| `Ctrl+Q` | Quit application |

---

## Performance Tips

### For Real-Time (30 FPS):
1. Resolution: 640x480
2. Point cloud max: 50,000 points
3. Stereo algorithm: Block Matching
4. Voxel downsampling: Enabled (0.01)
5. SLAM features: 500-1000

### For High Quality:
1. Resolution: 1280x720
2. Point cloud max: 200,000 points
3. Stereo algorithm: SGBM
4. Voxel downsampling: Disabled or larger (0.02)
5. SLAM features: 2000-5000

### System Requirements:
- **CPU**: Multi-core recommended (4+ cores)
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: Not required, but helps with visualization
- **USB**: USB 3.0 for best camera bandwidth
- **OS**: Linux, Windows, macOS

---

## Advanced Features

### Multi-View Stereo:
- Combine multiple camera pairs
- Denser reconstruction
- Better coverage

### Mesh Reconstruction:
- Poisson surface reconstruction
- Alpha shapes
- Ball pivoting

### Filtering:
- Statistical outlier removal
- Radius outlier removal
- Voxel grid filtering

---

## Known Issues & Limitations

### Camera Bandwidth:
- 3 cameras at high resolution may exceed USB bandwidth
- Solution: Lower resolution or use separate USB controllers

### SLAM Scale Ambiguity:
- Monocular SLAM has no absolute scale
- Relative motion only

### Calibration Required:
- Stereo reconstruction needs calibration for accuracy
- SLAM requires intrinsic calibration

### Performance:
- Real-time processing depends on hardware
- May need to reduce settings on slower systems

---

## Future Enhancements

- [ ] Loop closure detection for SLAM
- [ ] Deep learning depth estimation
- [ ] Multi-frame fusion
- [ ] Object detection integration
- [ ] AR/VR visualization
- [ ] Cloud processing support

---

**Version**: 1.0.0
**Last Updated**: 2024
**Status**: Production Ready ✅
