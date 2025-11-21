"""
Main Window
Primary GUI window for the 3D reconstruction application
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QMenuBar, QToolBar, QStatusBar, QMessageBox,
                             QFileDialog, QLabel)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon
import sys
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


class MainWindow(QMainWindow):
    """Main application window"""

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

        # UI state
        self.is_running = False
        self.is_recording = False

        self.init_ui()
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

        export_occ_action = QAction('Export Occupancy Map', self)
        export_occ_action.triggered.connect(self.export_occupancy_map)
        export_menu.addAction(export_occ_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        user_manual_action = QAction('&User Manual', self)
        user_manual_action.triggered.connect(self.show_user_manual)
        help_menu.addAction(user_manual_action)

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
        """Create central widget with three-panel layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel (Camera feeds) - will be created separately
        self.left_panel = QWidget()
        self.left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.addWidget(QLabel("Camera Feeds Panel"))
        # TODO: Add camera feed widgets

        # Center panel (3D Visualization) - will be created separately
        self.center_panel = QWidget()
        center_layout = QVBoxLayout(self.center_panel)
        center_layout.addWidget(QLabel("3D Visualization Panel"))
        # TODO: Add 3D visualization widget

        # Right panel (Controls) - will be created separately
        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(250)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.addWidget(QLabel("Control Panel"))
        # TODO: Add control widgets

        # Add panels to splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.center_panel)
        self.splitter.addWidget(self.right_panel)

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

        self.status_bar.showMessage("Ready")

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
            """)
        else:  # light theme
            self.setStyleSheet("")

        self.config.set('application.theme', theme)

    # Slot methods
    def toggle_processing(self):
        """Toggle processing on/off"""
        if self.is_running:
            self.stop_processing()
        else:
            self.start_processing()

    def start_processing(self):
        """Start 3D reconstruction processing"""
        self.is_running = True
        self.start_stop_action.setText('Stop')
        self.status_bar.showMessage("Processing started")
        self.logger.info("Processing started")

    def stop_processing(self):
        """Stop processing"""
        self.is_running = False
        self.start_stop_action.setText('Start')
        self.status_bar.showMessage("Processing stopped")
        self.logger.info("Processing stopped")

    def toggle_recording(self):
        """Toggle recording on/off"""
        if self.is_recording:
            self.is_recording = False
            self.record_action.setText('Record')
            self.status_bar.showMessage("Recording stopped")
        else:
            self.is_recording = True
            self.record_action.setText('Stop Recording')
            self.status_bar.showMessage("Recording started")

    def take_snapshot(self):
        """Take snapshot of current 3D scene"""
        self.status_bar.showMessage("Snapshot saved")
        self.logger.info("Snapshot taken")

    def start_intrinsic_calibration(self):
        """Start intrinsic camera calibration"""
        self.logger.info("Starting intrinsic calibration")
        # TODO: Implement calibration dialog

    def start_stereo_calibration(self):
        """Start stereo calibration"""
        self.logger.info("Starting stereo calibration")
        # TODO: Implement stereo calibration

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

    def export_point_cloud(self):
        """Export point cloud"""
        self.logger.info("Exporting point cloud")
        # TODO: Implement export

    def export_mesh(self):
        """Export mesh"""
        self.logger.info("Exporting mesh")
        # TODO: Implement export

    def export_occupancy_map(self):
        """Export occupancy map"""
        self.logger.info("Exporting occupancy map")
        # TODO: Implement export

    def open_session(self):
        """Open saved session"""
        self.logger.info("Opening session")

    def save_session(self):
        """Save current session"""
        self.logger.info("Saving session")

    def toggle_camera_panel(self):
        """Toggle camera panel visibility"""
        self.left_panel.setVisible(not self.left_panel.isVisible())

    def toggle_control_panel(self):
        """Toggle control panel visibility"""
        self.right_panel.setVisible(not self.right_panel.isVisible())

    def show_about(self):
        """Show about dialog"""
        about_text = f"""
        <h2>{self.config.get('application.name')}</h2>
        <p>Version: {self.config.get('application.version')}</p>
        <p>Professional multi-camera 3D scene reconstruction system</p>
        <p>Built with PyQt6, OpenCV, and Open3D</p>
        """
        QMessageBox.about(self, "About", about_text)

    def show_user_manual(self):
        """Show user manual"""
        QMessageBox.information(self, "User Manual",
                              "User manual can be found in docs/USER_MANUAL.md")

    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, 'Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Cleanup
            self.camera_manager.disconnect_all()
            self.logger.info("Application closed")
            event.accept()
        else:
            event.ignore()
