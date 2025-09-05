"""
Application Entry Point
=======================

This module contains the main application logic for the Safetensors Metadata Editor.
"""

import os
import sys

from PySide6.QtWidgets import QApplication

from ._version import __version__
from .controllers.main_controller import MainController
from .models.metadata_model import MetadataModel
from .services.config_service import ConfigService
from .services.image_service import ImageService
from .services.safetensors_service import SafetensorsService
from .services.stylesheet_service import StylesheetService
from .views.main_view import MainView


def main():
    """
    The main function that sets up and runs the application.
    """
    # TODO: Add support for themes in the future
    # Force light mode on Windows by setting environment variable before QApplication
    if sys.platform == "win32":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"

    # 1. Create the QApplication instance. This is a requirement for any Qt app.
    app = QApplication(sys.argv)

    # TODO: Add support for themes in the future
    # Force Qt to use its own style instead of system theme
    app.setStyle("Fusion")

    app.setApplicationDisplayName("Safetensors Metadata Editor")
    app.setApplicationVersion(__version__)

    resource_path = ":/assets/style.qss"
    filesystem_path = os.path.join(
        os.path.dirname(__file__), "..", "assets", "style.qss"
    )
    stylesheet_service = StylesheetService(app, resource_path, filesystem_path)
    stylesheet_service.apply_stylesheet()

    # 2. Instantiate services.
    config_service = ConfigService()
    safetensors_service = SafetensorsService()
    image_service = ImageService()

    # 3. Instantiate the MVC components.
    model = MetadataModel()
    view = MainView()
    controller = MainController(
        model, view, config_service, safetensors_service, image_service
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
