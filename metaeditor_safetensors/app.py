"""
Application Entry Point
=======================

This module contains the main application logic for the Safetensors Metadata Editor.
"""

import sys
import os
from PySide6.QtWidgets import QApplication

def main():
    """
    The main function that sets up and runs the application.
    """
    # Force light mode on Windows by setting environment variable before QApplication
    if sys.platform == "win32":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"
    
    # Import here to avoid circular imports
    from .models.metadata_model import MetadataModel
    from .views.main_view import MainView
    from .controllers.main_controller import MainController
    from ._version import __version__
    
    # 1. Create the QApplication instance. This is a requirement for any Qt app.
    app = QApplication(sys.argv)
    
    # TODO: Add support for themes in the future
    # Force Qt to use its own style instead of system theme
    app.setStyle('Fusion')
    
    # Set application properties for consistent font rendering
    app.setApplicationDisplayName("Metadata Editor")
    app.setApplicationVersion(__version__)

    # Apply stylesheet from Qt resources
    from PySide6.QtCore import QFile, QIODevice
    
    def apply_stylesheet():
        """Loads the stylesheet from Qt resources and applies it to the application."""
        style_file = QFile(":/assets/style.qss")
        if style_file.open(QIODevice.ReadOnly | QIODevice.Text):
            stylesheet = style_file.readAll().data().decode('utf-8')
            app.setStyleSheet(stylesheet)
            style_file.close()
        else:
            print(f"Warning: Could not load stylesheet from resources")

    # Apply the stylesheet from resources
    apply_stylesheet()

    # 2. Instantiate the MVC components.
    model = MetadataModel()
    view = MainView()
    controller = MainController(model, view)

    # 3. Run the application.
    controller.run()

    # 4. Start the Qt event loop.
    try:
        exit_code = app.exec()
    finally:
        # Ensure proper cleanup before exit
        controller.shutdown()
    
    sys.exit(exit_code)
