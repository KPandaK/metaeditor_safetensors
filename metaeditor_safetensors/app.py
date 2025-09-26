import logging
import os
import sys
from importlib.metadata import PackageNotFoundError, version

from PySide6.QtWidgets import QApplication

from .controllers.main_controller import MainController
from .models.metadata import Metadata
from .services.config_service import ConfigService
from .services.modelspec_service import ModelSpecService
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

    # Create the QApplication instance. This is a requirement for any Qt app.
    app = QApplication(sys.argv)

    app.setApplicationDisplayName("Safetensors Metadata Editor")
    app.setApplicationVersion(get_app_version())

    # Instantiate services.
    config_service = ConfigService()
    safetensors_service = SafetensorsService()

    # Instantiate the MVC components.
    model = Metadata()

    # Initialize modelspec service with metadata dependency
    modelspec_service = ModelSpecService(model)

    # Initialize theme service
    theme_service = ThemeService()
    theme_service.add_theme_changed_observer(
        lambda theme: app.setStyleSheet(theme.get_qss())
    )

    view = MainView(config_service)
    controller = MainController(
        model,
        view,
        config_service,
        safetensors_service,
        theme_service,
        modelspec_service,
    )

    # Run the application.
    controller.run()

    # Start the Qt event loop.
    try:
        exit_code = app.exec()
    finally:
        # Ensure proper cleanup before exit
        controller.shutdown()
        theme_service.shutdown()

    sys.exit(exit_code)
