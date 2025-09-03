"""
Application Entry Point
=======================

This is the main script to run the Safetensors Metadata Editor application.

It sets up the necessary components of the Model-View-Controller (MVC)
architecture and starts the Qt application event loop.
"""

import sys
import os
from PySide6.QtCore import QFileSystemWatcher, Qt
from PySide6.QtWidgets import QApplication

# Handle both direct execution and module execution
if __name__ == "__main__" and __package__ is None:
    # Direct execution - add parent directory to path for imports
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from metaeditor_safetensors.models.metadata_model import MetadataModel
    from metaeditor_safetensors.views.main_view import MainView
    from metaeditor_safetensors.controllers.main_controller import MainController
    from metaeditor_safetensors._version import __version__
else:
    # Module execution - use relative imports
    from .models.metadata_model import MetadataModel
    from .views.main_view import MainView
    from .controllers.main_controller import MainController
    from ._version import __version__

def main():
    """
    The main function that sets up and runs the application.
    """
    # 1. Create the QApplication instance. This is a requirement for any Qt app.
    app = QApplication(sys.argv)
    
    # Set application properties for consistent font rendering
    app.setApplicationDisplayName("Safetensors Metadata Editor")
    app.setApplicationVersion(__version__)

    # --- Live-reloading for stylesheet ---
    style_file = os.path.join(os.path.dirname(__file__), 'ui', 'style.qss')

    def apply_stylesheet():
        """Reads the stylesheet and applies it to the application."""
        # The file is read with 'utf-8' encoding to ensure compatibility
        with open(style_file, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())

    # Apply the initial stylesheet and watch for changes
    apply_stylesheet()
    watcher = QFileSystemWatcher([style_file])
    watcher.fileChanged.connect(apply_stylesheet)
    # --- End of live-reloading code ---

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

if __name__ == "__main__":
    main()
