"""
Camera Feed Widget
Displays live camera feed from OpenCV in Qt
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
import numpy as np
import cv2


class CameraFeedWidget(QWidget):
    """Widget to display a single camera feed"""

    def __init__(self, camera_id: int, camera_manager, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self.camera_manager = camera_manager
        self.current_frame = None

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header with camera info and controls
        header_layout = QHBoxLayout()

        # Camera label
        self.camera_label = QLabel(f"Camera {self.camera_id}")
        self.camera_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.camera_label)

        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: red; font-size: 16px;")
        header_layout.addWidget(self.status_indicator)

        header_layout.addStretch()

        # FPS label
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet("font-size: 10px;")
        header_layout.addWidget(self.fps_label)

        layout.addLayout(header_layout)

        # Video display label
        self.video_label = QLabel()
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setMaximumSize(640, 480)
        self.video_label.setScaledContents(True)
        self.video_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #555;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("No Camera")
        layout.addWidget(self.video_label)

        # Controls
        controls_layout = QHBoxLayout()

        # Resolution selector
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "800x600", "1280x720", "1920x1080"])
        self.resolution_combo.setCurrentIndex(0)
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        controls_layout.addWidget(QLabel("Res:"))
        controls_layout.addWidget(self.resolution_combo)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

    @pyqtSlot(np.ndarray)
    def update_frame(self, frame: np.ndarray):
        """Update the displayed frame"""
        if frame is None:
            return

        self.current_frame = frame

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get dimensions
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        # Create QImage
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # Create pixmap and display
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

    @pyqtSlot(float)
    def update_fps(self, fps: float):
        """Update FPS display"""
        self.fps_label.setText(f"FPS: {fps:.1f}")

    def update_status(self, is_active: bool):
        """Update camera status indicator"""
        if is_active:
            self.status_indicator.setStyleSheet("color: green; font-size: 16px;")
            self.camera_label.setText(f"Camera {self.camera_id} - Active")
        else:
            self.status_indicator.setStyleSheet("color: red; font-size: 16px;")
            self.camera_label.setText(f"Camera {self.camera_id} - Inactive")

    def on_resolution_changed(self, resolution_text: str):
        """Handle resolution change"""
        try:
            width, height = map(int, resolution_text.split('x'))
            camera = self.camera_manager.get_camera(self.camera_id)
            if camera:
                camera.set_resolution(width, height)
        except Exception as e:
            print(f"Error changing resolution: {e}")
