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
    try:
        return version("metaeditor-safetensors")
    except PackageNotFoundError:
        return "dev"


def main():
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

    # Initialize theme service with config service for monitoring
    theme_service = ThemeService(config_service)
    theme_service.add_theme_changed_observer(
        lambda theme: app.setStyleSheet(theme.get_qss())
    )

    # 3. Instantiate the MVC components.
    model = MetadataModel()
    view = MainView(config_service)
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
        theme_service.shutdown()

    sys.exit(exit_code)
