import logging
from importlib.metadata import PackageNotFoundError, version

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QDialog

from metaeditor_safetensors.models.theme import ThemeType
from metaeditor_safetensors.widgets.clickable_image import ThemeMode

from ..layouts.about_ui_layout import Ui_AboutDialog
from ..services.theme_service import ThemeService

logger = logging.getLogger(__name__)


def get_app_version():
    try:
        return version("metaeditor_safetensors")
    except PackageNotFoundError:
        return "dev"


class AboutDialog(QDialog):
    def __init__(self, theme_service: ThemeService, parent=None):
        super().__init__(parent)

        self._theme_service = theme_service

        self.ui = Ui_AboutDialog()
        self.ui.setup_ui(self)

        # Ensure the dialog uses the current application stylesheet
        app = QApplication.instance()
        if isinstance(app, QApplication):
            self.setStyleSheet(app.styleSheet())

        self.setWindowTitle("About")
        self.setFixedSize(690, 425)

        # Set version from package metadata
        app_version = get_app_version()
        self.ui.about_version.setText(f"v{app_version}")

        self._setup_clickable_images()

        self.ui.copy_version_btn.clicked.connect(self._copy_version_to_clipboard)

    def _setup_clickable_images(self):
        # Override mouse events to handle clicks
        self.ui.github_link.mousePressEvent = lambda event: self._open_github_link(
            event
        )
        self.ui.kofi_link.mousePressEvent = lambda event: self._open_kofi_link(event)

        # Connect to theme changes
        if self._theme_service:
            self._theme_service.add_theme_changed_observer(self._update_link_buttons)

        # Initial setup based on current theme
        self._update_link_buttons(self._theme_service.get_current_theme())

    def _update_link_buttons(self, theme):
        if theme:
            # Switch image based on theme category
            if theme.config.category == ThemeType.DARK:
                self.ui.github_link.setMode(ThemeMode.DARK)
            else:
                self.ui.github_link.setMode(ThemeMode.LIGHT)
        else:
            # Default to light mode if we can't determine theme
            self.ui.github_link.setMode(ThemeMode.LIGHT)

    def _open_github_link(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            QDesktopServices.openUrl(
                QUrl("https://github.com/KPandaK/metaeditor_safetensors")
            )

    def _open_kofi_link(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            QDesktopServices.openUrl(QUrl("https://ko-fi.com/kpandak"))

    def _copy_version_to_clipboard(self):
        clipboard = QApplication.clipboard()
        app_version = get_app_version()
        version_text = f"v{app_version}"
        clipboard.setText(version_text)
