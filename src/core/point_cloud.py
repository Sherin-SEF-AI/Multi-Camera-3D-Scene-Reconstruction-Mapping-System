"""
Point Cloud Reconstruction Module
Handles 3D point cloud generation, filtering, and processing
"""

import cv2
import numpy as np
import open3d as o3d
from typing import Optional, Tuple, List
from enum import Enum


class PointCloudProcessor:
    """Processes and manages 3D point clouds"""

    def __init__(self, max_points: int = 1000000):
        """
        Initialize point cloud processor

        Args:
            max_points: Maximum number of points to keep in memory
        """
        self.max_points = max_points
        self.point_cloud = o3d.geometry.PointCloud()

    def create_from_depth(self, depth_map: np.ndarray, color_image: np.ndarray,
                         camera_matrix: np.ndarray, max_depth: float = 5000.0) -> o3d.geometry.PointCloud:
        """
        Create point cloud from depth map and color image

        Args:
            depth_map: Depth map in mm
            color_image: Corresponding color image
            camera_matrix: 3x3 camera intrinsic matrix
            max_depth: Maximum depth threshold in mm

        Returns:
            Open3D point cloud
        """
        # Get image dimensions
        height, width = depth_map.shape

        # Create Open3D depth and color images
        depth_o3d = o3d.geometry.Image((depth_map).astype(np.float32))
        color_o3d = o3d.geometry.Image(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))

        # Create RGBD image
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color_o3d,
            depth_o3d,
            depth_scale=1.0,  # Depth is already in mm
            depth_trunc=max_depth,
            convert_rgb_to_intensity=False
        )

        # Create camera intrinsic
        fx = camera_matrix[0, 0]
        fy = camera_matrix[1, 1]
        cx = camera_matrix[0, 2]
        cy = camera_matrix[1, 2]

        intrinsic = o3d.camera.PinholeCameraIntrinsic(
            width, height, fx, fy, cx, cy
        )

        # Create point cloud
        pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, intrinsic)

        return pcd

    def create_from_disparity(self, disparity: np.ndarray, color_image: np.ndarray,
                             Q: np.ndarray) -> o3d.geometry.PointCloud:
        """
        Create point cloud from disparity map

        Args:
            disparity: Disparity map (16-bit fixed point)
            color_image: Corresponding color image
            Q: Disparity-to-depth mapping matrix

        Returns:
            Open3D point cloud
        """
        # Convert disparity to 3D points
        disparity_float = disparity.astype(np.float32) / 16.0
        points_3d = cv2.reprojectImageTo3D(disparity_float, Q)

        # Get valid points mask
        mask = disparity > 0

        # Extract points and colors
        points = points_3d[mask]
        colors = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)[mask] / 255.0

        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.colors = o3d.utility.Vector3dVector(colors)

        return pcd

    def filter_statistical_outliers(self, pcd: o3d.geometry.PointCloud,
                                    nb_neighbors: int = 20,
                                    std_ratio: float = 2.0) -> o3d.geometry.PointCloud:
        """
        Remove statistical outliers from point cloud

        Args:
            pcd: Input point cloud
            nb_neighbors: Number of neighbors to analyze
            std_ratio: Standard deviation ratio threshold

        Returns:
            Filtered point cloud
        """
        pcd_filtered, _ = pcd.remove_statistical_outlier(nb_neighbors, std_ratio)
        return pcd_filtered

    def filter_radius_outliers(self, pcd: o3d.geometry.PointCloud,
                              nb_points: int = 16,
                              radius: float = 0.05) -> o3d.geometry.PointCloud:
        """
        Remove radius outliers from point cloud

        Args:
            pcd: Input point cloud
            nb_points: Minimum number of points within radius
            radius: Search radius

        Returns:
            Filtered point cloud
        """
        pcd_filtered, _ = pcd.remove_radius_outlier(nb_points, radius)
        return pcd_filtered

    def downsample_voxel(self, pcd: o3d.geometry.PointCloud,
                        voxel_size: float = 0.01) -> o3d.geometry.PointCloud:
        """
        Downsample point cloud using voxel grid

        Args:
            pcd: Input point cloud
            voxel_size: Voxel size for downsampling

        Returns:
            Downsampled point cloud
        """
        pcd_downsampled = pcd.voxel_down_sample(voxel_size)
        return pcd_downsampled

    def estimate_normals(self, pcd: o3d.geometry.PointCloud,
                        search_param: Optional[o3d.geometry.KDTreeSearchParam] = None) -> None:
        """
        Estimate surface normals for point cloud

        Args:
            pcd: Point cloud (modified in-place)
            search_param: Search parameters for normal estimation
        """
        if search_param is None:
            search_param = o3d.geometry.KDTreeSearchParamHybridSearch(radius=0.1, max_nn=30)

        pcd.estimate_normals(search_param)
        pcd.orient_normals_consistent_tangent_plane(30)

    def merge_point_clouds(self, pcds: List[o3d.geometry.PointCloud]) -> o3d.geometry.PointCloud:
        """
        Merge multiple point clouds

        Args:
            pcds: List of point clouds to merge

        Returns:
            Merged point cloud
        """
        if not pcds:
            return o3d.geometry.PointCloud()

        merged = o3d.geometry.PointCloud()

        for pcd in pcds:
            merged += pcd

        return merged

    def transform_point_cloud(self, pcd: o3d.geometry.PointCloud,
                            R: np.ndarray, T: np.ndarray) -> o3d.geometry.PointCloud:
        """
        Transform point cloud using rotation and translation

        Args:
            pcd: Input point cloud
            R: 3x3 rotation matrix
            T: 3x1 translation vector

        Returns:
            Transformed point cloud
        """
        # Create 4x4 transformation matrix
        transformation = np.eye(4)
        transformation[:3, :3] = R
        transformation[:3, 3] = T.flatten()

        pcd_transformed = pcd.transform(transformation)
        return pcd_transformed

    def create_mesh_poisson(self, pcd: o3d.geometry.PointCloud,
                           depth: int = 9) -> Tuple[o3d.geometry.TriangleMesh, np.ndarray]:
        """
        Create mesh from point cloud using Poisson reconstruction

        Args:
            pcd: Input point cloud (must have normals)
            depth: Octree depth for reconstruction

        Returns:
            Tuple of (mesh, densities)
        """
        # Ensure normals are estimated
        if not pcd.has_normals():
            self.estimate_normals(pcd)

        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd, depth=depth
        )

        return mesh, densities

    def create_mesh_ball_pivoting(self, pcd: o3d.geometry.PointCloud,
                                  radii: Optional[List[float]] = None) -> o3d.geometry.TriangleMesh:
        """
        Create mesh from point cloud using ball pivoting algorithm

        Args:
            pcd: Input point cloud (must have normals)
            radii: List of radii for ball pivoting

        Returns:
            Triangle mesh
        """
        # Ensure normals are estimated
        if not pcd.has_normals():
            self.estimate_normals(pcd)

        if radii is None:
            # Estimate appropriate radii based on point cloud
            distances = pcd.compute_nearest_neighbor_distance()
            avg_dist = np.mean(distances)
            radii = [avg_dist, avg_dist * 2, avg_dist * 4]

        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
            pcd,
            o3d.utility.DoubleVector(radii)
        )

        return mesh

    def clean_mesh(self, mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
        """
        Clean mesh by removing degenerate triangles and duplicates

        Args:
            mesh: Input mesh

        Returns:
            Cleaned mesh
        """
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_non_manifold_edges()

        return mesh

    def compute_bounding_box(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.AxisAlignedBoundingBox:
        """Get axis-aligned bounding box of point cloud"""
        return pcd.get_axis_aligned_bounding_box()

    def crop_point_cloud(self, pcd: o3d.geometry.PointCloud,
                        bbox: o3d.geometry.AxisAlignedBoundingBox) -> o3d.geometry.PointCloud:
        """Crop point cloud to bounding box"""
        return pcd.crop(bbox)

    def get_point_count(self, pcd: o3d.geometry.PointCloud) -> int:
        """Get number of points in point cloud"""
        return len(pcd.points)

    def has_colors(self, pcd: o3d.geometry.PointCloud) -> bool:
        """Check if point cloud has colors"""
        return pcd.has_colors()

    def has_normals(self, pcd: o3d.geometry.PointCloud) -> bool:
        """Check if point cloud has normals"""
        return pcd.has_normals()


class PointCloudFusion:
    """Handles fusion of multiple point clouds over time"""

    def __init__(self, voxel_size: float = 0.01):
        """
        Initialize point cloud fusion

        Args:
            voxel_size: Voxel size for volumetric integration
        """
        self.voxel_size = voxel_size
        self.volume = o3d.pipelines.integration.ScalableTSDFVolume(
            voxel_length=voxel_size,
            sdf_trunc=0.04,
            color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8
        )
        self.frame_count = 0

    def integrate_frame(self, depth_image: np.ndarray, color_image: np.ndarray,
                       intrinsic: o3d.camera.PinholeCameraIntrinsic,
                       extrinsic: np.ndarray = np.eye(4)) -> None:
        """
        Integrate a new frame into the volume

        Args:
            depth_image: Depth image
            color_image: Color image
            intrinsic: Camera intrinsic parameters
            extrinsic: Camera extrinsic parameters (4x4 transformation matrix)
        """
        # Create RGBD image
        depth_o3d = o3d.geometry.Image(depth_image.astype(np.float32))
        color_o3d = o3d.geometry.Image(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))

        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color_o3d,
            depth_o3d,
            depth_scale=1.0,
            depth_trunc=5000.0,
            convert_rgb_to_intensity=False
        )

        # Integrate into volume
        self.volume.integrate(rgbd, intrinsic, extrinsic)
        self.frame_count += 1

    def extract_point_cloud(self) -> o3d.geometry.PointCloud:
        """
        Extract point cloud from integrated volume

        Returns:
            Fused point cloud
        """
        return self.volume.extract_point_cloud()

    def extract_mesh(self) -> o3d.geometry.TriangleMesh:
        """
        Extract triangle mesh from integrated volume

        Returns:
            Fused mesh
        """
        return self.volume.extract_triangle_mesh()

    def reset(self) -> None:
        """Reset the fusion volume"""
        self.volume = o3d.pipelines.integration.ScalableTSDFVolume(
            voxel_length=self.voxel_size,
            sdf_trunc=0.04,
            color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8
        )
        self.frame_count = 0
