"""
File Management Utilities
Handles file operations for exports, calibrations, and recordings
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional, List
from datetime import datetime
import open3d as o3d


class FileManager:
    """Manages file operations for the application"""

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize file manager

        Args:
            base_path: Base directory for all file operations
        """
        if base_path is None:
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)

        # Create standard directories
        self.exports_dir = self.base_path / "exports"
        self.calibrations_dir = self.base_path / "calibrations"
        self.recordings_dir = self.base_path / "recordings"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.calibrations_dir.mkdir(parents=True, exist_ok=True)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

    def generate_filename(self, prefix: str = "", extension: str = "",
                         timestamp: bool = True) -> str:
        """
        Generate filename with optional timestamp

        Args:
            prefix: Filename prefix
            extension: File extension (with or without dot)
            timestamp: Whether to include timestamp

        Returns:
            Generated filename
        """
        if not extension.startswith('.') and extension:
            extension = f".{extension}"

        if timestamp:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{ts}{extension}" if prefix else f"{ts}{extension}"
        else:
            filename = f"{prefix}{extension}"

        return filename

    def save_point_cloud(self, point_cloud: o3d.geometry.PointCloud,
                        filename: Optional[str] = None,
                        format: str = "ply") -> Optional[str]:
        """
        Save point cloud to file

        Args:
            point_cloud: Open3D point cloud object
            filename: Output filename. If None, auto-generated.
            format: File format (ply, pcd, xyz)

        Returns:
            Path to saved file or None if failed
        """
        try:
            if filename is None:
                filename = self.generate_filename("pointcloud", format)

            filepath = self.exports_dir / filename

            # Ensure correct extension
            if not filepath.suffix:
                filepath = filepath.with_suffix(f".{format}")

            o3d.io.write_point_cloud(str(filepath), point_cloud)
            return str(filepath)

        except Exception as e:
            print(f"Error saving point cloud: {e}")
            return None

    def load_point_cloud(self, filepath: str) -> Optional[o3d.geometry.PointCloud]:
        """
        Load point cloud from file

        Args:
            filepath: Path to point cloud file

        Returns:
            Open3D point cloud object or None if failed
        """
        try:
            return o3d.io.read_point_cloud(filepath)
        except Exception as e:
            print(f"Error loading point cloud: {e}")
            return None

    def save_mesh(self, mesh: o3d.geometry.TriangleMesh,
                 filename: Optional[str] = None,
                 format: str = "obj") -> Optional[str]:
        """
        Save mesh to file

        Args:
            mesh: Open3D triangle mesh object
            filename: Output filename. If None, auto-generated.
            format: File format (obj, stl, ply)

        Returns:
            Path to saved file or None if failed
        """
        try:
            if filename is None:
                filename = self.generate_filename("mesh", format)

            filepath = self.exports_dir / filename

            if not filepath.suffix:
                filepath = filepath.with_suffix(f".{format}")

            o3d.io.write_triangle_mesh(str(filepath), mesh)
            return str(filepath)

        except Exception as e:
            print(f"Error saving mesh: {e}")
            return None

    def save_calibration(self, calibration_data: Dict[str, Any],
                        camera_id: Optional[str] = None) -> Optional[str]:
        """
        Save camera calibration data

        Args:
            calibration_data: Dictionary containing calibration parameters
            camera_id: Camera identifier

        Returns:
            Path to saved file or None if failed
        """
        try:
            prefix = f"calibration_cam{camera_id}" if camera_id else "calibration"
            filename = self.generate_filename(prefix, "json")
            filepath = self.calibrations_dir / filename

            # Convert numpy arrays to lists for JSON serialization
            serializable_data = self._make_json_serializable(calibration_data)

            with open(filepath, 'w') as f:
                json.dump(serializable_data, f, indent=2)

            return str(filepath)

        except Exception as e:
            print(f"Error saving calibration: {e}")
            return None

    def load_calibration(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Load camera calibration data

        Args:
            filepath: Path to calibration file

        Returns:
            Dictionary containing calibration parameters or None if failed
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Convert lists back to numpy arrays
            return self._restore_numpy_arrays(data)

        except Exception as e:
            print(f"Error loading calibration: {e}")
            return None

    def save_numpy(self, array: np.ndarray, filename: Optional[str] = None) -> Optional[str]:
        """
        Save numpy array to file

        Args:
            array: Numpy array to save
            filename: Output filename

        Returns:
            Path to saved file or None if failed
        """
        try:
            if filename is None:
                filename = self.generate_filename("array", "npy")

            filepath = self.exports_dir / filename
            np.save(filepath, array)
            return str(filepath)

        except Exception as e:
            print(f"Error saving numpy array: {e}")
            return None

    def _make_json_serializable(self, data: Any) -> Any:
        """Convert numpy arrays and other non-serializable types to JSON-compatible format"""
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, dict):
            return {key: self._make_json_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_json_serializable(item) for item in data]
        elif isinstance(data, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
            return int(data)
        elif isinstance(data, (np.float_, np.float16, np.float32, np.float64)):
            return float(data)
        else:
            return data

    def _restore_numpy_arrays(self, data: Any) -> Any:
        """Restore numpy arrays from JSON-compatible format"""
        if isinstance(data, dict):
            # Check if this looks like a matrix (camera_matrix, dist_coeffs, etc.)
            if all(isinstance(v, list) for v in data.values()):
                return {key: np.array(value) for key, value in data.items()}
            else:
                return {key: self._restore_numpy_arrays(value) for key, value in data.items()}
        elif isinstance(data, list):
            # Check if this is a numeric list that should be an array
            if all(isinstance(item, (int, float, list)) for item in data):
                return np.array(data)
            return [self._restore_numpy_arrays(item) for item in data]
        else:
            return data

    def list_calibrations(self) -> List[str]:
        """
        List all saved calibration files

        Returns:
            List of calibration file paths
        """
        return [str(f) for f in self.calibrations_dir.glob("*.json")]

    def list_exports(self, pattern: str = "*") -> List[str]:
        """
        List all exported files

        Args:
            pattern: Glob pattern for filtering files

        Returns:
            List of export file paths
        """
        return [str(f) for f in self.exports_dir.glob(pattern)]

    def get_export_path(self, filename: str) -> Path:
        """Get full path for export file"""
        return self.exports_dir / filename

    def get_calibration_path(self, filename: str) -> Path:
        """Get full path for calibration file"""
        return self.calibrations_dir / filename

    def get_recording_path(self, filename: str) -> Path:
        """Get full path for recording file"""
        return self.recordings_dir / filename

    def cleanup_old_files(self, directory: str, days: int = 30) -> int:
        """
        Remove files older than specified days

        Args:
            directory: Directory to clean (exports, calibrations, recordings)
            days: Remove files older than this many days

        Returns:
            Number of files removed
        """
        dir_map = {
            "exports": self.exports_dir,
            "calibrations": self.calibrations_dir,
            "recordings": self.recordings_dir
        }

        target_dir = dir_map.get(directory)
        if not target_dir:
            return 0

        removed_count = 0
        cutoff_time = datetime.now().timestamp() - (days * 86400)

        for file in target_dir.iterdir():
            if file.is_file() and file.stat().st_mtime < cutoff_time:
                try:
                    file.unlink()
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing file {file}: {e}")

        return removed_count


# Global file manager instance
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """Get global file manager instance"""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager
