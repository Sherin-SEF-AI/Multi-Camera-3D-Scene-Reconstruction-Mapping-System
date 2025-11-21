"""
Camera Worker Thread
Handles background camera frame capture for PyQt6 GUI
"""

from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import time
from typing import Optional


class CameraWorker(QThread):
    """Worker thread for continuous camera frame capture"""

    # Signals
    frame_ready = pyqtSignal(int, np.ndarray)  # (camera_id, frame)
    fps_updated = pyqtSignal(int, float)  # (camera_id, fps)
    error_occurred = pyqtSignal(int, str)  # (camera_id, error_message)

    def __init__(self, camera_id: int, camera_manager):
        """
        Initialize camera worker

        Args:
            camera_id: Camera slot ID
            camera_manager: CameraManager instance
        """
        super().__init__()
        self.camera_id = camera_id
        self.camera_manager = camera_manager
        self.running = False

        # FPS calculation
        self.frame_times = []
        self.fps_update_interval = 1.0  # Update FPS every second

    def run(self):
        """Main worker loop"""
        self.running = True
        last_fps_update = time.time()
        frame_count = 0
        first_frame = True

        print(f"[CameraWorker {self.camera_id}] Started")

        while self.running:
            try:
                # Get camera
                camera = self.camera_manager.get_camera(self.camera_id)

                if camera is None or not camera.is_active:
                    time.sleep(0.1)
                    continue

                # Get latest frame
                frame = camera.get_latest_frame()

                if frame is not None:
                    if first_frame:
                        print(f"[CameraWorker {self.camera_id}] Got first frame: {frame.shape}")
                        first_frame = False

                    frame_count += 1
                    # Emit frame
                    self.frame_ready.emit(self.camera_id, frame)

                    # Calculate FPS
                    current_time = time.time()
                    self.frame_times.append(current_time)

                    # Remove old frame times (older than 1 second)
                    self.frame_times = [t for t in self.frame_times if current_time - t < 1.0]

                    # Update FPS periodically
                    if current_time - last_fps_update >= self.fps_update_interval:
                        fps = len(self.frame_times)
                        self.fps_updated.emit(self.camera_id, fps)
                        last_fps_update = current_time

                # Small delay to control update rate
                time.sleep(1.0 / 60.0)  # Target 60 Hz update rate

            except Exception as e:
                self.error_occurred.emit(self.camera_id, str(e))
                time.sleep(0.1)

    def stop(self):
        """Stop the worker thread"""
        self.running = False
        self.wait()
