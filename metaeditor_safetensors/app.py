"""
Application Entry Point
=======================

This module contains the main application logic for the Safetensors Metadata Editor.
"""

import logging
import os
import sys
from importlib.metadata import PackageNotFoundError, version

from PySide6.QtWidgets import QApplication

from .controllers.main_controller import MainController
from .models.metadata_model import MetadataModel
from .services.config_service import ConfigService
from .services.image_service import ImageService
from .services.safetensors_service import SafetensorsService
from .services.theme_service import ThemeService
from .views.main_view import MainView


def get_app_version():
    """Get the application version from package metadata."""
    try:
        return version("metaeditor-safetensors")
    except PackageNotFoundError:
        return "dev"


def main():
    """
    The main function that sets up and runs the application.
    """
    # Set logging level from environment variable
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    # 1. Create the QApplication instance. This is a requirement for any Qt app.
    app = QApplication(sys.argv)

    app.setApplicationDisplayName("Safetensors Metadata Editor")
    app.setApplicationVersion(get_app_version())

    # 2. Instantiate services.
    config_service = ConfigService()
    safetensors_service = SafetensorsService()
    image_service = ImageService()

    # Initialize theme service
    theme_service = ThemeService(app)

    # Apply user's theme preference (app coordinates between config and theme services)
    preferred_theme = config_service.get_theme_preference()
    if preferred_theme and theme_service.has_theme(preferred_theme):
        theme_service.apply_theme(preferred_theme)
    else:
        # Default to auto theme
        theme_service.apply_theme("auto")
        config_service.set_theme_preference("auto")

    # 3. Instantiate the MVC components.
    model = MetadataModel()
    view = MainView()
    controller = MainController(
        model, view, config_service, safetensors_service, image_service, theme_service
    )

    # 4. Run the application.
    controller.run()

    # 5. Start the Qt event loop.
    try:
        exit_code = app.exec()
    finally:
        # Ensure proper cleanup before exit
        controller.shutdown()

    sys.exit(exit_code)
