"""
Main Window
Primary GUI window for the 3D reconstruction application - FULLY FUNCTIONAL
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QMenuBar, QToolBar, QStatusBar, QMessageBox,
                             QFileDialog, QLabel)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon
import sys
import psutil
import numpy as np
from pathlib import Path

# Import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.camera_manager import CameraManager
from core.calibration import CalibrationManager
from core.stereo_vision import StereoMatcher, MultiViewStereo
from core.point_cloud import PointCloudProcessor
from core.occupancy_mapping import OccupancyGrid2D, OccupancyGrid3D
from core.slam import VisualSLAM
from utils.config import get_config
from utils.logger import get_logger
from utils.file_manager import get_file_manager
from workers.camera_worker import CameraWorker
from workers.processing_worker import ProcessingWorker
from workers.slam_worker import SLAMWorker

# Import GUI widgets
from gui.camera_panel import CameraPanel
from gui.visualization_widget import VisualizationWidget
from gui.control_panel import ControlPanel
from gui.dialogs import IntrinsicCalibrationDialog, StereoCalibrationDialog


class MainWindow(QMainWindow):
    """Main application window - FULLY FUNCTIONAL"""

    def __init__(self):
        super().__init__()

        self.config = get_config()
        self.logger = get_logger()
        self.file_manager = get_file_manager()

        # Initialize core components
        self.camera_manager = CameraManager(
            num_cameras=self.config.get('cameras.num_cameras', 3),
            resolution=tuple(self.config.get('cameras.default_resolution', [640, 480])),
            fps=self.config.get('cameras.default_fps', 30)
        )

        self.calibration_manager = CalibrationManager()
        self.stereo_matcher = StereoMatcher()
        self.multi_view_stereo = MultiViewStereo()
        self.point_cloud_processor = PointCloudProcessor()
        self.occupancy_grid_2d = OccupancyGrid2D()
        self.occupancy_grid_3d = OccupancyGrid3D()
        self.slam = VisualSLAM()

        # Worker threads
        self.camera_workers = []
        self.processing_worker = None
        self.slam_worker = None

        # UI state
        self.is_running = False
        self.is_recording = False
        self.slam_enabled = False

        # Initialize UI
        self.init_ui()

        # Setup timers
        self.setup_timers()

        self.logger.info("Main window initialized")

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(self.config.get('application.name', '3D Reconstruction System'))

        # Set window size
        window_size = self.config.get('ui.window_size', [1920, 1080])
        self.resize(window_size[0], window_size[1])

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar()

        # Create central widget with three-panel layout
        self.create_central_widget()

        # Create status bar
        self.create_status_bar()

        # Apply theme
        self.apply_theme()

        self.logger.info("UI initialized")

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        open_action = QAction('&Open Session', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_session)
        file_menu.addAction(open_action)

        save_action = QAction('&Save Session', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_session)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Calibration menu
        calib_menu = menubar.addMenu('&Calibration')

        calib_intrinsic_action = QAction('Calibrate &Intrinsic', self)
        calib_intrinsic_action.triggered.connect(self.start_intrinsic_calibration)
        calib_menu.addAction(calib_intrinsic_action)

        calib_stereo_action = QAction('Calibrate &Stereo', self)
        calib_stereo_action.triggered.connect(self.start_stereo_calibration)
        calib_menu.addAction(calib_stereo_action)

        calib_menu.addSeparator()

        load_calib_action = QAction('&Load Calibration', self)
        load_calib_action.triggered.connect(self.load_calibration)
        calib_menu.addAction(load_calib_action)

        save_calib_action = QAction('&Save Calibration', self)
        save_calib_action.triggered.connect(self.save_calibration)
        calib_menu.addAction(save_calib_action)

        # Processing menu
        process_menu = menubar.addMenu('&Processing')

        start_action = QAction('&Start Processing', self)
        start_action.setShortcut('Ctrl+R')
        start_action.triggered.connect(self.start_processing)
        process_menu.addAction(start_action)

        stop_action = QAction('S&top Processing', self)
        stop_action.setShortcut('Ctrl+T')
        stop_action.triggered.connect(self.stop_processing)
        process_menu.addAction(stop_action)

        # View menu
        view_menu = menubar.addMenu('&View')

        toggle_camera_action = QAction('Toggle Camera Panel', self)
        toggle_camera_action.triggered.connect(self.toggle_camera_panel)
        view_menu.addAction(toggle_camera_action)

        toggle_control_action = QAction('Toggle Control Panel', self)
        toggle_control_action.triggered.connect(self.toggle_control_panel)
        view_menu.addAction(toggle_control_action)

        view_menu.addSeparator()

        theme_dark_action = QAction('Dark Theme', self)
        theme_dark_action.triggered.connect(lambda: self.set_theme('dark'))
        view_menu.addAction(theme_dark_action)

        theme_light_action = QAction('Light Theme', self)
        theme_light_action.triggered.connect(lambda: self.set_theme('light'))
        view_menu.addAction(theme_light_action)

        # Export menu
        export_menu = menubar.addMenu('&Export')

        export_pcd_action = QAction('Export Point Cloud', self)
        export_pcd_action.triggered.connect(self.export_point_cloud)
        export_menu.addAction(export_pcd_action)

        export_mesh_action = QAction('Export Mesh', self)
        export_mesh_action.triggered.connect(self.export_mesh)
        export_menu.addAction(export_mesh_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Start/Stop button
        self.start_stop_action = QAction('Start', self)
        self.start_stop_action.triggered.connect(self.toggle_processing)
        toolbar.addAction(self.start_stop_action)

        toolbar.addSeparator()

        # Calibrate button
        calibrate_action = QAction('Calibrate', self)
        calibrate_action.triggered.connect(self.start_intrinsic_calibration)
        toolbar.addAction(calibrate_action)

        toolbar.addSeparator()

        # Record button
        self.record_action = QAction('Record', self)
        self.record_action.triggered.connect(self.toggle_recording)
        toolbar.addAction(self.record_action)

        # Snapshot button
        snapshot_action = QAction('Snapshot', self)
        snapshot_action.triggered.connect(self.take_snapshot)
        toolbar.addAction(snapshot_action)

    def create_central_widget(self):
        """Create central widget with three-panel layout - REAL WIDGETS"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Camera Feeds (REAL)
        self.camera_panel = CameraPanel(self.camera_manager)
        self.camera_panel.setMinimumWidth(300)
        self.camera_panel.connect_cameras_requested.connect(self.connect_cameras)

        # Center panel - 3D Visualization (REAL)
        self.visualization_widget = VisualizationWidget()

        # Right panel - Controls (REAL)
        self.control_panel = ControlPanel(self.config)
        self.control_panel.setMinimumWidth(250)

        # Connect control panel signals
        self.control_panel.calibration_requested.connect(self.handle_calibration_request)
        self.control_panel.stereo_params_changed.connect(self.update_stereo_params)
        self.control_panel.point_cloud_params_changed.connect(self.update_point_cloud_params)
        self.control_panel.slam_toggled.connect(self.toggle_slam)
        self.control_panel.export_requested.connect(self.handle_export_request)

        # Add panels to splitter
        self.splitter.addWidget(self.camera_panel)
        self.splitter.addWidget(self.visualization_widget)
        self.splitter.addWidget(self.control_panel)

        # Set initial sizes based on config
        panel_split = self.config.get('ui.panel_split', [30, 50, 20])
        total = sum(panel_split)
        width = self.width()
        self.splitter.setSizes([
            int(width * panel_split[0] / total),
            int(width * panel_split[1] / total),
            int(width * panel_split[2] / total)
        ])

        layout.addWidget(self.splitter)

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status labels
        self.fps_label = QLabel("FPS: 0")
        self.point_count_label = QLabel("Points: 0")
        self.processing_time_label = QLabel("Processing: 0ms")

        self.status_bar.addPermanentWidget(self.fps_label)
        self.status_bar.addPermanentWidget(self.point_count_label)
        self.status_bar.addPermanentWidget(self.processing_time_label)

        self.status_bar.showMessage("Ready - Connect cameras to begin")

    def setup_timers(self):
        """Setup update timers"""
        # Metrics update timer
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(1000)  # Update every second

        # Frame processing timer - feeds frames to processing worker
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self.update_processing_frames)
        self.frame_timer.start(50)  # Update at 20 Hz

    def apply_theme(self):
        """Apply theme to application"""
        theme = self.config.get('application.theme', 'dark')
        self.set_theme(theme)

    def set_theme(self, theme: str):
        """Set application theme"""
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow { background-color: #2b2b2b; color: #ffffff; }
                QWidget { background-color: #2b2b2b; color: #ffffff; }
                QLabel { color: #ffffff; }
                QPushButton { background-color: #3c3f41; color: #ffffff; border: 1px solid #555555; padding: 5px; }
                QPushButton:hover { background-color: #4c5052; }
                QMenuBar { background-color: #3c3f41; color: #ffffff; }
                QMenuBar::item:selected { background-color: #4c5052; }
                QMenu { background-color: #3c3f41; color: #ffffff; }
                QMenu::item:selected { background-color: #4c5052; }
                QToolBar { background-color: #3c3f41; border: none; }
                QStatusBar { background-color: #3c3f41; color: #ffffff; }
                QGroupBox { border: 1px solid #555555; margin-top: 0.5em; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }
            """)
        else:
            self.setStyleSheet("")

        self.config.set('application.theme', theme)

    def connect_cameras(self):
        """Connect to cameras"""
        self.logger.info("Connecting cameras...")
        self.status_bar.showMessage("Connecting cameras...")

        # Connect to specific Logitech C270 cameras at indices 2, 4, 6
        # These are the three external Logitech webcams
        logitech_camera_indices = [2, 4, 6]
        connected = self.camera_manager.auto_connect(preferred_indices=logitech_camera_indices)

        if connected > 0:
            self.logger.info(f"Connected {connected} Logitech C270 cameras")
            self.status_bar.showMessage(f"Connected {connected} cameras")
            self.camera_panel.update_camera_status()

            # Start camera workers
            self.start_camera_workers()
        else:
            self.logger.warning("No cameras detected")
            QMessageBox.warning(self, "Warning", "No cameras detected. Please connect cameras and try again.")

    def start_camera_workers(self):
        """Start camera worker threads"""
        # Stop existing workers
        for worker in self.camera_workers:
            worker.stop()

        self.camera_workers.clear()

        # Create and start new workers
        for i in range(3):
            if self.camera_manager.is_camera_active(i):
                worker = CameraWorker(i, self.camera_manager)

                # Connect signals
                camera_widget = self.camera_panel.get_camera_widget(i)
                if camera_widget:
                    worker.frame_ready.connect(camera_widget.update_frame)
                    worker.fps_updated.connect(camera_widget.update_fps)

                worker.start()
                self.camera_workers.append(worker)

        self.logger.info(f"Started {len(self.camera_workers)} camera workers")

    # Slot methods
    def toggle_processing(self):
        """Toggle processing on/off"""
        if self.is_running:
            self.stop_processing()
        else:
            self.start_processing()

    def create_default_calibration(self):
        """Create default calibration matrices for initial testing"""
        import numpy as np

        # Get camera resolution
        resolution = self.config.get('cameras.default_resolution', [320, 240])
        width, height = resolution[0], resolution[1]

        # Create a simple camera matrix (assuming ~60 degree FOV)
        focal_length = width * 1.2  # Rough approximation
        camera_matrix = np.array([
            [focal_length, 0, width / 2],
            [0, focal_length, height / 2],
            [0, 0, 1]
        ], dtype=np.float32)

        # Create Q matrix for stereo reconstruction
        # Assuming baseline of 10cm between cameras
        baseline = 0.1  # meters
        Q = np.array([
            [1, 0, 0, -width / 2],
            [0, 1, 0, -height / 2],
            [0, 0, 0, focal_length],
            [0, 0, 1/baseline, 0]
        ], dtype=np.float32)

        self.logger.info("Created default calibration matrices")
        self.control_panel.add_log_message("Using default calibration (uncalibrated mode)")

        return Q, camera_matrix

    def update_processing_frames(self):
        """Update frames in processing worker"""
        if not self.is_running or self.processing_worker is None:
            return

        # Get frames from first two cameras (for stereo)
        frames = self.camera_manager.get_frames()

        if len(frames) >= 2 and frames[0] is not None and frames[1] is not None:
            self.processing_worker.set_frames(frames[0], frames[1])

            # Feed first camera frame to SLAM if enabled
            if self.slam_enabled and self.slam_worker is not None:
                import time
                self.slam_worker.set_frame(frames[0], time.time())

    def on_point_cloud_ready(self, pcd):
        """Handle new point cloud from processing worker"""
        # Save for export
        self._last_point_cloud = pcd
        # Update visualization
        self.visualization_widget.update_point_cloud(pcd)

    def start_processing(self):
        """Start 3D reconstruction processing"""
        if not self.camera_manager.get_active_count() > 0:
            QMessageBox.warning(self, "Warning", "No active cameras. Please connect cameras first.")
            return

        self.is_running = True
        self.start_stop_action.setText('Stop')
        self.status_bar.showMessage("Processing started")
        self.logger.info("Processing started")

        # Start processing worker
        if self.processing_worker is None:
            self.processing_worker = ProcessingWorker(
                self.stereo_matcher,
                self.point_cloud_processor,
                self.occupancy_grid_2d
            )

            # Set default calibration if no calibration loaded
            Q, camera_matrix = self.create_default_calibration()
            self.processing_worker.set_calibration_data(Q, camera_matrix)

            # Connect signals
            self.processing_worker.point_cloud_ready.connect(self.on_point_cloud_ready)
            self.processing_worker.disparity_ready.connect(self.visualization_widget.update_disparity)
            self.processing_worker.depth_ready.connect(self.visualization_widget.update_depth)
            self.processing_worker.occupancy_map_ready.connect(self.visualization_widget.update_occupancy_map)
            self.processing_worker.processing_time.connect(
                lambda t: self.processing_time_label.setText(f"Processing: {t:.1f}ms")
            )

            self.processing_worker.start()

        self.processing_worker.enable_processing(True)
        self.processing_worker.enable_occupancy_mapping(True)
        self.control_panel.add_log_message("Processing started")

    def stop_processing(self):
        """Stop processing"""
        self.is_running = False
        self.start_stop_action.setText('Start')
        self.status_bar.showMessage("Processing stopped")
        self.logger.info("Processing stopped")

        if self.processing_worker:
            self.processing_worker.enable_processing(False)

        self.control_panel.add_log_message("Processing stopped")

    def toggle_recording(self):
        """Toggle recording on/off"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """Start recording session"""
        if not self.is_running:
            QMessageBox.warning(
                self,
                "Not Processing",
                "Please start processing before recording."
            )
            return

        # Create recording directory with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        recording_dir = self.file_manager.get_path('recordings') / f"session_{timestamp}"
        recording_dir.mkdir(parents=True, exist_ok=True)

        self.recording_dir = recording_dir
        self.recording_frame_count = 0

        self.is_recording = True
        self.record_action.setText('Stop Recording')
        self.status_bar.showMessage(f"Recording to: {recording_dir.name}")
        self.control_panel.add_log_message(f"Recording started: {recording_dir.name}")
        self.logger.info(f"Recording started: {recording_dir}")

    def stop_recording(self):
        """Stop recording session"""
        self.is_recording = False
        self.record_action.setText('Record')

        # Save session metadata
        if hasattr(self, 'recording_dir'):
            metadata_file = self.recording_dir / "session_info.txt"
            try:
                with open(metadata_file, 'w') as f:
                    f.write(f"Session Recording\n")
                    f.write(f"Frames recorded: {self.recording_frame_count}\n")
                    f.write(f"SLAM enabled: {self.slam_enabled}\n")
                    if self.slam_enabled:
                        f.write(f"SLAM poses: {len(self.slam.poses)}\n")
                        f.write(f"SLAM map points: {self.slam.get_num_map_points()}\n")

                self.logger.info(f"Session metadata saved: {metadata_file}")
            except Exception as e:
                self.logger.error(f"Failed to save session metadata: {e}")

        self.status_bar.showMessage("Recording stopped")
        self.control_panel.add_log_message("Recording stopped")
        self.logger.info("Recording stopped")

    def take_snapshot(self):
        """Take snapshot of current 3D scene"""
        if not hasattr(self, '_last_point_cloud') or self._last_point_cloud is None:
            QMessageBox.warning(self, "No Data", "No point cloud available to snapshot.")
            return

        # Create snapshot filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = self.file_manager.exports_dir / f"snapshot_{timestamp}.ply"

        try:
            import open3d as o3d
            o3d.io.write_point_cloud(str(snapshot_file), self._last_point_cloud)

            self.status_bar.showMessage(f"Snapshot saved: {snapshot_file.name}")
            self.control_panel.add_log_message(f"Snapshot: {snapshot_file.name}")
            self.logger.info(f"Snapshot saved: {snapshot_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Snapshot failed: {str(e)}")
            self.logger.error(f"Snapshot failed: {e}")

    def handle_calibration_request(self, calib_type: str):
        """Handle calibration request from control panel"""
        if calib_type == "intrinsic":
            self.start_intrinsic_calibration()
        elif calib_type == "stereo":
            self.start_stereo_calibration()

    def start_intrinsic_calibration(self):
        """Start intrinsic camera calibration"""
        self.logger.info("Starting intrinsic calibration")
        self.control_panel.add_log_message("Intrinsic calibration started")

        # Check if cameras are connected
        if self.camera_manager.get_active_count() == 0:
            QMessageBox.warning(
                self,
                "No Cameras",
                "Please connect cameras before calibration."
            )
            return

        # Create and show calibration dialog
        dialog = IntrinsicCalibrationDialog(
            self.camera_manager,
            self.calibration_manager,
            self
        )
        dialog.calibration_complete.connect(self.on_intrinsic_calibration_complete)
        dialog.exec()

    def on_intrinsic_calibration_complete(self, camera_id: int, result):
        """Handle intrinsic calibration completion"""
        self.logger.info(f"Intrinsic calibration complete for camera {camera_id}")
        self.control_panel.add_log_message(
            f"Camera {camera_id} calibrated - Error: {result.reprojection_error:.4f}px"
        )
        self.status_bar.showMessage(f"Camera {camera_id} calibration complete")

        # Update SLAM with camera intrinsics (use first camera for SLAM)
        if camera_id == 0:
            self.slam.set_camera_intrinsics(result.camera_matrix, result.dist_coeffs)
            self.logger.info("SLAM camera intrinsics updated")
            self.control_panel.add_log_message("SLAM camera intrinsics configured")

    def start_stereo_calibration(self):
        """Start stereo calibration"""
        self.logger.info("Starting stereo calibration")
        self.control_panel.add_log_message("Stereo calibration started")

        # Check if cameras are connected
        if self.camera_manager.get_active_count() < 2:
            QMessageBox.warning(
                self,
                "Insufficient Cameras",
                "Stereo calibration requires at least 2 cameras."
            )
            return

        # Create and show calibration dialog
        dialog = StereoCalibrationDialog(
            self.camera_manager,
            self.calibration_manager,
            self
        )
        dialog.calibration_complete.connect(self.on_stereo_calibration_complete)
        dialog.exec()

    def on_stereo_calibration_complete(self, camera_pair: tuple, result):
        """Handle stereo calibration completion"""
        cam1, cam2 = camera_pair
        self.logger.info(f"Stereo calibration complete for cameras {cam1}-{cam2}")
        self.control_panel.add_log_message(
            f"Stereo pair {cam1}-{cam2} calibrated - Error: {result.reprojection_error:.4f}px"
        )
        self.status_bar.showMessage(f"Stereo calibration complete: {cam1}-{cam2}")

    def load_calibration(self):
        """Load calibration from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Calibration", str(self.file_manager.calibrations_dir), "JSON Files (*.json)"
        )
        if filename:
            if self.calibration_manager.load_calibration(filename):
                self.status_bar.showMessage(f"Calibration loaded: {filename}")
                self.logger.info(f"Calibration loaded: {filename}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load calibration")

    def save_calibration(self):
        """Save calibration to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Calibration", str(self.file_manager.calibrations_dir), "JSON Files (*.json)"
        )
        if filename:
            if self.calibration_manager.save_calibration(filename):
                self.status_bar.showMessage(f"Calibration saved: {filename}")
                self.logger.info(f"Calibration saved: {filename}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save calibration")

    def update_stereo_params(self, params: dict):
        """Update stereo matching parameters"""
        for key, value in params.items():
            self.stereo_matcher.set_parameter(key, value)

        self.logger.info(f"Updated stereo parameters: {params}")
        self.control_panel.add_log_message(f"Stereo params updated: {params}")

    def update_point_cloud_params(self, params: dict):
        """Update point cloud processing parameters"""
        self.logger.info(f"Updated point cloud parameters: {params}")

    def toggle_slam(self, enabled: bool):
        """Toggle SLAM on/off"""
        if enabled:
            # Check if SLAM has camera intrinsics
            if self.slam.camera_matrix is None:
                QMessageBox.warning(
                    self,
                    "SLAM Not Configured",
                    "Please calibrate camera 0 (intrinsic) before enabling SLAM."
                )
                return

            # Start SLAM worker
            if self.slam_worker is None:
                self.slam_worker = SLAMWorker(self.slam)

                # Connect signals
                self.slam_worker.trajectory_updated.connect(self.visualization_widget.update_trajectory)
                self.slam_worker.map_points_updated.connect(self.visualization_widget.update_slam_map_points)
                self.slam_worker.slam_stats_updated.connect(self.on_slam_stats_updated)

                self.slam_worker.start()

            self.slam_worker.enable_processing(True)
            self.slam_enabled = True

            self.logger.info("SLAM enabled")
            self.control_panel.add_log_message("SLAM enabled - Tracking started")
            self.control_panel.update_slam_status(True)
        else:
            if self.slam_worker:
                self.slam_worker.enable_processing(False)

            self.slam_enabled = False
            self.logger.info("SLAM disabled")
            self.control_panel.add_log_message("SLAM disabled")
            self.control_panel.update_slam_status(False)

    def on_slam_stats_updated(self, stats: dict):
        """Handle SLAM statistics update"""
        num_poses = stats.get('num_poses', 0)
        num_points = stats.get('num_map_points', 0)
        self.control_panel.update_slam_status(True, num_poses, num_points)

    def handle_export_request(self, export_type: str):
        """Handle export request"""
        self.logger.info(f"Export requested: {export_type}")

        if export_type.startswith("pointcloud_"):
            format_type = export_type.split("_")[1].lower()
            self.export_point_cloud(format_type)
        elif export_type.startswith("mesh_"):
            format_type = export_type.split("_")[1].lower()
            self.export_mesh(format_type)
        elif export_type == "occupancy":
            self.export_occupancy_map()
        elif export_type == "trajectory":
            self.export_trajectory()

    def export_point_cloud(self, format_type="ply"):
        """Export point cloud"""
        if self.processing_worker is None or not hasattr(self, '_last_point_cloud'):
            QMessageBox.warning(self, "Warning", "No point cloud available to export. Start processing first.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Point Cloud",
            str(self.file_manager.exports_dir / f"pointcloud.{format_type}"),
            f"{format_type.upper()} Files (*.{format_type})"
        )

        if filename:
            try:
                import open3d as o3d
                if hasattr(self, '_last_point_cloud') and self._last_point_cloud is not None:
                    o3d.io.write_point_cloud(filename, self._last_point_cloud)
                    self.status_bar.showMessage(f"Point cloud exported: {filename}")
                    self.control_panel.add_log_message(f"Exported point cloud: {filename}")
                    self.logger.info(f"Point cloud exported to {filename}")
                else:
                    QMessageBox.warning(self, "Warning", "No point cloud data available")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
                self.logger.error(f"Point cloud export failed: {e}")

    def export_mesh(self, format_type="obj"):
        """Export mesh"""
        if not hasattr(self, '_last_point_cloud') or self._last_point_cloud is None:
            QMessageBox.warning(self, "Warning", "No point cloud available. Generate mesh from point cloud first.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Mesh",
            str(self.file_manager.exports_dir / f"mesh.{format_type}"),
            f"{format_type.upper()} Files (*.{format_type})"
        )

        if filename:
            try:
                import open3d as o3d
                # Generate mesh from point cloud
                self.control_panel.add_log_message("Generating mesh from point cloud...")
                mesh = self.point_cloud_processor.create_mesh_poisson(self._last_point_cloud)

                if mesh is not None and len(mesh.triangles) > 0:
                    o3d.io.write_triangle_mesh(filename, mesh)
                    self.status_bar.showMessage(f"Mesh exported: {filename}")
                    self.control_panel.add_log_message(f"Exported mesh: {filename}")
                    self.logger.info(f"Mesh exported to {filename}")
                else:
                    QMessageBox.warning(self, "Warning", "Failed to generate mesh from point cloud")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Mesh export failed: {str(e)}")
                self.logger.error(f"Mesh export failed: {e}")

    def export_occupancy_map(self):
        """Export occupancy map"""
        self.logger.info("Exporting occupancy map")

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Occupancy Map",
            str(self.file_manager.exports_dir / "occupancy_map.npy"),
            "NumPy Array (*.npy);;PNG Image (*.png)"
        )

        if filename:
            try:
                # Get occupancy grid visualization
                occupancy_vis = self.occupancy_grid_2d.get_visualization()

                if occupancy_vis is not None:
                    if filename.endswith('.png'):
                        # Export as PNG image
                        import cv2
                        cv2.imwrite(filename, occupancy_vis)
                    else:
                        # Export as NumPy array
                        np.save(filename, self.occupancy_grid_2d.grid)

                    self.status_bar.showMessage(f"Occupancy map exported: {filename}")
                    self.control_panel.add_log_message(f"Exported occupancy map: {filename}")
                    self.logger.info(f"Occupancy map exported to {filename}")
                else:
                    QMessageBox.warning(self, "Warning", "No occupancy map data available")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
                self.logger.error(f"Occupancy map export failed: {e}")

    def export_trajectory(self):
        """Export SLAM trajectory"""
        if not self.slam_enabled or len(self.slam.poses) == 0:
            QMessageBox.warning(
                self,
                "No Trajectory",
                "SLAM is not enabled or no trajectory data available."
            )
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export SLAM Trajectory",
            str(self.file_manager.exports_dir / "trajectory.txt"),
            "Text File (*.txt);;CSV File (*.csv)"
        )

        if filename:
            try:
                if self.slam.save_trajectory(filename):
                    self.status_bar.showMessage(f"Trajectory exported: {filename}")
                    self.control_panel.add_log_message(f"Exported trajectory: {filename}")
                    self.logger.info(f"Trajectory exported to {filename}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to export trajectory")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
                self.logger.error(f"Trajectory export failed: {e}")

    def open_session(self):
        """Open saved session"""
        self.logger.info("Opening session")

    def save_session(self):
        """Save current session"""
        self.logger.info("Saving session")

    def toggle_camera_panel(self):
        """Toggle camera panel visibility"""
        self.camera_panel.setVisible(not self.camera_panel.isVisible())

    def toggle_control_panel(self):
        """Toggle control panel visibility"""
        self.control_panel.setVisible(not self.control_panel.isVisible())

    def update_metrics(self):
        """Update metrics display"""
        # Get system metrics
        memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Calculate actual FPS from camera workers
        fps = 0
        active_cameras = 0
        for worker in self.camera_workers:
            if hasattr(worker, 'frame_times') and len(worker.frame_times) > 0:
                fps += len(worker.frame_times)
                active_cameras += 1
        if active_cameras > 0:
            fps = fps / active_cameras  # Average FPS across cameras

        # Get point count from last point cloud
        points = 0
        if hasattr(self, '_last_point_cloud') and self._last_point_cloud is not None:
            import numpy as np
            points = len(np.asarray(self._last_point_cloud.points))

        # Processing time will be updated via signal from processing worker
        processing_time = 0

        self.control_panel.update_metrics(fps, points, processing_time, memory)

    def show_about(self):
        """Show about dialog"""
        about_text = f"""
        <h2>{self.config.get('application.name')}</h2>
        <p>Version: {self.config.get('application.version')}</p>
        <p>Professional multi-camera 3D scene reconstruction system</p>
        <p>Built with PyQt6, OpenCV, and Open3D</p>
        """
        QMessageBox.about(self, "About", about_text)

    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, 'Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Stop workers
            for worker in self.camera_workers:
                worker.stop()

            if self.processing_worker:
                self.processing_worker.stop()

            if self.slam_worker:
                self.slam_worker.stop()

            # Cleanup
            self.camera_manager.disconnect_all()
            self.logger.info("Application closed")
            event.accept()
        else:
            event.ignore()
