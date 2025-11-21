"""
Calibration Dialog
GUI dialogs for camera calibration workflows
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QSpinBox, QProgressBar,
                             QTextEdit, QGroupBox, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
import numpy as np
from typing import Optional, List
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.calibration import CalibrationManager
from core.camera_manager import CameraManager


class IntrinsicCalibrationDialog(QDialog):
    """Dialog for intrinsic camera calibration"""

    calibration_complete = pyqtSignal(int, object)  # camera_id, calibration_result

    def __init__(self, camera_manager: CameraManager, calibration_manager: CalibrationManager,
                 parent=None):
        super().__init__(parent)

        self.camera_manager = camera_manager
        self.calibration_manager = calibration_manager
        self.current_camera_id = 0
        self.target_images = 20
        self.is_capturing = False
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self.update_preview)

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Intrinsic Camera Calibration")
        self.resize(900, 700)

        layout = QVBoxLayout()

        # Camera selection group
        camera_group = QGroupBox("Camera Selection")
        camera_layout = QHBoxLayout()

        camera_layout.addWidget(QLabel("Select Camera:"))
        self.camera_combo = QComboBox()

        # Populate camera list
        for i, camera in enumerate(self.camera_manager.cameras):
            self.camera_combo.addItem(f"Camera {i}: {camera.name}", i)

        self.camera_combo.currentIndexChanged.connect(self.on_camera_changed)
        camera_layout.addWidget(self.camera_combo)
        camera_layout.addStretch()

        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)

        # Calibration settings group
        settings_group = QGroupBox("Calibration Settings")
        settings_layout = QGridLayout()

        settings_layout.addWidget(QLabel("Target Images:"), 0, 0)
        self.target_spin = QSpinBox()
        self.target_spin.setMinimum(10)
        self.target_spin.setMaximum(50)
        self.target_spin.setValue(self.target_images)
        self.target_spin.valueChanged.connect(self.on_target_changed)
        settings_layout.addWidget(self.target_spin, 0, 1)

        settings_layout.addWidget(QLabel("Chessboard Size:"), 1, 0)
        chessboard_label = QLabel(f"{self.calibration_manager.chessboard_size[0]}x"
                                 f"{self.calibration_manager.chessboard_size[1]}")
        settings_layout.addWidget(chessboard_label, 1, 1)

        settings_layout.addWidget(QLabel("Square Size:"), 2, 0)
        square_label = QLabel(f"{self.calibration_manager.square_size} mm")
        settings_layout.addWidget(square_label, 2, 1)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Preview area
        preview_group = QGroupBox("Camera Preview")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(640, 480)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("QLabel { background-color: black; }")
        preview_layout.addWidget(self.preview_label)

        self.status_label = QLabel("Press 'Start Capture' to begin")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.status_label)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.target_images)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Images captured: 0 / 20")
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Results section
        results_group = QGroupBox("Calibration Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(100)
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_capture_btn = QPushButton("Start Capture")
        self.start_capture_btn.clicked.connect(self.start_capture)
        button_layout.addWidget(self.start_capture_btn)

        self.capture_btn = QPushButton("Capture Image")
        self.capture_btn.setEnabled(False)
        self.capture_btn.clicked.connect(self.capture_image)
        button_layout.addWidget(self.capture_btn)

        self.calibrate_btn = QPushButton("Calibrate")
        self.calibrate_btn.setEnabled(False)
        self.calibrate_btn.clicked.connect(self.perform_calibration)
        button_layout.addWidget(self.calibrate_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_calibration)
        button_layout.addWidget(self.reset_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_camera_changed(self, index):
        """Handle camera selection change"""
        self.current_camera_id = self.camera_combo.currentData()
        self.reset_calibration()

    def on_target_changed(self, value):
        """Handle target images change"""
        self.target_images = value
        self.progress_bar.setMaximum(value)
        self.update_progress_label()

    def start_capture(self):
        """Start capture mode"""
        if not self.is_capturing:
            self.is_capturing = True
            self.start_capture_btn.setText("Stop Capture")
            self.capture_btn.setEnabled(True)
            self.calibrate_btn.setEnabled(False)
            self.camera_combo.setEnabled(False)

            # Start preview timer
            self.capture_timer.start(33)  # ~30 FPS
            self.status_label.setText("Position chessboard in view and click 'Capture Image'")
        else:
            self.stop_capture()

    def stop_capture(self):
        """Stop capture mode"""
        self.is_capturing = False
        self.start_capture_btn.setText("Start Capture")
        self.capture_btn.setEnabled(False)
        self.camera_combo.setEnabled(True)
        self.capture_timer.stop()

        # Check if enough images captured
        num_images = len(self.calibration_manager.calibration_images.get(self.current_camera_id, []))
        if num_images >= 10:
            self.calibrate_btn.setEnabled(True)
            self.status_label.setText(f"Captured {num_images} images. Ready to calibrate.")
        else:
            self.status_label.setText(f"Need at least 10 images. Currently have {num_images}.")

    def update_preview(self):
        """Update preview with current camera frame"""
        camera = self.camera_manager.get_camera(self.current_camera_id)
        if camera is None:
            return

        frame = camera.get_latest_frame()
        if frame is None:
            return

        # Try to detect chessboard
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(
            gray,
            self.calibration_manager.chessboard_size,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK
        )

        # Draw corners if found
        display_frame = frame.copy()
        if ret:
            cv2.drawChessboardCorners(
                display_frame,
                self.calibration_manager.chessboard_size,
                corners,
                ret
            )
            cv2.putText(display_frame, "Chessboard Detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(display_frame, "Chessboard Not Detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Convert to QPixmap and display
        self.display_frame(display_frame)

    def capture_image(self):
        """Capture current frame for calibration"""
        camera = self.camera_manager.get_camera(self.current_camera_id)
        if camera is None:
            return

        frame = camera.get_latest_frame()
        if frame is None:
            return

        # Add calibration image
        success, image_with_corners = self.calibration_manager.add_calibration_image(
            self.current_camera_id, frame
        )

        if success:
            num_images = len(self.calibration_manager.calibration_images[self.current_camera_id])
            self.progress_bar.setValue(num_images)
            self.update_progress_label()
            self.status_label.setText(f"✓ Image {num_images} captured successfully!")

            # Display captured image with corners briefly
            self.display_frame(image_with_corners)

            # Check if target reached
            if num_images >= self.target_images:
                self.stop_capture()
        else:
            self.status_label.setText("✗ Failed to detect chessboard. Try again.")
            QMessageBox.warning(
                self,
                "Detection Failed",
                "Could not detect chessboard pattern. Ensure:\n"
                "- Pattern is fully visible\n"
                "- Good lighting conditions\n"
                "- Pattern is flat and not blurry"
            )

    def perform_calibration(self):
        """Perform camera calibration"""
        self.status_label.setText("Calibrating... Please wait.")
        self.calibrate_btn.setEnabled(False)

        # Perform calibration
        result = self.calibration_manager.calibrate_camera_intrinsic(self.current_camera_id)

        if result is not None:
            # Display results
            results_text = f"Calibration Successful!\n\n"
            results_text += f"Camera: {self.current_camera_id}\n"
            results_text += f"Reprojection Error: {result.reprojection_error:.4f} pixels\n"
            results_text += f"Image Size: {result.image_size[0]} x {result.image_size[1]}\n"
            results_text += f"Focal Length (fx, fy): {result.camera_matrix[0, 0]:.2f}, "
            results_text += f"{result.camera_matrix[1, 1]:.2f}\n"
            results_text += f"Principal Point (cx, cy): {result.camera_matrix[0, 2]:.2f}, "
            results_text += f"{result.camera_matrix[1, 2]:.2f}\n"

            self.results_text.setText(results_text)
            self.status_label.setText("Calibration complete!")

            # Emit signal
            self.calibration_complete.emit(self.current_camera_id, result)

            QMessageBox.information(
                self,
                "Calibration Complete",
                f"Camera {self.current_camera_id} calibrated successfully!\n"
                f"Reprojection error: {result.reprojection_error:.4f} pixels"
            )
        else:
            self.results_text.setText("Calibration failed. Try capturing more images.")
            self.status_label.setText("Calibration failed.")
            self.calibrate_btn.setEnabled(True)

            QMessageBox.critical(
                self,
                "Calibration Failed",
                "Failed to calibrate camera. Try:\n"
                "- Capturing more images\n"
                "- Using different angles and distances\n"
                "- Ensuring chessboard pattern is clearly visible"
            )

    def reset_calibration(self):
        """Reset calibration data for current camera"""
        if self.current_camera_id in self.calibration_manager.calibration_images:
            del self.calibration_manager.calibration_images[self.current_camera_id]
        if self.current_camera_id in self.calibration_manager.object_points:
            del self.calibration_manager.object_points[self.current_camera_id]
        if self.current_camera_id in self.calibration_manager.image_points:
            del self.calibration_manager.image_points[self.current_camera_id]

        self.progress_bar.setValue(0)
        self.update_progress_label()
        self.results_text.clear()
        self.status_label.setText("Reset complete. Press 'Start Capture' to begin.")
        self.calibrate_btn.setEnabled(False)

    def update_progress_label(self):
        """Update progress label"""
        num_images = len(self.calibration_manager.calibration_images.get(self.current_camera_id, []))
        self.progress_label.setText(f"Images captured: {num_images} / {self.target_images}")

    def display_frame(self, frame: np.ndarray):
        """Display frame in preview label"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Resize to fit preview area while maintaining aspect ratio
        h, w = rgb_frame.shape[:2]
        preview_w = self.preview_label.width()
        preview_h = self.preview_label.height()

        scale = min(preview_w / w, preview_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = cv2.resize(rgb_frame, (new_w, new_h))

        # Convert to QImage and display
        bytes_per_line = 3 * new_w
        q_image = QImage(resized.data, new_w, new_h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        self.preview_label.setPixmap(pixmap)

    def closeEvent(self, event):
        """Handle dialog close"""
        if self.is_capturing:
            self.stop_capture()
        event.accept()


class StereoCalibrationDialog(QDialog):
    """Dialog for stereo camera calibration"""

    calibration_complete = pyqtSignal(tuple, object)  # (camera_id1, camera_id2), calibration_result

    def __init__(self, camera_manager: CameraManager, calibration_manager: CalibrationManager,
                 parent=None):
        super().__init__(parent)

        self.camera_manager = camera_manager
        self.calibration_manager = calibration_manager
        self.camera_id1 = 0
        self.camera_id2 = 1

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Stereo Camera Calibration")
        self.resize(900, 600)

        layout = QVBoxLayout()

        # Camera pair selection
        camera_group = QGroupBox("Camera Pair Selection")
        camera_layout = QGridLayout()

        camera_layout.addWidget(QLabel("First Camera:"), 0, 0)
        self.camera1_combo = QComboBox()
        for i, camera in enumerate(self.camera_manager.cameras):
            self.camera1_combo.addItem(f"Camera {i}: {camera.name}", i)
        camera_layout.addWidget(self.camera1_combo, 0, 1)

        camera_layout.addWidget(QLabel("Second Camera:"), 1, 0)
        self.camera2_combo = QComboBox()
        for i, camera in enumerate(self.camera_manager.cameras):
            self.camera2_combo.addItem(f"Camera {i}: {camera.name}", i)
        self.camera2_combo.setCurrentIndex(1)
        camera_layout.addWidget(self.camera2_combo, 1, 1)

        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)

        # Instructions
        instructions_group = QGroupBox("Instructions")
        instructions_layout = QVBoxLayout()

        instructions = QLabel(
            "Stereo calibration requires:\n"
            "1. Both cameras must be intrinsically calibrated first\n"
            "2. Both cameras must see the same chessboard pattern simultaneously\n"
            "3. Capture at least 10 image pairs\n\n"
            "Make sure to calibrate individual cameras before proceeding."
        )
        instructions.setWordWrap(True)
        instructions_layout.addWidget(instructions)

        instructions_group.setLayout(instructions_layout)
        layout.addWidget(instructions_group)

        # Status section
        status_group = QGroupBox("Calibration Status")
        status_layout = QVBoxLayout()

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        status_layout.addWidget(self.status_text)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Results section
        results_group = QGroupBox("Calibration Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.check_btn = QPushButton("Check Prerequisites")
        self.check_btn.clicked.connect(self.check_prerequisites)
        button_layout.addWidget(self.check_btn)

        self.calibrate_btn = QPushButton("Calibrate Stereo Pair")
        self.calibrate_btn.clicked.connect(self.perform_calibration)
        button_layout.addWidget(self.calibrate_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Check prerequisites on startup
        QTimer.singleShot(100, self.check_prerequisites)

    def check_prerequisites(self):
        """Check if prerequisites are met for stereo calibration"""
        self.camera_id1 = self.camera1_combo.currentData()
        self.camera_id2 = self.camera2_combo.currentData()

        status = "Prerequisite Check:\n\n"

        # Check if cameras are different
        if self.camera_id1 == self.camera_id2:
            status += "✗ Error: Please select two different cameras\n"
            self.calibrate_btn.setEnabled(False)
            self.status_text.setText(status)
            return

        # Check intrinsic calibration for camera 1
        if self.camera_id1 in self.calibration_manager.intrinsic_calibrations:
            calib1 = self.calibration_manager.intrinsic_calibrations[self.camera_id1]
            status += f"✓ Camera {self.camera_id1} intrinsic calibration found\n"
            status += f"  Error: {calib1.reprojection_error:.4f} pixels\n"
        else:
            status += f"✗ Camera {self.camera_id1} not intrinsically calibrated\n"

        # Check intrinsic calibration for camera 2
        if self.camera_id2 in self.calibration_manager.intrinsic_calibrations:
            calib2 = self.calibration_manager.intrinsic_calibrations[self.camera_id2]
            status += f"✓ Camera {self.camera_id2} intrinsic calibration found\n"
            status += f"  Error: {calib2.reprojection_error:.4f} pixels\n"
        else:
            status += f"✗ Camera {self.camera_id2} not intrinsically calibrated\n"

        # Check if enough calibration images exist
        cam1_images = len(self.calibration_manager.image_points.get(self.camera_id1, []))
        cam2_images = len(self.calibration_manager.image_points.get(self.camera_id2, []))

        min_images = min(cam1_images, cam2_images)
        status += f"\nCalibration images: {min_images} pairs available\n"

        if min_images < 10:
            status += "✗ Need at least 10 image pairs for stereo calibration\n"

        # Enable calibration button if all prerequisites met
        can_calibrate = (
            self.camera_id1 != self.camera_id2 and
            self.camera_id1 in self.calibration_manager.intrinsic_calibrations and
            self.camera_id2 in self.calibration_manager.intrinsic_calibrations and
            min_images >= 10
        )

        self.calibrate_btn.setEnabled(can_calibrate)

        if can_calibrate:
            status += "\n✓ Ready for stereo calibration!"
        else:
            status += "\n✗ Prerequisites not met. Please calibrate individual cameras first."

        self.status_text.setText(status)

    def perform_calibration(self):
        """Perform stereo calibration"""
        self.camera_id1 = self.camera1_combo.currentData()
        self.camera_id2 = self.camera2_combo.currentData()

        self.calibrate_btn.setEnabled(False)
        self.status_text.append("\n\nPerforming stereo calibration...")

        # Perform stereo calibration
        result = self.calibration_manager.calibrate_stereo(
            self.camera_id1,
            self.camera_id2
        )

        if result is not None:
            # Display results
            results_text = f"Stereo Calibration Successful!\n\n"
            results_text += f"Camera Pair: {self.camera_id1} - {self.camera_id2}\n"
            results_text += f"Reprojection Error: {result.reprojection_error:.4f} pixels\n"
            results_text += f"Baseline: {result.baseline:.2f} mm\n"
            results_text += f"Rotation:\n{result.R}\n"
            results_text += f"Translation:\n{result.T}\n"

            self.results_text.setText(results_text)
            self.status_text.append("✓ Stereo calibration complete!")

            # Emit signal
            self.calibration_complete.emit((self.camera_id1, self.camera_id2), result)

            QMessageBox.information(
                self,
                "Calibration Complete",
                f"Stereo calibration for cameras {self.camera_id1} and {self.camera_id2} "
                f"completed successfully!\n"
                f"Reprojection error: {result.reprojection_error:.4f} pixels\n"
                f"Baseline: {result.baseline:.2f} mm"
            )
        else:
            self.results_text.setText("Stereo calibration failed.")
            self.status_text.append("✗ Stereo calibration failed!")
            self.calibrate_btn.setEnabled(True)

            QMessageBox.critical(
                self,
                "Calibration Failed",
                "Failed to calibrate stereo pair. Ensure:\n"
                "- Both cameras are intrinsically calibrated\n"
                "- Sufficient calibration images are available\n"
                "- Both cameras see the same chessboard pattern"
            )
