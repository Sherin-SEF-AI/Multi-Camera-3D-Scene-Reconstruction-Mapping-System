"""
Camera Panel
Contains all camera feed widgets
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from gui.camera_feed_widget import CameraFeedWidget


class CameraPanel(QWidget):
    """Panel containing all camera feeds"""

    # Signals
    connect_cameras_requested = pyqtSignal()

    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.camera_widgets = []

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Camera Feeds")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)

        # Connect button
        self.connect_btn = QPushButton("Connect Cameras")
        self.connect_btn.clicked.connect(self.on_connect_cameras)
        header_layout.addWidget(self.connect_btn)

        layout.addLayout(header_layout)

        # Create camera feed widgets
        for i in range(3):
            camera_widget = CameraFeedWidget(i, self.camera_manager)
            self.camera_widgets.append(camera_widget)
            layout.addWidget(camera_widget)

        layout.addStretch()

    def on_connect_cameras(self):
        """Handle connect cameras button"""
        self.connect_cameras_requested.emit()

    def get_camera_widget(self, camera_id: int) -> CameraFeedWidget:
        """Get camera widget by ID"""
        if 0 <= camera_id < len(self.camera_widgets):
            return self.camera_widgets[camera_id]
        return None

    def update_camera_status(self):
        """Update all camera status indicators"""
        for i, widget in enumerate(self.camera_widgets):
            is_active = self.camera_manager.is_camera_active(i)
            widget.update_status(is_active)
