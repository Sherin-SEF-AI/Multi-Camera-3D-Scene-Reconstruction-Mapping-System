"""
Control Panel
Contains tabbed interface for all controls and settings
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel,
                             QSlider, QSpinBox, QDoubleSpinBox, QComboBox,
                             QPushButton, QFormLayout, QGroupBox, QCheckBox,
                             QHBoxLayout, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal


class ControlPanel(QWidget):
    """Control panel with tabbed interface"""

    # Signals
    calibration_requested = pyqtSignal(str)  # Calibration type
    stereo_params_changed = pyqtSignal(dict)  # Stereo parameters
    point_cloud_params_changed = pyqtSignal(dict)  # Point cloud parameters
    slam_toggled = pyqtSignal(bool)  # SLAM enable/disable
    export_requested = pyqtSignal(str)  # Export format

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel("Controls & Settings")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_calibration_tab(), "Calibration")
        self.tabs.addTab(self.create_stereo_tab(), "Stereo")
        self.tabs.addTab(self.create_point_cloud_tab(), "Point Cloud")
        self.tabs.addTab(self.create_slam_tab(), "SLAM")
        self.tabs.addTab(self.create_export_tab(), "Export")
        self.tabs.addTab(self.create_metrics_tab(), "Metrics")

        layout.addWidget(self.tabs)

    def create_calibration_tab(self):
        """Create calibration controls tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Calibration type
        type_group = QGroupBox("Calibration Type")
        type_layout = QVBoxLayout()

        intrinsic_btn = QPushButton("Calibrate Intrinsic")
        intrinsic_btn.clicked.connect(lambda: self.calibration_requested.emit("intrinsic"))
        type_layout.addWidget(intrinsic_btn)

        stereo_btn = QPushButton("Calibrate Stereo")
        stereo_btn.clicked.connect(lambda: self.calibration_requested.emit("stereo"))
        type_layout.addWidget(stereo_btn)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Calibration settings
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()

        self.chessboard_width_spin = QSpinBox()
        self.chessboard_width_spin.setRange(3, 20)
        self.chessboard_width_spin.setValue(self.config.get('calibration.chessboard_size', [9, 6])[0])
        settings_layout.addRow("Chessboard Width:", self.chessboard_width_spin)

        self.chessboard_height_spin = QSpinBox()
        self.chessboard_height_spin.setRange(3, 20)
        self.chessboard_height_spin.setValue(self.config.get('calibration.chessboard_size', [9, 6])[1])
        settings_layout.addRow("Chessboard Height:", self.chessboard_height_spin)

        self.square_size_spin = QDoubleSpinBox()
        self.square_size_spin.setRange(1.0, 100.0)
        self.square_size_spin.setValue(self.config.get('calibration.square_size_mm', 25.0))
        self.square_size_spin.setSuffix(" mm")
        settings_layout.addRow("Square Size:", self.square_size_spin)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Status
        self.calib_status_label = QLabel("Status: Not calibrated")
        self.calib_status_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(self.calib_status_label)

        layout.addStretch()
        return tab

    def create_stereo_tab(self):
        """Create stereo vision controls tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Algorithm selection
        algo_group = QGroupBox("Algorithm")
        algo_layout = QFormLayout()

        self.stereo_algo_combo = QComboBox()
        self.stereo_algo_combo.addItems(["SGBM", "BM"])
        self.stereo_algo_combo.setCurrentText(self.config.get('stereo.algorithm', 'SGBM'))
        self.stereo_algo_combo.currentTextChanged.connect(self.on_stereo_params_changed)
        algo_layout.addRow("Algorithm:", self.stereo_algo_combo)

        algo_group.setLayout(algo_layout)
        layout.addWidget(algo_group)

        # Parameters
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout()

        # Num disparities
        self.num_disp_spin = QSpinBox()
        self.num_disp_spin.setRange(16, 256)
        self.num_disp_spin.setSingleStep(16)
        self.num_disp_spin.setValue(self.config.get('stereo.num_disparities', 80))
        self.num_disp_spin.valueChanged.connect(self.on_stereo_params_changed)
        params_layout.addRow("Num Disparities:", self.num_disp_spin)

        # Block size
        self.block_size_spin = QSpinBox()
        self.block_size_spin.setRange(5, 25)
        self.block_size_spin.setSingleStep(2)
        self.block_size_spin.setValue(self.config.get('stereo.block_size', 15))
        self.block_size_spin.valueChanged.connect(self.on_stereo_params_changed)
        params_layout.addRow("Block Size:", self.block_size_spin)

        # Uniqueness ratio
        self.uniqueness_spin = QSpinBox()
        self.uniqueness_spin.setRange(5, 15)
        self.uniqueness_spin.setValue(self.config.get('stereo.uniqueness_ratio', 10))
        self.uniqueness_spin.valueChanged.connect(self.on_stereo_params_changed)
        params_layout.addRow("Uniqueness Ratio:", self.uniqueness_spin)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        layout.addStretch()
        return tab

    def create_point_cloud_tab(self):
        """Create point cloud controls tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Filtering
        filter_group = QGroupBox("Filtering")
        filter_layout = QVBoxLayout()

        self.downsample_check = QCheckBox("Enable Voxel Downsampling")
        self.downsample_check.setChecked(self.config.get('point_cloud.downsample_enabled', True))
        self.downsample_check.stateChanged.connect(self.on_point_cloud_params_changed)
        filter_layout.addWidget(self.downsample_check)

        voxel_layout = QHBoxLayout()
        voxel_layout.addWidget(QLabel("Voxel Size:"))
        self.voxel_size_spin = QDoubleSpinBox()
        self.voxel_size_spin.setRange(0.001, 0.1)
        self.voxel_size_spin.setSingleStep(0.001)
        self.voxel_size_spin.setDecimals(3)
        self.voxel_size_spin.setValue(self.config.get('point_cloud.voxel_size', 0.01))
        self.voxel_size_spin.valueChanged.connect(self.on_point_cloud_params_changed)
        voxel_layout.addWidget(self.voxel_size_spin)
        filter_layout.addLayout(voxel_layout)

        self.outlier_check = QCheckBox("Statistical Outlier Removal")
        self.outlier_check.setChecked(True)
        self.outlier_check.stateChanged.connect(self.on_point_cloud_params_changed)
        filter_layout.addWidget(self.outlier_check)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Color mode
        color_group = QGroupBox("Color Mode")
        color_layout = QVBoxLayout()

        self.color_combo = QComboBox()
        self.color_combo.addItems(["RGB", "Depth", "Height"])
        self.color_combo.setCurrentText(self.config.get('point_cloud.color_mode', 'rgb').upper())
        self.color_combo.currentTextChanged.connect(self.on_point_cloud_params_changed)
        color_layout.addWidget(self.color_combo)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        layout.addStretch()
        return tab

    def create_slam_tab(self):
        """Create SLAM controls tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Enable/Disable
        enable_group = QGroupBox("SLAM Control")
        enable_layout = QVBoxLayout()

        self.slam_enable_check = QCheckBox("Enable SLAM")
        self.slam_enable_check.stateChanged.connect(
            lambda state: self.slam_toggled.emit(state == Qt.CheckState.Checked.value)
        )
        enable_layout.addWidget(self.slam_enable_check)

        enable_group.setLayout(enable_layout)
        layout.addWidget(enable_group)

        # Feature detector
        feature_group = QGroupBox("Feature Detection")
        feature_layout = QFormLayout()

        self.feature_combo = QComboBox()
        self.feature_combo.addItems(["ORB", "SIFT", "AKAZE"])
        self.feature_combo.setCurrentText(self.config.get('slam.feature_type', 'ORB'))
        feature_layout.addRow("Feature Type:", self.feature_combo)

        self.num_features_spin = QSpinBox()
        self.num_features_spin.setRange(100, 5000)
        self.num_features_spin.setValue(self.config.get('slam.num_features', 1000))
        feature_layout.addRow("Num Features:", self.num_features_spin)

        feature_group.setLayout(feature_layout)
        layout.addWidget(feature_group)

        # Status
        self.slam_status_label = QLabel("Status: Disabled")
        self.slam_status_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(self.slam_status_label)

        layout.addStretch()
        return tab

    def create_export_tab(self):
        """Create export controls tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Point cloud export
        pc_group = QGroupBox("Point Cloud")
        pc_layout = QVBoxLayout()

        for fmt in ["PLY", "PCD", "XYZ"]:
            btn = QPushButton(f"Export as {fmt}")
            btn.clicked.connect(lambda checked, f=fmt: self.export_requested.emit(f"pointcloud_{f}"))
            pc_layout.addWidget(btn)

        pc_group.setLayout(pc_layout)
        layout.addWidget(pc_group)

        # Mesh export
        mesh_group = QGroupBox("Mesh")
        mesh_layout = QVBoxLayout()

        for fmt in ["OBJ", "STL", "PLY"]:
            btn = QPushButton(f"Export as {fmt}")
            btn.clicked.connect(lambda checked, f=fmt: self.export_requested.emit(f"mesh_{f}"))
            mesh_layout.addWidget(btn)

        mesh_group.setLayout(mesh_layout)
        layout.addWidget(mesh_group)

        # Occupancy map export
        occ_btn = QPushButton("Export Occupancy Map")
        occ_btn.clicked.connect(lambda: self.export_requested.emit("occupancy"))
        layout.addWidget(occ_btn)

        layout.addStretch()
        return tab

    def create_metrics_tab(self):
        """Create metrics display tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Metrics display
        metrics_group = QGroupBox("Real-Time Metrics")
        metrics_layout = QFormLayout()

        self.fps_metric = QLabel("0 FPS")
        metrics_layout.addRow("Frame Rate:", self.fps_metric)

        self.points_metric = QLabel("0")
        metrics_layout.addRow("Point Count:", self.points_metric)

        self.processing_metric = QLabel("0 ms")
        metrics_layout.addRow("Processing Time:", self.processing_metric)

        self.memory_metric = QLabel("0 MB")
        metrics_layout.addRow("Memory Usage:", self.memory_metric)

        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)

        # Console log
        log_group = QGroupBox("Console Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-family: monospace;")
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()
        return tab

    def on_stereo_params_changed(self):
        """Handle stereo parameter changes"""
        params = {
            'algorithm': self.stereo_algo_combo.currentText(),
            'num_disparities': self.num_disp_spin.value(),
            'block_size': self.block_size_spin.value(),
            'uniqueness_ratio': self.uniqueness_spin.value()
        }
        self.stereo_params_changed.emit(params)

    def on_point_cloud_params_changed(self):
        """Handle point cloud parameter changes"""
        params = {
            'downsample_enabled': self.downsample_check.isChecked(),
            'voxel_size': self.voxel_size_spin.value(),
            'outlier_removal': self.outlier_check.isChecked(),
            'color_mode': self.color_combo.currentText().lower()
        }
        self.point_cloud_params_changed.emit(params)

    def update_metrics(self, fps: float, points: int, processing_time: float, memory: float):
        """Update metrics display"""
        self.fps_metric.setText(f"{fps:.1f} FPS")
        self.points_metric.setText(f"{points:,}")
        self.processing_metric.setText(f"{processing_time:.1f} ms")
        self.memory_metric.setText(f"{memory:.1f} MB")

    def add_log_message(self, message: str):
        """Add message to console log"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def update_slam_status(self, is_enabled: bool, num_poses: int = 0, num_points: int = 0):
        """Update SLAM status"""
        if is_enabled:
            self.slam_status_label.setText(
                f"Status: Active - {num_poses} poses, {num_points} points"
            )
        else:
            self.slam_status_label.setText("Status: Disabled")
