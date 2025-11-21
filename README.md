# Multi-Camera 3D Scene Reconstruction & Mapping System

A professional, production-ready desktop application for real-time 3D scene reconstruction using multiple external USB webcams. Built with PyQt6, OpenCV, and Open3D.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Features

### Multi-Camera Management
- Auto-detect and connect to 3 USB webcams
- Live feeds from all cameras simultaneously
- Per-camera resolution and FPS controls
- Camera naming and labeling
- Synchronized frame capture across all cameras

### Camera Calibration
- Automatic chessboard pattern detection
- Intrinsic calibration (focal length, principal point, distortion)
- Extrinsic calibration (relative camera positions)
- Stereo pair calibration for depth estimation
- Visual feedback during calibration
- Save/load calibration profiles (JSON format)
- Calibration quality metrics

### Stereo Vision & Depth Estimation
- Real-time disparity map computation
- Multiple algorithms (SGBM, Block Matching)
- Depth map generation with color visualization
- Adjustable stereo parameters
- Point cloud generation from depth maps
- Multi-view triangulation

### 3D Point Cloud Reconstruction
- Real-time 3D point cloud generation
- Integrated Open3D 3D viewer
- Point cloud filtering (statistical outlier removal, voxel downsampling)
- Color mapping from camera images
- Export formats: PLY, PCD, XYZ
- Point cloud recording and playback

### Occupancy Mapping
- Real-time 2D occupancy grid (top-down view)
- 3D voxel occupancy map
- Free space vs occupied space detection
- Adjustable grid resolution
- Occupancy probability visualization

### Visual SLAM
- Feature-based visual odometry
- Camera pose estimation and tracking
- Feature detection (ORB, SIFT, AKAZE)
- Trajectory visualization
- Map point tracking

### Professional GUI
- Three-panel layout (Camera Feeds | 3D Visualization | Controls)
- Menu bar with File, Calibration, Processing, View, Export, Help
- Toolbar with quick access buttons
- Status bar with real-time metrics
- Dark and light themes
- Keyboard shortcuts

## Requirements

### Hardware
- Computer with USB 3.0 ports
- 3x Logitech USB webcams (or compatible)
- 8GB+ RAM recommended
- GPU recommended for real-time processing

### Software
- Python 3.8 or higher
- Operating System: Linux, Windows, or macOS

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Multi-Camera-3D-Scene-Reconstruction-Mapping-System.git
cd Multi-Camera-3D-Scene-Reconstruction-Mapping-System
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import cv2, open3d, PyQt6; print('All dependencies installed successfully')"
```

## Quick Start

### 1. Connect Cameras

Connect 3 USB webcams to your computer. The system will auto-detect them on startup.

### 2. Run the Application

```bash
python src/main.py
```

### 3. Initial Setup

1. **Camera Detection**: Cameras should be auto-detected and displayed in the left panel
2. **Calibration**: Before 3D reconstruction, calibrate your cameras (see Calibration Guide)
3. **Processing**: Click "Start" to begin real-time 3D reconstruction

## Configuration

The application uses a JSON configuration file located at `config/default_config.json`. Key settings include:

- **Camera settings**: Resolution, FPS, number of cameras
- **Calibration**: Chessboard size, square size
- **Stereo parameters**: Algorithm, block size, disparities
- **Point cloud**: Voxel size, filtering parameters
- **UI**: Window size, theme, panel layout

## Usage

### Camera Setup

1. Connect 3 USB webcams
2. Launch application
3. Cameras will be auto-detected and assigned to slots 0, 1, 2
4. Verify camera feeds in the left panel

### Calibration Workflow

1. Print a chessboard calibration pattern (9x6 or as configured)
2. Go to **Calibration > Calibrate Intrinsic**
3. Present the pattern to each camera from different angles
4. Capture 20+ images per camera
5. System will compute calibration automatically
6. Save calibration: **Calibration > Save Calibration**

For detailed calibration instructions, see [docs/CALIBRATION_GUIDE.md](docs/CALIBRATION_GUIDE.md)

### 3D Reconstruction

1. Ensure cameras are calibrated
2. Click **Start** button in toolbar
3. View real-time:
   - Disparity maps
   - Depth maps
   - 3D point cloud
   - Occupancy maps

### Exporting Data

- **Point Cloud**: File > Export > Point Cloud (PLY, PCD, XYZ formats)
- **Mesh**: File > Export > Mesh (OBJ, STL formats)
- **Occupancy Map**: File > Export > Occupancy Map
- **Trajectory**: Export SLAM trajectory data

## Project Structure

```
Multi-Camera-3D-Scene-Reconstruction-Mapping-System/
├── src/
│   ├── main.py                 # Application entry point
│   ├── core/                   # Core processing modules
│   │   ├── camera_manager.py   # Camera management
│   │   ├── calibration.py      # Camera calibration
│   │   ├── stereo_vision.py    # Stereo matching and depth
│   │   ├── point_cloud.py      # Point cloud processing
│   │   ├── occupancy_mapping.py # Occupancy grid generation
│   │   └── slam.py             # Visual SLAM
│   ├── gui/                    # PyQt6 GUI components
│   │   ├── main_window.py      # Main application window
│   │   ├── camera_panel.py     # Camera feed display
│   │   ├── visualization_panel.py # 3D visualization
│   │   └── control_panel.py    # Control widgets
│   ├── utils/                  # Utility modules
│   │   ├── config.py           # Configuration management
│   │   ├── logger.py           # Logging system
│   │   └── file_manager.py     # File operations
│   └── workers/                # Background worker threads
│       ├── camera_worker.py    # Camera frame capture
│       └── processing_worker.py # 3D processing
├── config/
│   └── default_config.json     # Default configuration
├── calibrations/               # Saved calibrations
├── exports/                    # Exported data
├── recordings/                 # Recorded sessions
├── docs/                       # Documentation
│   ├── CALIBRATION_GUIDE.md    # Calibration instructions
│   └── USER_MANUAL.md          # Detailed user guide
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Keyboard Shortcuts

- `Ctrl+R` - Start/Resume processing
- `Ctrl+T` - Stop processing
- `Ctrl+S` - Save session
- `Ctrl+O` - Open session
- `Ctrl+Q` - Quit application

## Troubleshooting

### Cameras Not Detected

- Ensure webcams are properly connected
- Try different USB ports
- Check camera permissions (Linux: add user to `video` group)
- Restart application

### Low Frame Rate

- Reduce camera resolution
- Decrease stereo matching quality
- Enable GPU acceleration
- Reduce number of point cloud points

### Calibration Fails

- Ensure chessboard pattern is clearly visible
- Use good lighting conditions
- Capture images from various angles
- Use at least 20 images per camera

### Application Crashes

- Check logs in `logs/` directory
- Verify all dependencies are installed
- Ensure sufficient system resources
- Report issue on GitHub

## Performance Optimization

### For Real-Time Processing

1. **Camera Settings**:
   - Resolution: 640x480 or 800x600
   - FPS: 30

2. **Point Cloud**:
   - Enable voxel downsampling
   - Reduce max points to 100,000

3. **Stereo Matching**:
   - Use Block Matching for speed
   - Reduce num_disparities

### For High Quality

1. **Camera Settings**:
   - Resolution: 1280x720 or higher
   - FPS: 30

2. **Point Cloud**:
   - Disable downsampling
   - Increase statistical filtering parameters

3. **Stereo Matching**:
   - Use SGBM algorithm
   - Increase num_disparities

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Citation

If you use this software in your research, please cite:

```bibtex
@software{multicamera3d2024,
  title={Multi-Camera 3D Scene Reconstruction System},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/Multi-Camera-3D-Scene-Reconstruction-Mapping-System}
}
```

## Acknowledgments

- OpenCV for computer vision algorithms
- Open3D for 3D processing and visualization
- PyQt6 for the GUI framework

## Support

For questions, issues, or feature requests:
- GitHub Issues: https://github.com/yourusername/Multi-Camera-3D-Scene-Reconstruction-Mapping-System/issues
- Documentation: See `docs/` directory

## Roadmap

- [ ] Advanced mesh reconstruction algorithms
- [ ] Deep learning-based depth estimation
- [ ] Multi-frame fusion for noise reduction
- [ ] Object detection and segmentation
- [ ] Cloud-based processing support
- [ ] Mobile app integration

---

**Version**: 1.0.0
**Last Updated**: 2024
**Status**: Production Ready
