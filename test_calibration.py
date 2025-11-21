#!/usr/bin/env python3
"""
Diagnostic script to test calibration setup
Run this to check if your system is ready for calibration
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test if all required modules can be imported"""
    print("="* 60)
    print("Testing Imports...")
    print("="* 60)

    tests = {
        "PyQt6": lambda: __import__("PyQt6"),
        "OpenCV (cv2)": lambda: __import__("cv2"),
        "NumPy": lambda: __import__("numpy"),
        "Open3D": lambda: __import__("open3d"),
        "CameraManager": lambda: __import__("core.camera_manager"),
        "CalibrationManager": lambda: __import__("core.calibration"),
        "Calibration Dialogs": lambda: __import__("gui.dialogs.calibration_dialog"),
    }

    all_passed = True
    for name, test_fn in tests.items():
        try:
            test_fn()
            print(f"✓ {name:30s} OK")
        except Exception as e:
            print(f"✗ {name:30s} FAILED: {e}")
            all_passed = False

    print()
    return all_passed


def test_cameras():
    """Test camera detection"""
    print("="* 60)
    print("Testing Camera Detection...")
    print("="* 60)

    try:
        import cv2

        found_cameras = []
        # Test indices 0-10
        for i in range(11):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    h, w = frame.shape[:2]
                    found_cameras.append((i, w, h))
                    print(f"✓ Camera {i}: Found ({w}x{h})")
                cap.release()

        print()
        if len(found_cameras) == 0:
            print("✗ No cameras detected!")
            print("\nTroubleshooting:")
            print("- Ensure cameras are plugged in")
            print("- Check if other apps are using cameras (close Chrome, Zoom, etc.)")
            print("- On Linux, check permissions: ls -l /dev/video*")
            return False
        elif len(found_cameras) < 3:
            print(f"⚠ Only {len(found_cameras)} camera(s) detected (need 3 for full system)")
            print("Calibration will still work with 1+ cameras")
            return True
        else:
            print(f"✓ Found {len(found_cameras)} cameras - Good!")
            return True

    except Exception as e:
        print(f"✗ Error testing cameras: {e}")
        return False


def test_calibration_manager():
    """Test CalibrationManager initialization"""
    print("="* 60)
    print("Testing CalibrationManager...")
    print("="* 60)

    try:
        from core.calibration import CalibrationManager

        calib_mgr = CalibrationManager()
        print(f"✓ CalibrationManager created")
        print(f"  Chessboard size: {calib_mgr.chessboard_size}")
        print(f"  Square size: {calib_mgr.square_size} mm")
        print()
        return True

    except Exception as e:
        print(f"✗ Error creating CalibrationManager: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chessboard_pattern():
    """Check if chessboard pattern file exists"""
    print("="* 60)
    print("Testing Chessboard Pattern...")
    print("="* 60)

    pattern_file = Path(__file__).parent / "docs" / "chessboard_9x6.pdf"

    if pattern_file.exists():
        print(f"✓ Chessboard pattern found: {pattern_file}")
        print("  Print this file for calibration!")
        print()
        return True
    else:
        print(f"⚠ Chessboard pattern not found: {pattern_file}")
        print("  You can use any 9x6 chessboard pattern")
        print()
        return False


def main():
    """Run all diagnostic tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "CALIBRATION DIAGNOSTIC TOOL" + " "*21 + "║")
    print("╚" + "="*58 + "╝")
    print()

    results = {}

    results['imports'] = test_imports()
    results['cameras'] = test_cameras()
    results['calibration_manager'] = test_calibration_manager()
    results['chessboard'] = test_chessboard_pattern()

    # Summary
    print("="* 60)
    print("SUMMARY")
    print("="* 60)

    if all(results.values()):
        print("✓ All tests passed! Your system is ready for calibration.")
        print("\nTo start calibration:")
        print("1. Run: python src/main.py")
        print("2. Click 'Connect Cameras'")
        print("3. Go to: Calibration > Calibrate Intrinsic")
        print("4. Follow the on-screen instructions")
    elif not results['imports']:
        print("✗ Missing dependencies. Please install requirements:")
        print("\n  pip install -r requirements.txt")
    elif not results['cameras']:
        print("✗ Camera detection failed. Check troubleshooting tips above.")
    else:
        print("⚠ Some tests failed, but you may still be able to calibrate.")
        print("  Check the details above.")

    print()


if __name__ == "__main__":
    main()
