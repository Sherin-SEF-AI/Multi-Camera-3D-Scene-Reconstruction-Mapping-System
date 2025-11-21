"""
SLAM Worker Thread
Handles background Visual SLAM processing for PyQt6 GUI
"""

from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import time
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.slam import VisualSLAM


class SLAMWorker(QThread):
    """Worker thread for Visual SLAM processing"""

    # Signals
    pose_updated = pyqtSignal(np.ndarray)  # Current camera pose (4x4 transformation)
    trajectory_updated = pyqtSignal(np.ndarray)  # Trajectory points (Nx3)
    map_points_updated = pyqtSignal(np.ndarray, np.ndarray)  # Map points (Nx3) and colors (Nx3)
    slam_stats_updated = pyqtSignal(dict)  # Statistics (num_poses, num_points, etc.)
    error_occurred = pyqtSignal(str)  # Error message

    def __init__(self, slam_system: VisualSLAM):
        """
        Initialize SLAM worker

        Args:
            slam_system: VisualSLAM instance
        """
        super().__init__()
        self.slam = slam_system

        self.running = False
        self.processing_enabled = False

        # Current frame data
        self.current_frame: Optional[np.ndarray] = None
        self.frame_timestamp = 0.0

        # Update rate control
        self.last_emit_time = 0.0
        self.emit_interval = 0.5  # Emit updates every 500ms

    def set_frame(self, frame: np.ndarray, timestamp: float = None):
        """
        Set current frame for SLAM processing

        Args:
            frame: Input image frame
            timestamp: Frame timestamp (defaults to current time)
        """
        self.current_frame = frame.copy()
        self.frame_timestamp = timestamp if timestamp is not None else time.time()

    def enable_processing(self, enabled: bool):
        """Enable or disable SLAM processing"""
        self.processing_enabled = enabled

        if not enabled:
            # Reset SLAM when disabled
            self.slam.reset()
            self.logger_info("SLAM system reset")

    def reset_slam(self):
        """Reset SLAM system"""
        self.slam.reset()
        self.emit_updates()  # Emit empty updates

    def run(self):
        """Main SLAM processing loop"""
        self.running = True

        while self.running:
            if not self.processing_enabled or self.current_frame is None:
                time.sleep(0.05)
                continue

            try:
                # Process frame through SLAM
                success = self.slam.process_frame(self.current_frame, self.frame_timestamp)

                if success:
                    # Emit current pose
                    current_pose = self.slam.current_pose
                    self.pose_updated.emit(current_pose)

                    # Emit trajectory and map points periodically
                    current_time = time.time()
                    if current_time - self.last_emit_time > self.emit_interval:
                        self.emit_updates()
                        self.last_emit_time = current_time

                # Control processing rate
                time.sleep(0.033)  # ~30 Hz

            except Exception as e:
                self.error_occurred.emit(f"SLAM Error: {str(e)}")
                time.sleep(0.1)

    def emit_updates(self):
        """Emit trajectory and map points updates"""
        try:
            # Get trajectory
            trajectory = self.slam.get_trajectory()
            if len(trajectory) > 0:
                self.trajectory_updated.emit(trajectory)

            # Get map points
            map_points = self.slam.get_map_points_array()
            if len(map_points) > 0:
                colors = self.slam.get_map_colors()
                if colors is not None:
                    self.map_points_updated.emit(map_points, colors)

            # Emit statistics
            stats = {
                'num_poses': len(self.slam.poses),
                'num_map_points': self.slam.get_num_map_points(),
                'current_position': self.slam.get_current_position().tolist()
            }
            self.slam_stats_updated.emit(stats)

        except Exception as e:
            self.error_occurred.emit(f"SLAM Update Error: {str(e)}")

    def logger_info(self, message: str):
        """Log info message (placeholder)"""
        print(f"[SLAM Worker] {message}")

    def stop(self):
        """Stop the worker thread"""
        self.running = False
        self.wait()
