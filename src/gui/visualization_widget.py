"""
3D Visualization Widget
Real-time 3D point cloud and mesh visualization
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import Qt, pyqtSlot
import pyqtgraph.opengl as gl
import numpy as np


class VisualizationWidget(QWidget):
    """3D visualization widget for point clouds and meshes"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.point_cloud_item = None
        self.mesh_item = None
        self.trajectory_item = None
        self.slam_map_points_item = None
        self.occupancy_map_item = None
        self.current_mode = "Point Cloud"

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header with controls
        header_layout = QHBoxLayout()

        title_label = QLabel("3D Visualization")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)

        # View mode selector
        header_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Point Cloud", "Mesh", "Occupancy Map", "SLAM Trajectory"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        header_layout.addWidget(self.mode_combo)

        header_layout.addStretch()

        # Reset view button
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_view)
        header_layout.addWidget(reset_btn)

        layout.addLayout(header_layout)

        # 3D View widget
        self.view_widget = gl.GLViewWidget()
        self.view_widget.setMinimumSize(400, 400)
        self.view_widget.setCameraPosition(distance=2.0)
        self.view_widget.setBackgroundColor('k')  # Black background

        # Add grid
        self.grid = gl.GLGridItem()
        self.grid.scale(0.1, 0.1, 0.1)
        self.view_widget.addItem(self.grid)

        # Add coordinate axes
        self.add_axes()

        layout.addWidget(self.view_widget)

        # Info label
        self.info_label = QLabel("Ready - No data")
        self.info_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(self.info_label)

    def add_axes(self):
        """Add XYZ coordinate axes"""
        # X axis (red)
        x_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [1, 0, 0]]),
            color=(1, 0, 0, 1),
            width=2,
            antialias=True
        )
        self.view_widget.addItem(x_axis)

        # Y axis (green)
        y_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 1, 0]]),
            color=(0, 1, 0, 1),
            width=2,
            antialias=True
        )
        self.view_widget.addItem(y_axis)

        # Z axis (blue)
        z_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 0, 1]]),
            color=(0, 0, 1, 1),
            width=2,
            antialias=True
        )
        self.view_widget.addItem(z_axis)

    @pyqtSlot(object)
    def update_point_cloud(self, pcd):
        """Update point cloud display"""
        try:
            # Remove old point cloud
            if self.point_cloud_item is not None:
                self.view_widget.removeItem(self.point_cloud_item)
                self.point_cloud_item = None

            # Extract points and colors from Open3D point cloud
            points = np.asarray(pcd.points)

            if len(points) == 0:
                self.info_label.setText("No points in cloud")
                return

            # Get colors
            if pcd.has_colors():
                colors = np.asarray(pcd.colors)
            else:
                # Default white color
                colors = np.ones((len(points), 3))

            # Create scatter plot
            self.point_cloud_item = gl.GLScatterPlotItem(
                pos=points,
                color=colors,
                size=2,
                pxMode=True
            )
            self.view_widget.addItem(self.point_cloud_item)

            # Update info
            self.info_label.setText(f"Point Cloud: {len(points)} points")

        except Exception as e:
            print(f"Error updating point cloud: {e}")
            self.info_label.setText(f"Error: {str(e)}")

    @pyqtSlot(np.ndarray)
    def update_disparity(self, disparity: np.ndarray):
        """Update with disparity map visualization"""
        # For now, just show info
        self.info_label.setText(f"Disparity map: {disparity.shape}")

    @pyqtSlot(np.ndarray)
    def update_depth(self, depth: np.ndarray):
        """Update with depth map visualization"""
        self.info_label.setText(f"Depth map: {depth.shape}")

    @pyqtSlot(np.ndarray)
    def update_trajectory(self, positions: np.ndarray):
        """Update SLAM trajectory"""
        try:
            # Remove old trajectory
            if self.trajectory_item is not None:
                self.view_widget.removeItem(self.trajectory_item)
                self.trajectory_item = None

            if len(positions) < 2:
                return

            # Create line plot for trajectory
            self.trajectory_item = gl.GLLinePlotItem(
                pos=positions,
                color=(1, 0, 0, 1),
                width=3,
                antialias=True
            )
            self.view_widget.addItem(self.trajectory_item)

            self.info_label.setText(f"Trajectory: {len(positions)} poses")

        except Exception as e:
            print(f"Error updating trajectory: {e}")

    @pyqtSlot(np.ndarray, np.ndarray)
    def update_slam_map_points(self, points: np.ndarray, colors: np.ndarray):
        """Update SLAM map points"""
        try:
            # Remove old map points
            if self.slam_map_points_item is not None:
                self.view_widget.removeItem(self.slam_map_points_item)
                self.slam_map_points_item = None

            if len(points) == 0:
                return

            # Create scatter plot for map points
            self.slam_map_points_item = gl.GLScatterPlotItem(
                pos=points,
                color=colors,
                size=3,
                pxMode=True
            )
            self.view_widget.addItem(self.slam_map_points_item)

            self.info_label.setText(f"SLAM: {len(points)} map points")

        except Exception as e:
            print(f"Error updating SLAM map points: {e}")

    @pyqtSlot(np.ndarray)
    def update_occupancy_map(self, occupancy_grid: np.ndarray):
        """Update occupancy map visualization"""
        try:
            # Remove old occupancy map
            if self.occupancy_map_item is not None:
                self.view_widget.removeItem(self.occupancy_map_item)
                self.occupancy_map_item = None

            if occupancy_grid is None or occupancy_grid.size == 0:
                return

            # Convert 2D occupancy grid to 3D points for visualization
            # Assuming occupancy_grid is a 2D array where >0 means occupied
            occupied_cells = np.argwhere(occupancy_grid > 0)

            if len(occupied_cells) == 0:
                return

            # Scale to world coordinates (adjust as needed)
            scale = 0.05  # 5cm per cell
            points = occupied_cells * scale
            # Add z=0 coordinate
            points_3d = np.column_stack([points[:, 0], points[:, 1], np.zeros(len(points))])

            # Color based on occupancy value
            colors = np.zeros((len(points), 4))
            colors[:, 0] = 1.0  # Red channel
            colors[:, 3] = np.clip(occupancy_grid[occupied_cells[:, 0], occupied_cells[:, 1]] / 255.0, 0, 1)

            # Create scatter plot
            self.occupancy_map_item = gl.GLScatterPlotItem(
                pos=points_3d,
                color=colors,
                size=5,
                pxMode=True
            )
            self.view_widget.addItem(self.occupancy_map_item)

            self.info_label.setText(f"Occupancy Map: {len(occupied_cells)} occupied cells")

        except Exception as e:
            print(f"Error updating occupancy map: {e}")

    def on_mode_changed(self, mode: str):
        """Handle visualization mode change"""
        self.current_mode = mode

        # Show/hide different visualizations based on mode
        if mode == "Point Cloud":
            # Show point cloud, hide others
            if self.slam_map_points_item:
                self.slam_map_points_item.setVisible(False)
            if self.occupancy_map_item:
                self.occupancy_map_item.setVisible(False)
        elif mode == "SLAM Trajectory":
            # Show trajectory and map points
            if self.slam_map_points_item:
                self.slam_map_points_item.setVisible(True)
            if self.occupancy_map_item:
                self.occupancy_map_item.setVisible(False)
            if self.point_cloud_item:
                self.point_cloud_item.setVisible(False)
        elif mode == "Occupancy Map":
            # Show occupancy map
            if self.occupancy_map_item:
                self.occupancy_map_item.setVisible(True)
            if self.slam_map_points_item:
                self.slam_map_points_item.setVisible(False)
            if self.point_cloud_item:
                self.point_cloud_item.setVisible(False)

        self.info_label.setText(f"Mode: {mode}")

    def reset_view(self):
        """Reset camera view to default"""
        self.view_widget.setCameraPosition(distance=2.0, elevation=30, azimuth=45)

    def clear(self):
        """Clear all visualizations"""
        if self.point_cloud_item:
            self.view_widget.removeItem(self.point_cloud_item)
            self.point_cloud_item = None
        if self.mesh_item:
            self.view_widget.removeItem(self.mesh_item)
            self.mesh_item = None
        if self.trajectory_item:
            self.view_widget.removeItem(self.trajectory_item)
            self.trajectory_item = None
        if self.slam_map_points_item:
            self.view_widget.removeItem(self.slam_map_points_item)
            self.slam_map_points_item = None
        if self.occupancy_map_item:
            self.view_widget.removeItem(self.occupancy_map_item)
            self.occupancy_map_item = None

        self.info_label.setText("Ready - No data")
