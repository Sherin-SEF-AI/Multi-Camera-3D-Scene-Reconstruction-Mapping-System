"""
Processing Worker Thread
Handles background 3D reconstruction processing for PyQt6 GUI
"""

from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import open3d as o3d
import time
from typing import Optional, Dict, Any


class ProcessingWorker(QThread):
    """Worker thread for 3D reconstruction processing"""

    # Signals
    disparity_ready = pyqtSignal(np.ndarray)  # Disparity map
    depth_ready = pyqtSignal(np.ndarray)  # Depth map
    point_cloud_ready = pyqtSignal(object)  # Point cloud (Open3D)
    occupancy_map_ready = pyqtSignal(np.ndarray)  # Occupancy grid visualization
    processing_time = pyqtSignal(float)  # Processing time in ms
    error_occurred = pyqtSignal(str)  # Error message

    def __init__(self, stereo_matcher, point_cloud_processor, occupancy_grid_2d=None):
        """
        Initialize processing worker

        Args:
            stereo_matcher: StereoMatcher instance
            point_cloud_processor: PointCloudProcessor instance
            occupancy_grid_2d: OccupancyGrid2D instance (optional)
        """
        super().__init__()
        self.stereo_matcher = stereo_matcher
        self.point_cloud_processor = point_cloud_processor
        self.occupancy_grid_2d = occupancy_grid_2d

        self.running = False
        self.process_enabled = False

        # Frame data
        self.left_frame: Optional[np.ndarray] = None
        self.right_frame: Optional[np.ndarray] = None
        self.Q_matrix: Optional[np.ndarray] = None
        self.camera_matrix: Optional[np.ndarray] = None

        # Rectification maps
        self.rectify_maps_left = None
        self.rectify_maps_right = None

        # Occupancy mapping enabled
        self.occupancy_enabled = False

    def set_frames(self, left_frame: np.ndarray, right_frame: np.ndarray):
        """
        Set stereo frames for processing

        Args:
            left_frame: Left camera frame
            right_frame: Right camera frame
        """
        self.left_frame = left_frame
        self.right_frame = right_frame

    def set_calibration_data(self, Q_matrix: np.ndarray, camera_matrix: np.ndarray,
                           rectify_maps_left=None, rectify_maps_right=None):
        """
        Set calibration data for processing

        Args:
            Q_matrix: Disparity-to-depth mapping matrix
            camera_matrix: Camera intrinsic matrix
            rectify_maps_left: Rectification maps for left camera
            rectify_maps_right: Rectification maps for right camera
        """
        self.Q_matrix = Q_matrix
        self.camera_matrix = camera_matrix
        self.rectify_maps_left = rectify_maps_left
        self.rectify_maps_right = rectify_maps_right

    def enable_processing(self, enabled: bool):
        """Enable or disable processing"""
        self.process_enabled = enabled

    def enable_occupancy_mapping(self, enabled: bool):
        """Enable or disable occupancy mapping"""
        self.occupancy_enabled = enabled

    def run(self):
        """Main processing loop"""
        self.running = True

        while self.running:
            if not self.process_enabled or self.left_frame is None or self.right_frame is None:
                time.sleep(0.05)
                continue

            try:
                start_time = time.time()

                # Rectify images if maps are available
                if self.rectify_maps_left is not None and self.rectify_maps_right is not None:
                    import cv2
                    left_rect = cv2.remap(
                        self.left_frame,
                        self.rectify_maps_left[0],
                        self.rectify_maps_left[1],
                        cv2.INTER_LINEAR
                    )
                    right_rect = cv2.remap(
                        self.right_frame,
                        self.rectify_maps_right[0],
                        self.rectify_maps_right[1],
                        cv2.INTER_LINEAR
                    )
                else:
                    left_rect = self.left_frame
                    right_rect = self.right_frame

                # Compute disparity
                disparity = self.stereo_matcher.compute_disparity(left_rect, right_rect)

                if disparity is not None:
                    self.disparity_ready.emit(disparity)

                    # Compute depth if Q matrix is available
                    if self.Q_matrix is not None:
                        depth_map = self.stereo_matcher.compute_depth(disparity, self.Q_matrix)

                        if depth_map is not None:
                            self.depth_ready.emit(depth_map)

                            # Generate point cloud if camera matrix is available
                            if self.camera_matrix is not None:
                                pcd = self.point_cloud_processor.create_from_depth(
                                    depth_map,
                                    left_rect,
                                    self.camera_matrix,
                                    max_depth=5000.0
                                )

                                # Filter point cloud
                                if len(pcd.points) > 0:
                                    pcd = self.point_cloud_processor.filter_statistical_outliers(
                                        pcd, nb_neighbors=20, std_ratio=2.0
                                    )

                                    # Downsample if too many points
                                    if len(pcd.points) > 100000:
                                        pcd = self.point_cloud_processor.downsample_voxel(
                                            pcd, voxel_size=0.01
                                        )

                                    self.point_cloud_ready.emit(pcd)

                                    # Update occupancy grid if enabled
                                    if self.occupancy_enabled and self.occupancy_grid_2d is not None:
                                        points = np.asarray(pcd.points)
                                        if len(points) > 0:
                                            # Update occupancy grid
                                            for point in points:
                                                self.occupancy_grid_2d.update(point[:3])

                                            # Get visualization
                                            occupancy_vis = self.occupancy_grid_2d.get_visualization()
                                            if occupancy_vis is not None:
                                                self.occupancy_map_ready.emit(occupancy_vis)

                # Calculate processing time
                elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
                self.processing_time.emit(elapsed_time)

                # Control processing rate (don't process too fast)
                time.sleep(0.05)  # 20 Hz max processing rate

            except Exception as e:
                self.error_occurred.emit(str(e))
                time.sleep(0.1)

    def stop(self):
        """Stop the worker thread"""
        self.running = False
        self.wait()
