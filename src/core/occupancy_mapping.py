"""
Occupancy Mapping Module
Handles 2D and 3D occupancy grid generation from point clouds
"""

import numpy as np
import cv2
import open3d as o3d
from typing import Tuple, Optional
from scipy.ndimage import gaussian_filter


class OccupancyGrid2D:
    """2D occupancy grid for top-down mapping"""

    def __init__(self, resolution: float = 0.05, size: Tuple[float, float] = (10.0, 10.0)):
        """
        Initialize 2D occupancy grid

        Args:
            resolution: Grid cell size in meters
            size: Grid size in meters (width, height)
        """
        self.resolution = resolution
        self.size = size

        # Calculate grid dimensions
        self.width_cells = int(size[0] / resolution)
        self.height_cells = int(size[1] / resolution)

        # Initialize grid (0.5 = unknown, 0 = free, 1 = occupied)
        self.grid = np.ones((self.height_cells, self.width_cells), dtype=np.float32) * 0.5

        # Center of the grid in world coordinates
        self.origin = np.array([-size[0] / 2, -size[1] / 2, 0])

        # Parameters for probabilistic updates
        self.occupied_threshold = 0.7
        self.free_threshold = 0.3
        self.prob_occupied = 0.7
        self.prob_free = 0.3

    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """
        Convert world coordinates to grid indices

        Args:
            x: X coordinate in world frame (meters)
            y: Y coordinate in world frame (meters)

        Returns:
            Tuple of (row, col) grid indices
        """
        grid_x = int((x - self.origin[0]) / self.resolution)
        grid_y = int((y - self.origin[1]) / self.resolution)

        return grid_y, grid_x

    def grid_to_world(self, row: int, col: int) -> Tuple[float, float]:
        """
        Convert grid indices to world coordinates

        Args:
            row: Grid row index
            col: Grid column index

        Returns:
            Tuple of (x, y) world coordinates
        """
        x = col * self.resolution + self.origin[0]
        y = row * self.resolution + self.origin[1]

        return x, y

    def update_from_point_cloud(self, pcd: o3d.geometry.PointCloud,
                                sensor_position: np.ndarray = np.array([0, 0, 1])) -> None:
        """
        Update occupancy grid from point cloud

        Args:
            pcd: Open3D point cloud
            sensor_position: Sensor position in world frame (x, y, z)
        """
        points = np.asarray(pcd.points)

        if len(points) == 0:
            return

        # Project points to 2D (top-down view)
        points_2d = points[:, :2]  # Take X and Y coordinates

        # Mark occupied cells
        for point in points_2d:
            row, col = self.world_to_grid(point[0], point[1])

            if 0 <= row < self.height_cells and 0 <= col < self.width_cells:
                # Update probability using log-odds
                self.grid[row, col] = min(1.0, self.grid[row, col] + 0.1)

        # Ray tracing for free space (simplified)
        sensor_2d = sensor_position[:2]

        for point in points_2d:
            # Trace ray from sensor to point
            self._trace_ray(sensor_2d, point)

    def _trace_ray(self, start: np.ndarray, end: np.ndarray) -> None:
        """
        Trace ray and mark cells as free

        Args:
            start: Start point (x, y)
            end: End point (x, y)
        """
        # Bresenham's line algorithm for ray tracing
        start_grid = self.world_to_grid(start[0], start[1])
        end_grid = self.world_to_grid(end[0], end[1])

        line_points = self._bresenham_line(start_grid, end_grid)

        # Mark all points except the last one as free
        for i, (row, col) in enumerate(line_points[:-1]):
            if 0 <= row < self.height_cells and 0 <= col < self.width_cells:
                # Decrease occupancy probability
                self.grid[row, col] = max(0.0, self.grid[row, col] - 0.05)

    def _bresenham_line(self, start: Tuple[int, int], end: Tuple[int, int]) -> list:
        """
        Bresenham's line algorithm for integer line drawing

        Args:
            start: Start grid cell (row, col)
            end: End grid cell (row, col)

        Returns:
            List of (row, col) tuples along the line
        """
        points = []
        y0, x0 = start
        y1, x1 = end

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        x, y = x0, y0

        while True:
            points.append((y, x))

            if x == x1 and y == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        return points

    def get_visualization(self, colormap: int = cv2.COLORMAP_JET) -> np.ndarray:
        """
        Get color-coded visualization of occupancy grid

        Args:
            colormap: OpenCV colormap

        Returns:
            Color visualization (BGR image)
        """
        # Convert to 0-255 range
        grid_visual = (self.grid * 255).astype(np.uint8)

        # Apply colormap
        grid_color = cv2.applyColorMap(grid_visual, colormap)

        # Flip vertically for correct orientation
        grid_color = cv2.flip(grid_color, 0)

        return grid_color

    def get_binary_map(self) -> np.ndarray:
        """
        Get binary occupancy map (occupied vs free)

        Returns:
            Binary map (0 = free/unknown, 255 = occupied)
        """
        binary_map = np.zeros_like(self.grid, dtype=np.uint8)
        binary_map[self.grid > self.occupied_threshold] = 255

        return cv2.flip(binary_map, 0)

    def clear(self) -> None:
        """Reset grid to unknown state"""
        self.grid = np.ones((self.height_cells, self.width_cells), dtype=np.float32) * 0.5


