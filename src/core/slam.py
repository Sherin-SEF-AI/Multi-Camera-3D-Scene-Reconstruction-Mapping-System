"""
Visual SLAM Module
Feature-based visual odometry and mapping
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class FeatureType(Enum):
    """Feature detector types"""
    ORB = "ORB"
    SIFT = "SIFT"
    AKAZE = "AKAZE"


@dataclass
class CameraPose:
    """Represents camera pose (position and orientation)"""
    R: np.ndarray  # 3x3 rotation matrix
    t: np.ndarray  # 3x1 translation vector
    timestamp: float
    frame_id: int


@dataclass
class MapPoint:
    """3D map point"""
    position: np.ndarray  # 3D position
    descriptor: np.ndarray  # Feature descriptor
    observations: List[int]  # Frame IDs where this point was observed
    color: Optional[np.ndarray] = None


class VisualSLAM:
    """Visual SLAM system for camera tracking and mapping"""

    def __init__(self, feature_type: str = "ORB", num_features: int = 1000):
        """
        Initialize Visual SLAM

        Args:
            feature_type: Type of feature detector (ORB, SIFT, AKAZE)
            num_features: Maximum number of features to detect
        """
        self.feature_type = feature_type
        self.num_features = num_features

        # Feature detector and matcher
        self.detector = self._create_detector()
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING if feature_type == "ORB" else cv2.NORM_L2,
                                     crossCheck=False)

        # Camera trajectory
        self.poses: List[CameraPose] = []
        self.current_pose = np.eye(4)  # 4x4 transformation matrix

        # Map points
        self.map_points: List[MapPoint] = []

        # Previous frame data
        self.prev_frame = None
        self.prev_keypoints = None
        self.prev_descriptors = None

        # Camera intrinsics (must be set before use)
        self.camera_matrix: Optional[np.ndarray] = None
        self.dist_coeffs: Optional[np.ndarray] = None

        # Parameters
        self.min_inliers = 10
        self.ransac_threshold = 1.0

        self.frame_count = 0

    def _create_detector(self):
        """Create feature detector based on type"""
        if self.feature_type == "ORB":
            return cv2.ORB_create(nfeatures=self.num_features)
        elif self.feature_type == "SIFT":
            return cv2.SIFT_create(nfeatures=self.num_features)
        elif self.feature_type == "AKAZE":
            return cv2.AKAZE_create()
        else:
            return cv2.ORB_create(nfeatures=self.num_features)

    def set_camera_intrinsics(self, camera_matrix: np.ndarray,
                             dist_coeffs: Optional[np.ndarray] = None) -> None:
        """
        Set camera intrinsic parameters

        Args:
            camera_matrix: 3x3 camera matrix
            dist_coeffs: Distortion coefficients
        """
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs if dist_coeffs is not None else np.zeros(5)

    def detect_features(self, image: np.ndarray) -> Tuple[List, np.ndarray]:
        """
        Detect features in image

        Args:
            image: Input image

        Returns:
            Tuple of (keypoints, descriptors)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Detect and compute
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)

        return keypoints, descriptors

    def match_features(self, desc1: np.ndarray, desc2: np.ndarray) -> List[cv2.DMatch]:
        """
        Match features between two frames

        Args:
            desc1: Descriptors from frame 1
            desc2: Descriptors from frame 2

        Returns:
            List of matches
        """
        if desc1 is None or desc2 is None or len(desc1) == 0 or len(desc2) == 0:
            return []

        # KNN matching with ratio test
        matches = self.matcher.knnMatch(desc1, desc2, k=2)

        # Apply ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)

        return good_matches

    def estimate_pose(self, kp1: List, kp2: List, matches: List[cv2.DMatch]) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Estimate camera pose from matched features

        Args:
            kp1: Keypoints from frame 1
            kp2: Keypoints from frame 2
            matches: Feature matches

        Returns:
            Tuple of (R, t, inliers) or None if estimation fails
        """
        if len(matches) < self.min_inliers or self.camera_matrix is None:
            return None

        # Extract matched keypoints
        pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
        pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

        # Estimate essential matrix
        E, mask = cv2.findEssentialMat(
            pts1, pts2,
            self.camera_matrix,
            method=cv2.RANSAC,
            prob=0.999,
            threshold=self.ransac_threshold
        )

        if E is None:
            return None

        # Recover pose from essential matrix
        _, R, t, mask = cv2.recoverPose(E, pts1, pts2, self.camera_matrix, mask=mask)

        inliers = mask.ravel().astype(bool)
        num_inliers = np.sum(inliers)

        if num_inliers < self.min_inliers:
            return None

        return R, t, inliers

    def process_frame(self, image: np.ndarray, timestamp: float = 0.0) -> bool:
        """
        Process a new frame for SLAM

        Args:
            image: Input image
            timestamp: Frame timestamp

        Returns:
            True if pose was successfully estimated
        """
        # Detect features
        keypoints, descriptors = self.detect_features(image)

        if descriptors is None or len(keypoints) == 0:
            return False

        # First frame initialization
        if self.prev_frame is None:
            self.prev_frame = image
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors

            # Add initial pose
            R = np.eye(3)
            t = np.zeros((3, 1))
            self.poses.append(CameraPose(R, t, timestamp, self.frame_count))

            self.frame_count += 1
            return True

        # Match features with previous frame
        matches = self.match_features(self.prev_descriptors, descriptors)

        if len(matches) < self.min_inliers:
            self.prev_frame = image
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            self.frame_count += 1
            return False

        # Estimate pose
        result = self.estimate_pose(self.prev_keypoints, keypoints, matches)

        if result is None:
            self.prev_frame = image
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            self.frame_count += 1
            return False

        R, t, inliers = result

        # Update current pose (accumulate transformation)
        T_increment = np.eye(4)
        T_increment[:3, :3] = R
        T_increment[:3, 3:4] = t

        self.current_pose = self.current_pose @ T_increment

        # Store pose
        current_R = self.current_pose[:3, :3]
        current_t = self.current_pose[:3, 3:4]
        self.poses.append(CameraPose(current_R, current_t, timestamp, self.frame_count))

        # Triangulate 3D points for inlier matches
        self._triangulate_points(keypoints, matches, inliers, image)

        # Update previous frame data
        self.prev_frame = image
        self.prev_keypoints = keypoints
        self.prev_descriptors = descriptors

        self.frame_count += 1
        return True

    def _triangulate_points(self, keypoints: List, matches: List[cv2.DMatch],
                           inliers: np.ndarray, image: np.ndarray) -> None:
        """
        Triangulate 3D points from matched features

        Args:
            keypoints: Current frame keypoints
            matches: Feature matches
            inliers: Inlier mask
            image: Current frame image for color
        """
        if len(self.poses) < 2:
            return

        # Get previous and current poses
        prev_pose = self.poses[-2]
        curr_pose = self.poses[-1]

        # Create projection matrices
        P1 = self.camera_matrix @ np.hstack([prev_pose.R, prev_pose.t])
        P2 = self.camera_matrix @ np.hstack([curr_pose.R, curr_pose.t])

        # Extract inlier matches
        inlier_matches = [m for i, m in enumerate(matches) if inliers[i]]

        if len(inlier_matches) < 4:
            return

        # Get 2D points
        pts1 = np.float32([self.prev_keypoints[m.queryIdx].pt for m in inlier_matches]).T
        pts2 = np.float32([keypoints[m.trainIdx].pt for m in inlier_matches]).T

        # Triangulate
        points_4d = cv2.triangulatePoints(P1, P2, pts1, pts2)
        points_3d = points_4d[:3] / points_4d[3]  # Convert to 3D

        # Add to map (limit to prevent memory overflow)
        max_new_points = 100
        for i, match in enumerate(inlier_matches[:max_new_points]):
            point_3d = points_3d[:, i]

            # Get color from image
            kp = keypoints[match.trainIdx]
            x, y = int(kp.pt[0]), int(kp.pt[1])
            if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
                color = image[y, x] / 255.0 if len(image.shape) == 3 else None
            else:
                color = None

            # Get descriptor
            descriptor = self.prev_descriptors[match.queryIdx]

            # Create map point
            map_point = MapPoint(
                position=point_3d,
                descriptor=descriptor,
                observations=[self.frame_count - 1, self.frame_count],
                color=color
            )

            self.map_points.append(map_point)

    def get_trajectory(self) -> np.ndarray:
        """
        Get camera trajectory as Nx3 array of positions

        Returns:
            Nx3 array of camera positions
        """
        if len(self.poses) == 0:
            return np.array([])

        positions = np.array([pose.t.flatten() for pose in self.poses])
        return positions

    def get_map_points_array(self) -> np.ndarray:
        """
        Get map points as Nx3 array

        Returns:
            Nx3 array of 3D points
        """
        if len(self.map_points) == 0:
            return np.array([])

        points = np.array([mp.position for mp in self.map_points])
        return points

    def get_map_colors(self) -> Optional[np.ndarray]:
        """
        Get colors for map points

        Returns:
            Nx3 array of colors or None
        """
        if len(self.map_points) == 0:
            return None

        colors = []
        for mp in self.map_points:
            if mp.color is not None:
                colors.append(mp.color)
            else:
                colors.append([0.5, 0.5, 0.5])  # Gray for points without color

        return np.array(colors)

    def reset(self) -> None:
        """Reset SLAM system"""
        self.poses.clear()
        self.map_points.clear()
        self.current_pose = np.eye(4)
        self.prev_frame = None
        self.prev_keypoints = None
        self.prev_descriptors = None
        self.frame_count = 0

    def get_current_position(self) -> np.ndarray:
        """Get current camera position"""
        return self.current_pose[:3, 3]

    def get_num_map_points(self) -> int:
        """Get number of map points"""
        return len(self.map_points)

    def save_trajectory(self, filepath: str) -> bool:
        """
        Save trajectory to file

        Args:
            filepath: Output file path

        Returns:
            True if successful
        """
        try:
            trajectory = self.get_trajectory()
            np.savetxt(filepath, trajectory, fmt='%.6f', header='x y z')
            return True
        except Exception as e:
            print(f"Error saving trajectory: {e}")
            return False
