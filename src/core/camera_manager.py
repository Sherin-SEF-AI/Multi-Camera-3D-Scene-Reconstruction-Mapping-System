"""
Camera Management Module
Handles detection, connection, and frame capture from multiple USB webcams
"""

import cv2
import numpy as np
import threading
import time
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from queue import Queue


@dataclass
class CameraInfo:
    """Information about a camera device"""
    index: int
    name: str
    resolution: Tuple[int, int]
    fps: int
    is_active: bool = False
    last_frame_time: float = 0.0


class Camera:
    """Represents a single camera with frame capture capabilities"""

    def __init__(self, index: int, resolution: Tuple[int, int] = (640, 480), fps: int = 30):
        """
        Initialize camera

        Args:
            index: Camera device index
            resolution: Desired resolution (width, height)
            fps: Desired frames per second
        """
        self.index = index
        self.resolution = resolution
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_active = False
        self.frame_buffer = Queue(maxsize=5)
        self.latest_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        self.capture_thread: Optional[threading.Thread] = None
        self.stop_capture = threading.Event()
        self.frame_count = 0
        self.last_frame_time = 0.0
        self.name = f"Camera {index}"

        # Camera properties
        self.exposure = None
        self.brightness = None
        self.contrast = None

    def open(self) -> bool:
        """
        Open camera connection

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"[Camera {self.index}] Opening camera...")
            self.cap = cv2.VideoCapture(self.index)

            if not self.cap.isOpened():
                print(f"[Camera {self.index}] Failed to open - VideoCapture.isOpened() returned False")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

            print(f"[Camera {self.index}] Opened successfully: {actual_width}x{actual_height} @ {actual_fps} FPS")

            self.resolution = (actual_width, actual_height)
            self.fps = actual_fps

            # Read initial properties
            self.exposure = self.cap.get(cv2.CAP_PROP_EXPOSURE)
            self.brightness = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
            self.contrast = self.cap.get(cv2.CAP_PROP_CONTRAST)

            self.is_active = True

            # Try to read one test frame
            ret, test_frame = self.cap.read()
            if ret:
                print(f"[Camera {self.index}] Test frame read successful: {test_frame.shape}")
            else:
                print(f"[Camera {self.index}] WARNING: Test frame read failed!")

            return True

        except Exception as e:
            print(f"[Camera {self.index}] Exception opening camera: {e}")
            return False

    def close(self) -> None:
        """Close camera connection"""
        self.stop_capture_thread()

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.is_active = False

    def start_capture_thread(self) -> None:
        """Start background frame capture thread"""
        if self.capture_thread is not None and self.capture_thread.is_alive():
            return

        self.stop_capture.clear()
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()

    def stop_capture_thread(self) -> None:
        """Stop background frame capture thread"""
        self.stop_capture.set()

        if self.capture_thread is not None:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None

    def _capture_loop(self) -> None:
        """Background loop for continuous frame capture"""
        print(f"[Camera {self.index}] Capture loop started")
        first_frame_captured = False

        while not self.stop_capture.is_set() and self.is_active:
            frame = self.read_frame()
            if frame is not None:
                if not first_frame_captured:
                    print(f"[Camera {self.index}] First frame captured: {frame.shape}")
                    first_frame_captured = True

                with self.frame_lock:
                    self.latest_frame = frame.copy()
                    self.last_frame_time = time.time()
                    self.frame_count += 1

            # Small delay to control capture rate
            time.sleep(1.0 / self.fps)

        print(f"[Camera {self.index}] Capture loop ended")

    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a single frame from camera

        Returns:
            Frame as numpy array or None if failed
        """
        if self.cap is None or not self.is_active:
            return None

        try:
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                # Only print first few failures to avoid spam
                if not hasattr(self, '_read_failures'):
                    self._read_failures = 0
                self._read_failures += 1
                if self._read_failures <= 5:
                    print(f"[Camera {self.index}] Failed to read frame (attempt {self._read_failures})")
            return None

        except Exception as e:
            print(f"[Camera {self.index}] Exception reading frame: {e}")
            return None

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame from the buffer

        Returns:
            Latest frame or None if not available
        """
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
            return None

    def set_resolution(self, width: int, height: int) -> bool:
        """
        Change camera resolution

        Args:
            width: New width
            height: New height

        Returns:
            True if successful
        """
        if self.cap is None:
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Verify change
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.resolution = (actual_width, actual_height)
        return (actual_width == width and actual_height == height)

    def set_fps(self, fps: int) -> bool:
        """
        Change camera FPS

        Args:
            fps: New FPS value

        Returns:
            True if successful
        """
        if self.cap is None:
            return False

        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        return True

    def set_exposure(self, value: float) -> bool:
        """Set camera exposure"""
        if self.cap is None:
            return False

        self.cap.set(cv2.CAP_PROP_EXPOSURE, value)
        self.exposure = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        return True

    def set_brightness(self, value: float) -> bool:
        """Set camera brightness"""
        if self.cap is None:
            return False

        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)
        self.brightness = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
        return True

    def set_contrast(self, value: float) -> bool:
        """Set camera contrast"""
        if self.cap is None:
            return False

        self.cap.set(cv2.CAP_PROP_CONTRAST, value)
        self.contrast = self.cap.get(cv2.CAP_PROP_CONTRAST)
        return True

    def get_info(self) -> CameraInfo:
        """Get camera information"""
        return CameraInfo(
            index=self.index,
            name=self.name,
            resolution=self.resolution,
            fps=self.fps,
            is_active=self.is_active,
            last_frame_time=self.last_frame_time
        )


class CameraManager:
    """Manages multiple cameras for synchronized capture"""

    def __init__(self, num_cameras: int = 3, resolution: Tuple[int, int] = (640, 480), fps: int = 30):
        """
        Initialize camera manager

        Args:
            num_cameras: Number of cameras to manage
            resolution: Default resolution for all cameras
            fps: Default FPS for all cameras
        """
        self.num_cameras = num_cameras
        self.default_resolution = resolution
        self.default_fps = fps
        self.cameras: List[Optional[Camera]] = [None] * num_cameras
        self.active_camera_indices: List[int] = []

    def detect_cameras(self, max_index: int = 10) -> List[int]:
        """
        Detect available cameras

        Args:
            max_index: Maximum camera index to check

        Returns:
            List of available camera indices
        """
        available = []

        for i in range(max_index):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()

        return available

    def auto_connect(self) -> int:
        """
        Auto-detect and connect to available cameras

        Returns:
            Number of cameras successfully connected
        """
        available_indices = self.detect_cameras()

        if len(available_indices) < self.num_cameras:
            print(f"Warning: Found only {len(available_indices)} cameras, expected {self.num_cameras}")

        connected = 0
        for i, cam_index in enumerate(available_indices[:self.num_cameras]):
            if self.connect_camera(i, cam_index):
                connected += 1

        return connected

    def connect_camera(self, slot: int, device_index: int) -> bool:
        """
        Connect a camera to a specific slot

        Args:
            slot: Camera slot (0, 1, 2)
            device_index: Device index to connect

        Returns:
            True if successful
        """
        if slot >= self.num_cameras:
            return False

        # Close existing camera in slot
        if self.cameras[slot] is not None:
            self.cameras[slot].close()

        # Create and open new camera
        camera = Camera(device_index, self.default_resolution, self.default_fps)

        if camera.open():
            self.cameras[slot] = camera
            camera.start_capture_thread()

            if slot not in self.active_camera_indices:
                self.active_camera_indices.append(slot)

            print(f"Connected camera {device_index} to slot {slot}")
            return True
        else:
            return False

    def disconnect_camera(self, slot: int) -> None:
        """
        Disconnect camera from slot

        Args:
            slot: Camera slot to disconnect
        """
        if slot < self.num_cameras and self.cameras[slot] is not None:
            self.cameras[slot].close()
            self.cameras[slot] = None

            if slot in self.active_camera_indices:
                self.active_camera_indices.remove(slot)

    def disconnect_all(self) -> None:
        """Disconnect all cameras"""
        for i in range(self.num_cameras):
            self.disconnect_camera(i)

    def get_frames(self) -> List[Optional[np.ndarray]]:
        """
        Get latest frames from all cameras

        Returns:
            List of frames (None for disconnected cameras)
        """
        frames = []
        for camera in self.cameras:
            if camera is not None and camera.is_active:
                frames.append(camera.get_latest_frame())
            else:
                frames.append(None)
        return frames

    def capture_synchronized(self) -> List[Optional[np.ndarray]]:
        """
        Capture synchronized frames from all active cameras

        Returns:
            List of frames captured at approximately the same time
        """
        frames = [None] * self.num_cameras

        # Trigger frame capture on all cameras
        for i, camera in enumerate(self.cameras):
            if camera is not None and camera.is_active:
                frames[i] = camera.read_frame()

        return frames

    def get_camera(self, slot: int) -> Optional[Camera]:
        """Get camera at specific slot"""
        if slot < self.num_cameras:
            return self.cameras[slot]
        return None

    def get_camera_info(self, slot: int) -> Optional[CameraInfo]:
        """Get information about camera in slot"""
        camera = self.get_camera(slot)
        if camera is not None:
            return camera.get_info()
        return None

    def get_all_info(self) -> List[Optional[CameraInfo]]:
        """Get information about all cameras"""
        return [cam.get_info() if cam is not None else None for cam in self.cameras]

    def is_camera_active(self, slot: int) -> bool:
        """Check if camera in slot is active"""
        camera = self.get_camera(slot)
        return camera is not None and camera.is_active

    def get_active_count(self) -> int:
        """Get number of active cameras"""
        return len(self.active_camera_indices)

    def __del__(self):
        """Cleanup on destruction"""
        self.disconnect_all()