class OccupancyGrid3D:
    """3D voxel occupancy grid"""

    def __init__(self, resolution: float = 0.05,
                 size: Tuple[float, float, float] = (10.0, 10.0, 3.0)):
        """
        Initialize 3D occupancy grid

        Args:
            resolution: Voxel size in meters
            size: Grid size in meters (width, depth, height)
        """
        self.resolution = resolution
        self.size = size

        # Calculate grid dimensions
        self.width_cells = int(size[0] / resolution)
        self.depth_cells = int(size[1] / resolution)
        self.height_cells = int(size[2] / resolution)

        # Initialize grid (0.5 = unknown, 0 = free, 1 = occupied)
        self.grid = np.ones(
            (self.width_cells, self.depth_cells, self.height_cells),
            dtype=np.float32
        ) * 0.5

        # Center of the grid in world coordinates
        self.origin = np.array([-size[0] / 2, -size[1] / 2, 0])

    def world_to_grid(self, point: np.ndarray) -> Tuple[int, int, int]:
        """
        Convert world coordinates to grid indices

        Args:
            point: 3D point in world frame (x, y, z)

        Returns:
            Tuple of (i, j, k) grid indices
        """
        grid_x = int((point[0] - self.origin[0]) / self.resolution)
        grid_y = int((point[1] - self.origin[1]) / self.resolution)
        grid_z = int((point[2] - self.origin[2]) / self.resolution)

        return grid_x, grid_y, grid_z

    def grid_to_world(self, i: int, j: int, k: int) -> np.ndarray:
        """
        Convert grid indices to world coordinates

        Args:
            i, j, k: Grid indices

        Returns:
            3D point in world frame
        """
        x = i * self.resolution + self.origin[0]
        y = j * self.resolution + self.origin[1]
        z = k * self.resolution + self.origin[2]

        return np.array([x, y, z])

    def update_from_point_cloud(self, pcd: o3d.geometry.PointCloud) -> None:
        """
        Update 3D occupancy grid from point cloud

        Args:
            pcd: Open3D point cloud
        """
        points = np.asarray(pcd.points)

        if len(points) == 0:
            return

        # Mark occupied voxels
        for point in points:
            i, j, k = self.world_to_grid(point)

            if (0 <= i < self.width_cells and
                0 <= j < self.depth_cells and
                0 <= k < self.height_cells):
                # Update occupancy probability
                self.grid[i, j, k] = min(1.0, self.grid[i, j, k] + 0.1)

    def get_occupied_voxels(self, threshold: float = 0.7) -> np.ndarray:
        """
        Get coordinates of occupied voxels

        Args:
            threshold: Occupancy threshold

        Returns:
            Nx3 array of voxel centers
        """
        occupied_indices = np.argwhere(self.grid > threshold)

        if len(occupied_indices) == 0:
            return np.array([])

        # Convert to world coordinates
        occupied_voxels = []
        for idx in occupied_indices:
            voxel_center = self.grid_to_world(idx[0], idx[1], idx[2])
            occupied_voxels.append(voxel_center)

        return np.array(occupied_voxels)

    def to_point_cloud(self, threshold: float = 0.7) -> o3d.geometry.PointCloud:
        """
        Convert occupied voxels to point cloud

        Args:
            threshold: Occupancy threshold

        Returns:
            Open3D point cloud of occupied voxels
        """
        occupied_voxels = self.get_occupied_voxels(threshold)

        pcd = o3d.geometry.PointCloud()
        if len(occupied_voxels) > 0:
            pcd.points = o3d.utility.Vector3dVector(occupied_voxels)

            # Color by height (Z coordinate)
            z_values = occupied_voxels[:, 2]
            z_normalized = (z_values - z_values.min()) / (z_values.max() - z_values.min() + 1e-6)

            # Create color map (blue to red)
            colors = np.zeros((len(occupied_voxels), 3))
            colors[:, 0] = z_normalized  # Red channel
            colors[:, 2] = 1 - z_normalized  # Blue channel

            pcd.colors = o3d.utility.Vector3dVector(colors)

        return pcd

    def get_slice(self, z_height: float) -> np.ndarray:
        """
        Get 2D slice of 3D grid at specified height

        Args:
            z_height: Height in world coordinates

        Returns:
            2D occupancy grid at specified height
        """
        k = int((z_height - self.origin[2]) / self.resolution)

        if 0 <= k < self.height_cells:
            return self.grid[:, :, k]
        else:
            return np.zeros((self.width_cells, self.depth_cells))

    def clear(self) -> None:
        """Reset grid to unknown state"""
        self.grid = np.ones(
            (self.width_cells, self.depth_cells, self.height_cells),
            dtype=np.float32
        ) * 0.5
