"""
Camera Calibration Module
Handles intrinsic and extrinsic calibration for multiple cameras
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict
import json
from datetime import datetime


@dataclass
class IntrinsicCalibration:
    """Stores intrinsic camera calibration parameters"""
    camera_matrix: np.ndarray  # 3x3 camera matrix
    dist_coeffs: np.ndarray    # Distortion coefficients
    image_size: Tuple[int, int]  # (width, height)
    reprojection_error: float
    calibration_date: str


@dataclass
class StereoCalibration:
    """Stores stereo calibration parameters"""
    R: np.ndarray  # Rotation matrix between cameras
    T: np.ndarray  # Translation vector between cameras
    E: np.ndarray  # Essential matrix
    F: np.ndarray  # Fundamental matrix
    reprojection_error: float
    baseline: float  # Distance between cameras in mm


class CalibrationManager:
    """Manages camera calibration process"""

    def __init__(self, chessboard_size: Tuple[int, int] = (9, 6), square_size: float = 25.0):
        """
        Initialize calibration manager

        Args:
            chessboard_size: Number of internal corners (columns, rows)
            square_size: Size of chessboard squares in mm
        """
        self.chessboard_size = chessboard_size
        self.square_size = square_size

        # Prepare object points for chessboard (in mm)
        self.obj_points_template = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
        self.obj_points_template[:, :2] = np.mgrid[0:chessboard_size[0],
                                                     0:chessboard_size[1]].T.reshape(-1, 2)
        self.obj_points_template *= square_size

        # Storage for calibration images
        self.calibration_images: Dict[int, List[np.ndarray]] = {}
        self.object_points: Dict[int, List[np.ndarray]] = {}
        self.image_points: Dict[int, List[np.ndarray]] = {}

        # Calibration results
        self.intrinsic_calibrations: Dict[int, IntrinsicCalibration] = {}
        self.stereo_calibrations: Dict[Tuple[int, int], StereoCalibration] = {}

    def add_calibration_image(self, camera_id: int, image: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Add calibration image and detect chessboard

        Args:
            camera_id: Camera identifier
            image: Calibration image

        Returns:
            Tuple of (success, image_with_corners_drawn)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Find chessboard corners
        ret, corners = cv2.findChessboardCorners(
            gray,
            self.chessboard_size,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        if ret:
            # Refine corner positions
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

            # Store calibration data
            if camera_id not in self.calibration_images:
                self.calibration_images[camera_id] = []
                self.object_points[camera_id] = []
                self.image_points[camera_id] = []

            self.calibration_images[camera_id].append(image.copy())
            self.object_points[camera_id].append(self.obj_points_template)
            self.image_points[camera_id].append(corners_refined)

            # Draw corners for visualization
            image_with_corners = image.copy()
            cv2.drawChessboardCorners(image_with_corners, self.chessboard_size, corners_refined, ret)

            return True, image_with_corners
        else:
            return False, None

    def calibrate_camera_intrinsic(self, camera_id: int) -> Optional[IntrinsicCalibration]:
        """
        Perform intrinsic calibration for a camera

        Args:
            camera_id: Camera identifier

        Returns:
            IntrinsicCalibration object or None if calibration fails
        """
        if camera_id not in self.image_points or len(self.image_points[camera_id]) == 0:
            print(f"No calibration images for camera {camera_id}")
            return None

        # Get image size from first calibration image
        image_size = self.calibration_images[camera_id][0].shape[1::-1]  # (width, height)

        # Perform calibration
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            self.object_points[camera_id],
            self.image_points[camera_id],
            image_size,
            None,
            None
        )

        if not ret:
            print(f"Calibration failed for camera {camera_id}")
            return None

        # Calculate reprojection error
        total_error = 0
        for i in range(len(self.object_points[camera_id])):
            imgpoints2, _ = cv2.projectPoints(
                self.object_points[camera_id][i],
                rvecs[i],
                tvecs[i],
                camera_matrix,
                dist_coeffs
            )
            error = cv2.norm(self.image_points[camera_id][i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            total_error += error

        mean_error = total_error / len(self.object_points[camera_id])

        # Create calibration object
        calibration = IntrinsicCalibration(
            camera_matrix=camera_matrix,
            dist_coeffs=dist_coeffs,
            image_size=image_size,
            reprojection_error=mean_error,
            calibration_date=datetime.now().isoformat()
        )

        # Store calibration
        self.intrinsic_calibrations[camera_id] = calibration

        print(f"Camera {camera_id} calibrated with reprojection error: {mean_error:.4f}")
        return calibration

    def calibrate_stereo(self, camera_id_1: int, camera_id_2: int) -> Optional[StereoCalibration]:
        """
        Perform stereo calibration between two cameras

        Args:
            camera_id_1: First camera identifier
            camera_id_2: Second camera identifier

        Returns:
            StereoCalibration object or None if calibration fails
        """
        # Check if both cameras have intrinsic calibrations
        if camera_id_1 not in self.intrinsic_calibrations:
            print(f"Camera {camera_id_1} not intrinsically calibrated")
            return None

        if camera_id_2 not in self.intrinsic_calibrations:
            print(f"Camera {camera_id_2} not intrinsically calibrated")
            return None

        # Get intrinsic parameters
        calib1 = self.intrinsic_calibrations[camera_id_1]
        calib2 = self.intrinsic_calibrations[camera_id_2]

        # Find common calibration images (requires synchronized capture)
        # For now, assume images are synchronized by index
        num_images = min(len(self.object_points[camera_id_1]), len(self.object_points[camera_id_2]))

        if num_images == 0:
            print("No common calibration images for stereo calibration")
            return None

        # Perform stereo calibration
        flags = cv2.CALIB_FIX_INTRINSIC  # Use pre-calibrated intrinsic parameters

        ret, _, _, _, _, R, T, E, F = cv2.stereoCalibrate(
            self.object_points[camera_id_1][:num_images],
            self.image_points[camera_id_1][:num_images],
            self.image_points[camera_id_2][:num_images],
            calib1.camera_matrix,
            calib1.dist_coeffs,
            calib2.camera_matrix,
            calib2.dist_coeffs,
            calib1.image_size,
            flags=flags
        )

        if not ret:
            print("Stereo calibration failed")
            return None

        # Calculate baseline (distance between cameras)
        baseline = float(np.linalg.norm(T))

        # Create stereo calibration object
        stereo_calib = StereoCalibration(
            R=R,
            T=T,
            E=E,
            F=F,
            reprojection_error=ret,
            baseline=baseline
        )

        # Store calibration
        self.stereo_calibrations[(camera_id_1, camera_id_2)] = stereo_calib

        print(f"Stereo calibration complete. Baseline: {baseline:.2f}mm, Error: {ret:.4f}")
        return stereo_calib

    def get_rectification_maps(self, camera_id_1: int, camera_id_2: int) -> Optional[Dict[str, Any]]:
        """
        Get stereo rectification maps

        Args:
            camera_id_1: First camera identifier
            camera_id_2: Second camera identifier

        Returns:
            Dictionary containing rectification maps and new camera matrices
        """
        if (camera_id_1, camera_id_2) not in self.stereo_calibrations:
            print("Stereo calibration not found")
            return None

        calib1 = self.intrinsic_calibrations[camera_id_1]
        calib2 = self.intrinsic_calibrations[camera_id_2]
        stereo_calib = self.stereo_calibrations[(camera_id_1, camera_id_2)]

        # Compute rectification transforms
        R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
            calib1.camera_matrix,
            calib1.dist_coeffs,
            calib2.camera_matrix,
            calib2.dist_coeffs,
            calib1.image_size,
            stereo_calib.R,
            stereo_calib.T,
            alpha=0
        )

        # Compute rectification maps
        map1_left, map2_left = cv2.initUndistortRectifyMap(
            calib1.camera_matrix,
            calib1.dist_coeffs,
            R1,
            P1,
            calib1.image_size,
            cv2.CV_32FC1
        )

        map1_right, map2_right = cv2.initUndistortRectifyMap(
            calib2.camera_matrix,
            calib2.dist_coeffs,
            R2,
            P2,
            calib2.image_size,
            cv2.CV_32FC1
        )

        return {
            'map1_left': map1_left,
            'map2_left': map2_left,
            'map1_right': map1_right,
            'map2_right': map2_right,
            'Q': Q,  # Disparity-to-depth mapping matrix
            'P1': P1,
            'P2': P2,
            'roi1': roi1,
            'roi2': roi2
        }

    def undistort_image(self, camera_id: int, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Undistort image using intrinsic calibration

        Args:
            camera_id: Camera identifier
            image: Image to undistort

        Returns:
            Undistorted image or None if calibration not available
        """
        if camera_id not in self.intrinsic_calibrations:
            return None

        calib = self.intrinsic_calibrations[camera_id]
        return cv2.undistort(image, calib.camera_matrix, calib.dist_coeffs)

    def get_num_calibration_images(self, camera_id: int) -> int:
        """Get number of calibration images for camera"""
        return len(self.calibration_images.get(camera_id, []))

    def clear_calibration_images(self, camera_id: Optional[int] = None) -> None:
        """
        Clear calibration images

        Args:
            camera_id: Camera ID to clear, or None to clear all
        """
        if camera_id is None:
            self.calibration_images.clear()
            self.object_points.clear()
            self.image_points.clear()
        else:
            self.calibration_images.pop(camera_id, None)
            self.object_points.pop(camera_id, None)
            self.image_points.pop(camera_id, None)

    def save_calibration(self, filepath: str) -> bool:
        """
        Save all calibrations to file

        Args:
            filepath: Path to save calibration

        Returns:
            True if successful
        """
        try:
            calibration_data = {
                'chessboard_size': self.chessboard_size,
                'square_size': self.square_size,
                'intrinsic_calibrations': {},
                'stereo_calibrations': {}
            }

            # Save intrinsic calibrations
            for cam_id, calib in self.intrinsic_calibrations.items():
                calibration_data['intrinsic_calibrations'][str(cam_id)] = {
                    'camera_matrix': calib.camera_matrix.tolist(),
                    'dist_coeffs': calib.dist_coeffs.tolist(),
                    'image_size': calib.image_size,
                    'reprojection_error': float(calib.reprojection_error),
                    'calibration_date': calib.calibration_date
                }

            # Save stereo calibrations
            for (cam_id_1, cam_id_2), stereo in self.stereo_calibrations.items():
                key = f"{cam_id_1}_{cam_id_2}"
                calibration_data['stereo_calibrations'][key] = {
                    'R': stereo.R.tolist(),
                    'T': stereo.T.tolist(),
                    'E': stereo.E.tolist(),
                    'F': stereo.F.tolist(),
                    'reprojection_error': float(stereo.reprojection_error),
                    'baseline': float(stereo.baseline)
                }

            with open(filepath, 'w') as f:
                json.dump(calibration_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving calibration: {e}")
            return False

    def load_calibration(self, filepath: str) -> bool:
        """
        Load calibrations from file

        Args:
            filepath: Path to calibration file

        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r') as f:
                calibration_data = json.load(f)

            self.chessboard_size = tuple(calibration_data['chessboard_size'])
            self.square_size = calibration_data['square_size']

            # Load intrinsic calibrations
            for cam_id_str, calib_dict in calibration_data['intrinsic_calibrations'].items():
                cam_id = int(cam_id_str)
                self.intrinsic_calibrations[cam_id] = IntrinsicCalibration(
                    camera_matrix=np.array(calib_dict['camera_matrix']),
                    dist_coeffs=np.array(calib_dict['dist_coeffs']),
                    image_size=tuple(calib_dict['image_size']),
                    reprojection_error=calib_dict['reprojection_error'],
                    calibration_date=calib_dict['calibration_date']
                )

            # Load stereo calibrations
            for key, stereo_dict in calibration_data['stereo_calibrations'].items():
                cam_id_1, cam_id_2 = map(int, key.split('_'))
                self.stereo_calibrations[(cam_id_1, cam_id_2)] = StereoCalibration(
                    R=np.array(stereo_dict['R']),
                    T=np.array(stereo_dict['T']),
                    E=np.array(stereo_dict['E']),
                    F=np.array(stereo_dict['F']),
                    reprojection_error=stereo_dict['reprojection_error'],
                    baseline=stereo_dict['baseline']
                )

            return True

        except Exception as e:
            print(f"Error loading calibration: {e}")
            return False
