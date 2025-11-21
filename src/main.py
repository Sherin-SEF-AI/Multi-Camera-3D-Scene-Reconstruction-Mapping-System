"""
Main Entry Point
Multi-Camera 3D Scene Reconstruction & Mapping System
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import MainWindow
from utils.config import init_config
from utils.logger import init_logger


def main():
    """Main application entry point"""

    # Initialize configuration
    config = init_config()

    # Initialize logger
    logger = init_logger(
        level=config.get('logging.level', 'INFO'),
        log_to_file=config.get('logging.save_to_file', True),
        log_path=config.get('logging.log_path', 'logs')
    )

    logger.info("="*60)
    logger.info(f"Starting {config.get('application.name')} v{config.get('application.version')}")
    logger.info("="*60)

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(config.get('application.name'))
    app.setApplicationVersion(config.get('application.version'))

    # Enable high DPI scaling
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # Create and show main window
    main_window = MainWindow()
    main_window.show()

    logger.info("Application window displayed")

    # Run application
    exit_code = app.exec()

    logger.info("Application exiting")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
