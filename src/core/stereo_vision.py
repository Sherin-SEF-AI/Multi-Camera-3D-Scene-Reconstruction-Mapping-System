"""
Stereo Vision Module
Handles disparity map computation and depth estimation from stereo pairs
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any, Tuple
from enum import Enum


class StereoAlgorithm(Enum):
    """Available stereo matching algorithms"""
    BM = "Block Matching"
    SGBM = "Semi-Global Block Matching"


class StereoMatcher:
    """Computes disparity and depth maps from stereo image pairs"""

    def __init__(self, algorithm: str = "SGBM"):
        """
        Initialize stereo matcher

        Args:
            algorithm: Stereo matching algorithm ("BM" or "SGBM")
        """
        self.algorithm = algorithm
        self.matcher = None

        # Default parameters
        self.params = {
            'num_disparities': 16 * 5,  # Must be divisible by 16
            'block_size': 15,  # Must be odd, typically 5-25
            'min_disparity': 0,
            'uniqueness_ratio': 10,
            'speckle_window_size': 100,
            'speckle_range': 32,
            'pre_filter_cap': 63,
            'p1': 8 * 3 * 15 ** 2,  # 8*number_of_image_channels*block_size^2
            'p2': 32 * 3 * 15 ** 2  # 32*number_of_image_channels*block_size^2
        }

        self._create_matcher()

    def _create_matcher(self) -> None:
        """Create stereo matcher based on selected algorithm"""
        if self.algorithm == "BM":
            self.matcher = cv2.StereoBM_create()
            self.matcher.setNumDisparities(self.params['num_disparities'])
            self.matcher.setBlockSize(self.params['block_size'])
            self.matcher.setPreFilterCap(self.params['pre_filter_cap'])
            self.matcher.setMinDisparity(self.params['min_disparity'])
            self.matcher.setUniquenessRatio(self.params['uniqueness_ratio'])
            self.matcher.setSpeckleWindowSize(self.params['speckle_window_size'])
            self.matcher.setSpeckleRange(self.params['speckle_range'])

        elif self.algorithm == "SGBM":
            self.matcher = cv2.StereoSGBM_create(
                minDisparity=self.params['min_disparity'],
                numDisparities=self.params['num_disparities'],
                blockSize=self.params['block_size'],
                P1=self.params['p1'],
                P2=self.params['p2'],
                uniquenessRatio=self.params['uniqueness_ratio'],
                speckleWindowSize=self.params['speckle_window_size'],
                speckleRange=self.params['speckle_range'],
                preFilterCap=self.params['pre_filter_cap'],
                mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
            )

    def set_parameter(self, param_name: str, value: Any) -> bool:
        """
        Set stereo matching parameter

        Args:
            param_name: Parameter name
            value: Parameter value

        Returns:
            True if successful
        """
        if param_name not in self.params:
            return False

        # Validate certain parameters
        if param_name == 'num_disparities':
            value = (value // 16) * 16  # Must be divisible by 16
        elif param_name == 'block_size':
            value = value if value % 2 == 1 else value + 1  # Must be odd

        self.params[param_name] = value

        # Update P1 and P2 if block_size changes
        if param_name == 'block_size':
            self.params['p1'] = 8 * 3 * value ** 2
            self.params['p2'] = 32 * 3 * value ** 2

        # Recreate matcher with new parameters
        self._create_matcher()
        return True

    def compute_disparity(self, left_image: np.ndarray, right_image: np.ndarray,
                         rectified: bool = False) -> Optional[np.ndarray]:
        """
        Compute disparity map from stereo pair

        Args:
            left_image: Left camera image
            right_image: Right camera image
            rectified: Whether images are already rectified

        Returns:
            Disparity map (16-bit fixed-point, divide by 16 for actual disparity)
        """
        if self.matcher is None:
            return None

        # Convert to grayscale if needed
        if len(left_image.shape) == 3:
            left_gray = cv2.cvtColor(left_image, cv2.COLOR_BGR2GRAY)
        else:
            left_gray = left_image

        if len(right_image.shape) == 3:
            right_gray = cv2.cvtColor(right_image, cv2.COLOR_BGR2GRAY)
        else:
            right_gray = right_image

        # Ensure same size
        if left_gray.shape != right_gray.shape:
            print("Warning: Stereo images have different sizes")
            return None

        # Compute disparity
        disparity = self.matcher.compute(left_gray, right_gray)

        return disparity

    def compute_depth(self, disparity: np.ndarray, Q: np.ndarray) -> Optional[np.ndarray]:
        """
        Convert disparity map to depth map

        Args:
            disparity: Disparity map from compute_disparity
            Q: Disparity-to-depth mapping matrix from stereo calibration

        Returns:
            Depth map in the same units as calibration (typically mm)
        """
        # Convert from fixed-point to float
        disparity_float = disparity.astype(np.float32) / 16.0

        # Reproject to 3D
        points_3d = cv2.reprojectImageTo3D(disparity_float, Q)

        # Extract depth (Z coordinate)
        depth_map = points_3d[:, :, 2]

        # Filter out invalid depths
        depth_map[depth_map <= 0] = 0
        depth_map[depth_map > 10000] = 0  # Remove extremely far points

        return depth_map

    def get_disparity_visualization(self, disparity: np.ndarray) -> np.ndarray:
        """
        Create color-coded visualization of disparity map

        Args:
            disparity: Disparity map

        Returns:
            Color-coded disparity visualization (BGR image)
        """
        # Normalize to 0-255
        disparity_visual = cv2.normalize(disparity, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        # Apply color map
        disparity_color = cv2.applyColorMap(disparity_visual, cv2.COLORMAP_JET)

        return disparity_color

    def get_depth_visualization(self, depth_map: np.ndarray, max_depth: float = 5000.0) -> np.ndarray:
        """
        Create color-coded visualization of depth map

        Args:
            depth_map: Depth map in mm
            max_depth: Maximum depth for visualization in mm

        Returns:
            Color-coded depth visualization (BGR image)
        """
        # Clip and normalize
        depth_clipped = np.clip(depth_map, 0, max_depth)
        depth_normalized = (depth_clipped / max_depth * 255).astype(np.uint8)

        # Apply color map (inverse - closer is hotter)
        depth_color = cv2.applyColorMap(255 - depth_normalized, cv2.COLORMAP_JET)

        return depth_color

    def filter_disparity(self, disparity: np.ndarray, filter_type: str = "wls") -> np.ndarray:
        """
        Apply post-processing filter to disparity map

        Args:
            disparity: Raw disparity map
            filter_type: Type of filter ("wls", "median", "bilateral")

        Returns:
            Filtered disparity map
        """
        if filter_type == "median":
            # Median filter for noise reduction
            return cv2.medianBlur(disparity, 5)

        elif filter_type == "bilateral":
            # Bilateral filter for edge-preserving smoothing
            disparity_float = disparity.astype(np.float32) / 16.0
            filtered = cv2.bilateralFilter(disparity_float, 9, 75, 75)
            return (filtered * 16).astype(np.int16)

        else:  # WLS filter
            # Weighted Least Squares filter (requires right disparity)
            # For now, just return the original
            return disparity

    def compute_confidence_map(self, disparity: np.ndarray) -> np.ndarray:
        """
        Compute confidence map for disparity

        Args:
            disparity: Disparity map

        Returns:
            Confidence map (0-255, higher is more confident)
        """
        # Simple confidence based on disparity validity
        confidence = np.zeros_like(disparity, dtype=np.uint8)

        # Valid disparities have values > 0
        valid_mask = disparity > 0
        confidence[valid_mask] = 255

        # Apply median filter to smooth confidence
        confidence = cv2.medianBlur(confidence, 5)

        return confidence


class MultiViewStereo:
    """Handles multi-view stereo processing for 3+ cameras"""

    def __init__(self):
        """Initialize multi-view stereo processor"""
        self.stereo_matchers: Dict[Tuple[int, int], StereoMatcher] = {}

    def add_stereo_pair(self, cam_id_1: int, cam_id_2: int, algorithm: str = "SGBM") -> None:
        """
        Add a stereo pair for processing

        Args:
            cam_id_1: First camera ID
            cam_id_2: Second camera ID
            algorithm: Stereo matching algorithm
        """
        self.stereo_matchers[(cam_id_1, cam_id_2)] = StereoMatcher(algorithm)

    def compute_all_disparities(self, images: Dict[int, np.ndarray]) -> Dict[Tuple[int, int], np.ndarray]:
        """
        Compute disparity maps for all stereo pairs

        Args:
            images: Dictionary mapping camera IDs to images

        Returns:
            Dictionary mapping stereo pairs to disparity maps
        """
        disparities = {}

        for (cam_id_1, cam_id_2), matcher in self.stereo_matchers.items():
            if cam_id_1 in images and cam_id_2 in images:
                disparity = matcher.compute_disparity(images[cam_id_1], images[cam_id_2])
                if disparity is not None:
                    disparities[(cam_id_1, cam_id_2)] = disparity

        return disparities

    def fuse_depth_maps(self, depth_maps: Dict[Tuple[int, int], np.ndarray]) -> np.ndarray:
        """
        Fuse multiple depth maps for improved accuracy

        Args:
            depth_maps: Dictionary of depth maps from different stereo pairs

        Returns:
            Fused depth map
        """
        if not depth_maps:
            return None

        # Simple fusion: average valid depths
        depth_stack = []
        for depth_map in depth_maps.values():
            depth_stack.append(depth_map)

        depth_stack = np.array(depth_stack)

        # Compute median depth (more robust than mean)
        fused_depth = np.median(depth_stack, axis=0)

        return fused_depth

    def get_matcher(self, cam_id_1: int, cam_id_2: int) -> Optional[StereoMatcher]:
        """Get stereo matcher for a specific pair"""
        return self.stereo_matchers.get((cam_id_1, cam_id_2))
