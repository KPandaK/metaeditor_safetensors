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
from .services.status_message_service import StatusMessageService
from .services.theme_coordinator import ThemeCoordinator
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
    status_message_service = StatusMessageService()

    # Instantiate the MVC components.
    model = Metadata()

    # Initialize modelspec service with metadata dependency
    modelspec_service = ModelSpecService(model)

    # Initialize theme service
    theme_service = ThemeService()
    theme_coordinator = ThemeCoordinator(
        theme_service,
        config_service,
        status_message_service,
    )
    theme_coordinator.connect_app(app)
    theme_coordinator.apply_startup_theme()

    view = MainView(config_service, status_message_service)
    controller = MainController(
        model,
        view,
        config_service,
        safetensors_service,
        theme_coordinator,
        modelspec_service,
        status_message_service,
    )

    # Run the application.
    controller.run()

    # Start the Qt event loop.
    try:
        exit_code = app.exec()
    finally:
        # Ensure proper cleanup before exit
        controller.shutdown()
        theme_coordinator.shutdown()
        theme_service.shutdown()

    sys.exit(exit_code)
