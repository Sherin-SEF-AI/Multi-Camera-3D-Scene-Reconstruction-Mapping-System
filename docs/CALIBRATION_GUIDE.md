# Camera Calibration Guide

Proper camera calibration is essential for accurate 3D reconstruction. This guide will walk you through the complete calibration process for the Multi-Camera 3D Reconstruction System.

## Table of Contents

1. [Overview](#overview)
2. [Preparing the Calibration Pattern](#preparing-the-calibration-pattern)
3. [Intrinsic Calibration](#intrinsic-calibration)
4. [Stereo Calibration](#stereo-calibration)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Overview

The calibration process consists of two main steps:

1. **Intrinsic Calibration**: Determines internal camera parameters (focal length, principal point, distortion coefficients) for each camera individually.
2. **Stereo Calibration**: Determines the relative position and orientation between camera pairs for depth estimation.

## Preparing the Calibration Pattern

### Chessboard Pattern Specifications

The default configuration uses a **9x6 chessboard pattern** with **25mm squares**.

#### Creating a Calibration Pattern

**Option 1: Download Pre-made Pattern**
- Download from: https://docs.opencv.org/4.x/pattern.png
- Print on A4 or Letter paper

**Option 2: Generate Custom Pattern**
```python
import cv2
import numpy as np

# Generate 9x6 chessboard
chessboard_size = (9, 6)
square_size_mm = 25

# Create pattern (white and black squares)
square_size_pixels = 100  # pixels per square
width = chessboard_size[0] * square_size_pixels
height = chessboard_size[1] * square_size_pixels

pattern = np.zeros((height, width), dtype=np.uint8)
for i in range(chessboard_size[1]):
    for j in range(chessboard_size[0]):
        if (i + j) % 2 == 0:
            pattern[i*square_size_pixels:(i+1)*square_size_pixels,
                   j*square_size_pixels:(j+1)*square_size_pixels] = 255

cv2.imwrite('calibration_pattern.png', pattern)
```

#### Printing Guidelines

1. **Print at actual size** (100% scale, no fit-to-page)
2. **Use high-quality printer** for sharp edges
3. **Print on rigid surface** or mount on stiff board
4. **Measure actual square size** after printing (should be 25mm)
5. **Ensure pattern is flat** without wrinkles or curves

### Verifying Pattern Quality

- Edges should be sharp and clear
- No smudging or blurring
- Pattern should be completely flat
- Squares should be perfectly aligned

## Intrinsic Calibration

Intrinsic calibration determines each camera's internal parameters.

### Step 1: Start Calibration Process

1. Launch the application
2. Ensure all 3 cameras are connected and active
3. Go to **Calibration > Calibrate Intrinsic**

### Step 2: Capture Calibration Images

You need to capture **20-30 images per camera** from various angles and distances.

#### Camera Coverage Guidelines

Capture images with the pattern at:
- **Different angles** (0°, 15°, 30°, 45° tilt in all directions)
- **Different distances** (near, medium, far)
- **Different positions** (center, corners, edges of frame)
- **Different orientations** (horizontal, vertical, diagonal)

#### Image Capture Tips

```
✓ Good Image Checklist:
  - Pattern fully visible in frame
  - All corners detected (green overlay visible)
  - Good lighting (no glare or shadows)
  - Pattern flat and not blurred
  - Covers different areas of the frame

✗ Bad Images to Avoid:
  - Pattern partially out of frame
  - Motion blur
  - Glare on pattern
  - Poor lighting
  - Only capturing from similar positions
```

### Step 3: Automatic Processing

Once sufficient images are captured:
1. System automatically detects chessboard corners
2. Computes intrinsic parameters:
   - Camera matrix (fx, fy, cx, cy)
   - Distortion coefficients (k1, k2, p1, p2, k3)
3. Calculates reprojection error

### Step 4: Verify Calibration Quality

**Reprojection Error Guidelines:**
- **Excellent**: < 0.3 pixels
- **Good**: 0.3 - 0.5 pixels
- **Acceptable**: 0.5 - 1.0 pixels
- **Poor**: > 1.0 pixels (recalibrate)

### Step 5: Save Calibration

1. Go to **Calibration > Save Calibration**
2. Enter a descriptive name (e.g., `calibration_20241121_cameras_123.json`)
3. Calibration saved to `calibrations/` directory

## Stereo Calibration

Stereo calibration determines the relative position between camera pairs.

### Prerequisites

- All cameras must be intrinsically calibrated first
- Cameras should remain in fixed positions (mounted/stationary)

### Step 1: Start Stereo Calibration

1. Go to **Calibration > Calibrate Stereo**
2. Select camera pair (e.g., Camera 0 + Camera 1)

### Step 2: Synchronized Capture

For stereo calibration, you must capture **synchronized images** where the pattern is visible in both cameras simultaneously.

#### Setup Guidelines

1. **Position pattern** so both cameras can see it clearly
2. **Maintain synchronization** - pattern must be static during capture
3. **Capture 20-30 synchronized pairs** from various angles
4. **Ensure overlap** - pattern visible in both camera views

### Step 3: Compute Stereo Parameters

The system computes:
- **Rotation matrix (R)**: Rotation between cameras
- **Translation vector (T)**: Relative position
- **Essential matrix (E)**: Fundamental geometric relationship
- **Fundamental matrix (F)**: Epipolar geometry
- **Baseline**: Physical distance between cameras (in mm)

### Step 4: Verify Stereo Calibration

Check the following:
- Baseline should match physical camera separation
- Reprojection error should be low (< 1.0 pixels)
- Rectified images should have aligned epipolar lines

### Step 5: Generate Rectification Maps

System automatically generates:
- Rectification transformation matrices
- Projection matrices for 3D reconstruction
- Disparity-to-depth mapping matrix (Q)

## Troubleshooting

### Pattern Not Detected

**Problem**: Green corner overlay not appearing

**Solutions**:
- Improve lighting (avoid glare and shadows)
- Move pattern closer to camera
- Ensure pattern is completely flat
- Clean camera lens
- Adjust camera focus (if manual focus available)
- Verify pattern is correct size (9x6, not 6x9)

### High Reprojection Error

**Problem**: Reprojection error > 1.0 pixels

**Solutions**:
- Capture more images (30-40 instead of 20)
- Increase variety of capture angles
- Remove blurry images
- Ensure pattern is perfectly flat
- Check for lens distortion (clean lens)
- Recalibrate with fresh images

### Stereo Calibration Fails

**Problem**: Cannot compute stereo parameters

**Solutions**:
- Verify both cameras are intrinsically calibrated
- Ensure pattern is visible in BOTH cameras simultaneously
- Check camera synchronization
- Increase number of stereo pairs
- Verify cameras are stationary (not moved during calibration)

### Incorrect Depth Measurements

**Problem**: Depth values don't match reality

**Solutions**:
- Re-measure and verify square size (must be exact)
- Check baseline calculation (should match physical distance)
- Verify camera mounting is rigid (no movement)
- Recalibrate stereo parameters
- Check for lens distortion issues

## Best Practices

### Environment Setup

1. **Lighting**:
   - Use diffuse, even lighting
   - Avoid direct sunlight or harsh shadows
   - No glare on calibration pattern
   - Consistent lighting across all captures

2. **Camera Mounting**:
   - Cameras should be rigidly mounted
   - No movement during or after calibration
   - Stable, vibration-free mounting
   - Consider permanent mounting for repeated use

3. **Pattern Handling**:
   - Mount pattern on rigid board
   - Keep pattern clean and undamaged
   - Store flat to prevent warping
   - Verify measurements periodically

### Calibration Workflow

1. **Initial Calibration**:
   - Calibrate in controlled environment
   - Take time to capture quality images
   - Verify results before proceeding
   - Save calibration with timestamp

2. **Regular Verification**:
   - Re-check calibration if cameras are moved
   - Periodic recalibration (monthly recommended)
   - Keep calibration backups

3. **Multiple Configurations**:
   - Save calibrations for different setups
   - Label calibrations clearly
   - Document camera positions

### Capture Strategy

**For Each Camera (Intrinsic):**
```
Angles: 0°, 15°, 30°, 45° (tilt in X and Y)
Distances: Near (30cm), Medium (60cm), Far (100cm)
Positions: Center, Top, Bottom, Left, Right, Corners
Total: ~25 images per camera
```

**For Stereo Pairs:**
```
Angles: 0°, 15°, 30° (tilt in multiple directions)
Ensure: Pattern visible in BOTH cameras
Overlap: Pattern should cover overlapping region
Total: ~20 synchronized pairs per stereo pair
```

## Advanced Topics

### Custom Pattern Sizes

To use a different pattern size:

1. Modify `config/default_config.json`:
```json
{
  "calibration": {
    "chessboard_size": [10, 7],  // Change to your pattern
    "square_size_mm": 30.0        // Measured square size
  }
}
```

2. Restart application for changes to take effect

### Calibration Quality Metrics

The system provides several quality indicators:

- **Reprojection Error**: Average pixel error (lower is better)
- **Coverage**: How well images cover the field of view
- **Symmetry**: Balance of capture angles
- **Baseline**: Physical distance between stereo cameras

### Automated Calibration

For repeated setups, consider:
- Scripting the calibration process
- Using the API directly
- Batch processing multiple calibrations

## Appendix

### Chessboard Pattern Dimensions

| Pattern | Corners (WxH) | Recommended Size | Square Size |
|---------|---------------|------------------|-------------|
| Default | 9x6           | A4 / Letter      | 25mm        |
| Large   | 11x8          | A3               | 30mm        |
| Small   | 7x5           | A5               | 20mm        |

### Calibration File Format

Calibration files are saved as JSON:

```json
{
  "chessboard_size": [9, 6],
  "square_size": 25.0,
  "intrinsic_calibrations": {
    "0": {
      "camera_matrix": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
      "dist_coeffs": [k1, k2, p1, p2, k3],
      "image_size": [width, height],
      "reprojection_error": 0.245
    }
  },
  "stereo_calibrations": {
    "0_1": {
      "R": [...],
      "T": [...],
      "baseline": 120.5
    }
  }
}
```

### References

- OpenCV Calibration Tutorial: https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html
- Camera Calibration Theory: https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html
- Stereo Vision: https://docs.opencv.org/4.x/dd/d53/tutorial_py_depthmap.html

---

**Last Updated**: 2024
**Version**: 1.0
