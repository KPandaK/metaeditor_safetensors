"""
Main entry point for the MVC-based Safetensors Metadata Editor.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from controllers import MainController

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_application():
    """Create and configure the QApplication."""
    app = QApplication(sys.argv)
    app.setApplicationName("Safetensors Metadata Editor")
    app.setApplicationVersion("2.0 MVC")
    app.setOrganizationName("MetaEditor")
    app.setOrganizationDomain("github.com/KPandaK/metaeditor_safetensors")
    
    # Set application style for consistent look across platforms
    app.setStyle('Fusion')
    
    return app


def main():
    """Main entry point for the MVC application."""
    try:
        # Create QApplication first (required for Qt widgets)
        app = create_application()
        
        # Create and configure the main controller
        controller = MainController(app)
        
        # Run the application
        return controller.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
