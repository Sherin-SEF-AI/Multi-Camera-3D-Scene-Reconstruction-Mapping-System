"""
Configuration Management System
Handles loading, saving, and managing application configuration
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import copy


class ConfigManager:
    """Manages application configuration with JSON backend"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.project_root = Path(__file__).parent.parent.parent

        if config_path is None:
            self.config_path = self.project_root / "config" / "default_config.json"
        else:
            self.config_path = Path(config_path)

        self.config: Dict[str, Any] = {}
        self.default_config: Dict[str, Any] = {}

        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self.default_config = copy.deepcopy(self.config)
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self._get_fallback_config()
            self.default_config = copy.deepcopy(self.config)

    def _get_fallback_config(self) -> Dict[str, Any]:
        """Return a minimal fallback configuration"""
        return {
            "application": {
                "name": "Multi-Camera 3D Reconstruction System",
                "version": "1.0.0",
                "theme": "dark"
            },
            "cameras": {
                "num_cameras": 3,
                "default_resolution": [640, 480],
                "default_fps": 30
            },
            "logging": {
                "level": "INFO",
                "save_to_file": True,
                "log_path": "logs"
            }
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key_path: Path to config value (e.g., "cameras.default_resolution")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation

        Args:
            key_path: Path to config value (e.g., "cameras.default_fps")
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

    def save(self, path: Optional[str] = None) -> bool:
        """
        Save current configuration to file

        Args:
            path: Path to save config. If None, uses current config_path.

        Returns:
            True if successful, False otherwise
        """
        save_path = Path(path) if path else self.config_path

        try:
            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def reset_to_default(self) -> None:
        """Reset configuration to default values"""
        self.config = copy.deepcopy(self.default_config)

    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with dictionary

        Args:
            updates: Dictionary of updates to apply
        """
        self._deep_update(self.config, updates)

    def _deep_update(self, base: Dict, updates: Dict) -> None:
        """Recursively update nested dictionaries"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section

        Args:
            section: Section name (e.g., "cameras", "stereo")

        Returns:
            Dictionary of section configuration
        """
        return self.config.get(section, {})

    def export_config(self, path: str) -> bool:
        """
        Export current configuration to a new file

        Args:
            path: Path to export configuration

        Returns:
            True if successful, False otherwise
        """
        return self.save(path)

    def import_config(self, path: str) -> bool:
        """
        Import configuration from file

        Args:
            path: Path to configuration file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, 'r') as f:
                imported = json.load(f)
            self.update(imported)
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False

    def validate_config(self) -> bool:
        """
        Validate configuration structure

        Returns:
            True if valid, False otherwise
        """
        required_sections = [
            "application", "cameras", "calibration",
            "stereo", "point_cloud", "logging"
        ]

        for section in required_sections:
            if section not in self.config:
                print(f"Missing required section: {section}")
                return False

        return True

    def __repr__(self) -> str:
        return f"ConfigManager(config_path='{self.config_path}')"


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def init_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Initialize global configuration manager

    Args:
        config_path: Path to configuration file

    Returns:
        ConfigManager instance
    """
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager
