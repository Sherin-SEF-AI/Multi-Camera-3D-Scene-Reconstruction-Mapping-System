# Troubleshooting Guide

Solutions to common issues and problems with the Multi-Camera 3D Reconstruction System.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Camera Problems](#camera-problems)
- [Calibration Issues](#calibration-issues)
- [Performance Problems](#performance-problems)
- [SLAM Issues](#slam-issues)
- [Visualization Problems](#visualization-problems)
- [Export Errors](#export-errors)
- [System Crashes](#system-crashes)

---

## Installation Issues

### ImportError: No module named 'PyQt6'

**Problem**: Missing PyQt6 or other dependencies

**Solution**:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If still failing:
```bash
pip install PyQt6 PyQt6-WebEngine
```

### ImportError: No module named 'cv2'

**Problem**: OpenCV not installed

**Solution**:
```bash
pip install opencv-python opencv-contrib-python
```

### ImportError: No module named 'open3d'

**Problem**: Open3D not installed

**Solution**:
```bash
pip install open3d
```

For older systems, try:
```bash
pip install open3d==0.17.0
```

### ImportError: DLL load failed (Windows)

**Problem**: Missing Visual C++ Redistributables

**Solution**:
1. Download and install Visual C++ Redistributables
2. Restart computer
3. Try again

### Permission Denied Errors (Linux)

**Problem**: Insufficient permissions

**Solution**:
```bash
sudo chmod +x run.sh
# Or for camera access:
sudo usermod -a -G video $USER
# Log out and back in
```

---

## Camera Problems

### Cameras Not Detected

**Symptoms**: "No cameras detected" message after clicking "Connect Cameras"

**Solutions**:

1. **Check Physical Connection**:
   ```bash
   # Linux:
   ls /dev/video*
   # Should show video0, video2, video4, video6, etc.

   # Windows: Check Device Manager > Cameras
   # macOS: System Preferences > Security > Camera
   ```

2. **Close Other Applications**:
   - Close Chrome, Zoom, Skype, etc.
   - Only one app can access cameras at a time

3. **Check Permissions (Linux)**:
   ```bash
   sudo usermod -a -G video $USER
   newgrp video  # Or log out/in
   ```

4. **Try Different USB Ports**:
   - Use USB 3.0 ports
   - Try different USB controllers
   - Avoid USB hubs if possible

5. **Check Camera Indices**:
   - Edit `src/gui/main_window.py`
   - Line ~337: `logitech_camera_indices = [2, 4, 6]`
   - Change to `[0, 1, 2]` or whatever indices work

### Only 1-2 Cameras Detected

**Problem**: Not all 3 cameras found

**Solutions**:

1. **USB Bandwidth Issue**:
   - Most common problem!
   - 3 cameras at high resolution exceed USB bandwidth

   **Fix**:
   ```python
   # In config/default_config.json:
   {
     "cameras": {
       "default_resolution": [320, 240],  # Lower resolution
       "default_fps": 15  # Lower FPS
     }
   }
   ```

2. **Use Separate USB Controllers**:
   - Connect cameras to different USB root hubs
   - Check with: `lsusb -t` (Linux)

3. **Specific Camera Indices**:
   - Some systems skip indices
   - Try: `[0, 2, 4]` or `[1, 3, 5]`

### Black/No Image from Camera

**Problem**: Camera connected but shows black screen

**Solutions**:

1. **Check Camera Lens Cap**: Remove any lens covers!

2. **Increase Exposure**:
   ```python
   # Low light environment
   # Edit src/core/camera_manager.py
   # Add after line 86:
   self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
   ```

3. **Test Camera Separately**:
   ```python
   import cv2
   cap = cv2.VideoCapture(0)  # Try 0, 1, 2, etc.
   ret, frame = cap.read()
   if ret:
       cv2.imwrite('test.jpg', frame)
   ```

### Low Frame Rate (< 10 FPS)

**Problem**: Slow camera capture

**Solutions**:

1. **Reduce Resolution**:
   - Camera Panel or config file
   - Try 320x240 or 640x480

2. **Reduce Number of Cameras**:
   - Temporarily use 2 cameras
   - Check if performance improves

3. **Check CPU Usage**:
   - Too many background apps
   - Close unnecessary programs

4. **USB 2.0 vs 3.0**:
   - Use USB 3.0 ports (blue connectors)
   - USB 2.0 is limited to ~480 Mbps

---

## Calibration Issues

### Chessboard Not Detected

**Symptoms**: "Chessboard Not Detected" message, no green corners

**Solutions**:

1. **Verify Pattern Size**:
   - Default: 9×6 (9 columns, 6 rows of internal corners)
   - Check `config/default_config.json`:
     ```json
     "calibration": {
       "chessboard_size": [9, 6]
     }
     ```

2. **Improve Lighting**:
   - Use bright, even lighting
   - Avoid shadows on pattern
   - No glare or reflections

3. **Pattern Quality**:
   - Print clearly (not blurry)
   - Mount on flat surface (cardboard/foam)
   - Ensure pattern is flat, not wrinkled

4. **Distance and Angle**:
   - Hold pattern closer (fill 50-80% of frame)
   - Keep pattern perpendicular (not too tilted)
   - Pattern must be fully visible

5. **Camera Focus**:
   - Some cameras have fixed focus
   - Ensure pattern is in focus range
   - Try different distances

### High Reprojection Error (> 1.0 px)

**Problem**: Poor calibration quality

**Solutions**:

1. **Capture More Images**:
   - Use 30-50 images instead of 20
   - More views = better calibration

2. **Better Image Variety**:
   - Vary angles more (tilted, rotated)
   - Include near and far views
   - Cover all parts of frame

3. **Check Pattern Accuracy**:
   - Measure actual square size
   - Update `square_size` in config
   - Use high-quality printed pattern

4. **Discard Poor Images**:
   - Click "Reset" and try again
   - Only capture when pattern is clearly detected
   - Avoid motion blur

### Stereo Calibration Fails

**Problem**: "Stereo calibration failed" or very high error

**Solutions**:

1. **Check Intrinsic Calibrations**:
   - Both cameras must be calibrated first
   - Errors should be < 0.5 px each

2. **Synchronized Captures**:
   - Both cameras must see same pattern
   - Position pattern so both can see it
   - Capture 20+ synchronized views

3. **Camera Separation**:
   - Cameras too close or too far
   - Ideal: 15-30 cm apart
   - Closer for small objects, farther for rooms

4. **Reset and Retry**:
   - Sometimes helps to recalibrate intrinsics
   - Try different camera pair (0-2 instead of 0-1)

---

## Performance Problems

### Application Slow/Laggy

**Problem**: UI freezes, slow response

**Solutions**:

1. **Reduce Point Cloud Size**:
   - Point Cloud tab > Max Points: 50000
   - Enable voxel downsampling: 0.02

2. **Lower Camera Resolution**:
   ```json
   "cameras": {
     "default_resolution": [320, 240]
   }
   ```

3. **Disable Features**:
   - Turn off SLAM if not needed
   - Disable occupancy mapping
   - Reduce stereo quality

4. **Check System Resources**:
   ```bash
   # Linux:
   top
   # Look for high CPU/memory usage

   # Windows: Task Manager
   # macOS: Activity Monitor
   ```

### High CPU Usage (> 80%)

**Problem**: CPU maxed out

**Solutions**:

1. **Processing Workers**:
   - Each worker is a separate thread
   - Normal to see 100-300% CPU (multi-core)

2. **Optimize Settings**:
   - Use Block Matching instead of SGBM
   - Reduce num_disparities: 64 instead of 128
   - Lower FPS: 15 instead of 30

3. **Background Processes**:
   - Close browser tabs
   - Stop other intensive apps

### Out of Memory Errors

**Problem**: "MemoryError" or system freeze

**Solutions**:

1. **Reduce Point Cloud Size**:
   - Max points: 50000 or less
   - Enable downsampling

2. **Limit SLAM Map Points**:
   - SLAM accumulates points over time
   - Reset SLAM periodically
   - Reduce num_features: 500

3. **Close and Restart**:
   - Memory leaks may accumulate
   - Restart application every 30 minutes

4. **Upgrade RAM**:
   - 8GB is minimum
   - 16GB+ recommended for long sessions

---

## SLAM Issues

### SLAM Won't Enable

**Symptoms**: Warning "SLAM Not Configured" or "Please calibrate camera 0"

**Solution**:
1. Camera 0 must be intrinsically calibrated first
2. Go to Calibration > Calibrate Intrinsic
3. Select Camera 0
4. Complete calibration (20+ images)
5. Try enabling SLAM again

### No Trajectory Appearing

**Problem**: SLAM enabled but no red line visible

**Solutions**:

1. **Check View Mode**:
   - Switch to "SLAM Trajectory" mode
   - Dropdown at top of visualization panel

2. **Initialization**:
   - SLAM needs 2+ frames to start
   - Move camera slowly
   - Wait 5-10 seconds

3. **Feature Detection**:
   - Scene must have visual features (texture)
   - White walls won't work
   - Try textured objects or posters

4. **Check Status**:
   - SLAM tab should show "Status: Active"
   - Should show # poses and # points

### SLAM Trajectory Drifts

**Problem**: Path curves incorrectly or drifts off

**Solutions**:

1. **Normal Behavior**:
   - Monocular SLAM always drifts without loop closure
   - No absolute scale (relative only)

2. **Improve Feature Quality**:
   - Use SIFT instead of ORB (more accurate)
   - Increase num_features: 2000

3. **Smooth Motion**:
   - Move camera slowly and smoothly
   - Avoid rapid rotations
   - Maintain visual overlap between frames

4. **Good Lighting**:
   - Consistent, bright lighting
   - Avoid moving shadows

### SLAM Crashes or Fails

**Problem**: "SLAM Error" messages

**Solutions**:

1. **Check Logs**:
   - Look in `logs/` directory
   - Check error messages

2. **Feature Detector**:
   - Try different detector (ORB, SIFT, AKAZE)
   - SIFT is most robust but slower

3. **Reduce Features**:
   - Lower num_features to 500
   - Less computational load

4. **Reset SLAM**:
   - Disable and re-enable SLAM
   - Clears accumulated state

---

## Visualization Problems

### 3D View is Black

**Problem**: No point cloud visible

**Solutions**:

1. **Check Processing**:
   - Is "Start" button activated?
   - Are frames being captured?

2. **Check Point Cloud**:
   - Status bar should show "Points: > 0"
   - If 0 points, stereo matching failed

3. **Reset View**:
   - Click "Reset View" button
   - Camera might be pointing away

4. **Check Visibility**:
   - Some modes hide point cloud
   - Try "Point Cloud" mode

### Points Too Small/Large

**Problem**: Can't see points or they're huge

**Solution**:
- Zoom in/out with mouse wheel
- Reset view button
- Point size is automatic based on distance

### Visualization Freezes

**Problem**: 3D view stops updating

**Solutions**:

1. **Too Many Points**:
   - Reduce max_points to 30000
   - Enable downsampling

2. **GPU/Graphics Driver**:
   - Update graphics drivers
   - Reduce visualization quality

3. **Restart Application**:
   - Sometimes helps clear state

---

## Export Errors

### "No point cloud available to export"

**Problem**: Export fails because no data

**Solution**:
1. Start processing first
2. Wait for point cloud to generate
3. Status bar should show "Points: > 0"
4. Try export again

### Mesh Export Fails

**Problem**: "Failed to generate mesh" error

**Solutions**:

1. **Too Few Points**:
   - Need at least 10,000 points
   - Capture more views

2. **Poisson Reconstruction**:
   - Requires dense, clean point cloud
   - Enable filtering first
   - Try alpha shapes instead (future feature)

3. **Open3D Version**:
   - Update Open3D: `pip install --upgrade open3d`
   - Some versions have mesh bugs

### Export Path Errors

**Problem**: "Permission denied" or "Path not found"

**Solution**:
1. Check `exports/` directory exists
2. Check write permissions
3. Try different location
4. On Windows, avoid special characters in path

---

## System Crashes

### Application Won't Start

**Problem**: Crash on launch or immediate exit

**Solutions**:

1. **Check Dependencies**:
   ```bash
   python -c "import PyQt6, cv2, open3d"
   # Should run without errors
   ```

2. **Check Logs**:
   ```bash
   cat logs/latest.log
   # Or on Windows: type logs\latest.log
   ```

3. **Try Safe Mode**:
   ```bash
   # Edit config/default_config.json
   {
     "cameras": {
       "num_cameras": 0  # Don't auto-connect
     }
   }
   # Then connect manually
   ```

4. **Clean Start**:
   ```bash
   # Remove config and try again
   rm -rf ~/.cache/3d_reconstruction
   ```

### Random Crashes During Use

**Problem**: Application crashes unexpectedly

**Solutions**:

1. **Check Logs**:
   - Look in `logs/` for error messages
   - Note what action caused crash

2. **Memory**:
   - Monitor RAM usage
   - Reduce point cloud size
   - Restart application periodically

3. **Worker Threads**:
   - Sometimes thread synchronization issues
   - Try disabling SLAM temporarily
   - Restart application

4. **Update Dependencies**:
   ```bash
   pip install --upgrade PyQt6 opencv-python open3d
   ```

### Segmentation Fault (Linux)

**Problem**: "Segmentation fault (core dumped)"

**Solutions**:

1. **OpenCV Build**:
   - May be incompatible build
   - Try: `pip install opencv-python-headless`

2. **Graphics Drivers**:
   ```bash
   # Update drivers
   sudo apt update && sudo apt upgrade
   ```

3. **Qt Platform**:
   ```bash
   export QT_QPA_PLATFORM=xcb
   python src/main.py
   ```

---

## Getting More Help

### Enable Debug Logging

Edit `config/default_config.json`:
```json
{
  "logging": {
    "level": "DEBUG",
    "save_to_file": true
  }
}
```

This will create detailed logs in `logs/` directory.

### Check System Info

```bash
# Python version
python --version

# Package versions
pip list | grep -E "PyQt6|opencv|open3d|numpy"

# System info (Linux)
uname -a
```

### Report Bug

If you can't solve the issue:

1. Check existing issues: https://github.com/Sherin-SEF-AI/Multi-Camera-3D-Scene-Reconstruction-Mapping-System/issues
2. Create new issue with:
   - OS and Python version
   - Full error message
   - Steps to reproduce
   - Relevant log files
   - Screenshots if applicable

---

## Common Solutions Quick Reference

| Problem | Quick Fix |
|---------|-----------|
| Cameras not detected | Check permissions, try `[0,1,2]` indices |
| Low FPS | Reduce resolution to 320x240 |
| Chessboard not detected | Improve lighting, print clearer pattern |
| High calibration error | Capture more varied images (30+) |
| Application slow | Reduce max_points to 50000 |
| SLAM won't enable | Calibrate camera 0 first |
| No trajectory | Switch to "SLAM Trajectory" view mode |
| Memory errors | Reduce max_points, restart app |
| Export fails | Start processing first |
| Crashes | Update dependencies, check logs |

---

## Still Having Issues?

1. Check documentation:
   - `docs/FEATURES.md` - Complete feature guide
   - `docs/QUICKSTART.md` - Setup instructions
   - `docs/CALIBRATION_GUIDE.md` - Calibration help

2. Search GitHub issues

3. Create new issue with details

4. Join community discussions

---

**Last Updated**: 2024
**Version**: 1.0.0
