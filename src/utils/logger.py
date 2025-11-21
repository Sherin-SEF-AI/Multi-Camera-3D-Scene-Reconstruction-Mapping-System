"""
Logging System
Provides centralized logging functionality for the application
"""

import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime


class Logger:
    """Application logger with file and console output"""

    def __init__(self, name: str = "3DReconstruction", level: str = "INFO",
                 log_to_file: bool = True, log_path: Optional[str] = None):
        """
        Initialize logger

        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to save logs to file
            log_path: Directory to save log files
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Console handler with color support
        self._setup_console_handler()

        # File handler
        if log_to_file:
            self._setup_file_handler(log_path)

    def _setup_console_handler(self) -> None:
        """Setup console logging handler with formatting"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Colored formatter
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)

        self.logger.addHandler(console_handler)

    def _setup_file_handler(self, log_path: Optional[str] = None) -> None:
        """
        Setup file logging handler with rotation

        Args:
            log_path: Directory to save log files
        """
        if log_path is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"
        else:
            log_dir = Path(log_path)

        log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"{self.name}_{timestamp}.log"

        # Rotating file handler (10MB max, 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # Detailed file formatter
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)

        self.logger.addHandler(file_handler)

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception with traceback"""
        self.logger.exception(message, *args, **kwargs)

    def set_level(self, level: str) -> None:
        """
        Change logging level

        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger.setLevel(getattr(logging, level.upper()))

    def add_file_handler(self, log_file: str, level: str = "INFO") -> None:
        """
        Add additional file handler

        Args:
            log_file: Path to log file
            level: Logging level for this handler
        """
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))

        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)

        self.logger.addHandler(file_handler)

    def __repr__(self) -> str:
        return f"Logger(name='{self.name}', level={self.logger.level})"


# Global logger instance
_global_logger: Optional[Logger] = None


def get_logger(name: Optional[str] = None, level: str = "INFO",
               log_to_file: bool = True) -> Logger:
    """
    Get or create logger instance

    Args:
        name: Logger name. If None, returns global logger.
        level: Logging level
        log_to_file: Whether to save logs to file

    Returns:
        Logger instance
    """
    global _global_logger

    if name is None:
        if _global_logger is None:
            _global_logger = Logger("3DReconstruction", level, log_to_file)
        return _global_logger
    else:
        return Logger(name, level, log_to_file)


def init_logger(name: str = "3DReconstruction", level: str = "INFO",
                log_to_file: bool = True, log_path: Optional[str] = None) -> Logger:
    """
    Initialize global logger

    Args:
        name: Logger name
        level: Logging level
        log_to_file: Whether to save logs to file
        log_path: Directory to save log files

    Returns:
        Logger instance
    """
    global _global_logger
    _global_logger = Logger(name, level, log_to_file, log_path)
    return _global_logger
