import logging
from importlib.metadata import PackageNotFoundError, version

from PySide6.QtCore import QFile, QIODevice, Qt, QTimer, QUrl
from PySide6.QtGui import QClipboard, QDesktopServices
from PySide6.QtWidgets import QApplication, QDialog

from metaeditor_safetensors.widgets.clickable_image import ThemeMode

from ..services.css_service import refresh_style_recursive
from ..services.theme_service import ThemeService
from ..widgets.svg_widget import SvgWidget
from .about_dialog_ui import Ui_AboutDialog

logger = logging.getLogger(__name__)


def get_app_version():
    """Get the application version from package metadata."""
    try:
        return version("metaeditor_safetensors")
    except PackageNotFoundError:
        return "dev"


class AboutDialog(QDialog):
    def __init__(self, theme_service: ThemeService, parent=None):
        super().__init__(parent)

        self._theme_service = theme_service

        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)

        # Ensure the dialog uses the current application stylesheet
        app = QApplication.instance()
        if isinstance(app, QApplication):
            self.setStyleSheet(app.styleSheet())

        self.setWindowTitle("About")
        self.setFixedSize(690, 425)
        self.ui.tabWidget.tabBar().setExpanding(True)

        # Always start on the first tab (About)
        self.ui.tabWidget.setCurrentIndex(0)

        # Set version from package metadata
        app_version = get_app_version()
        self.ui.aboutVersion.setText(f"v{app_version}")

        logo_file = QFile(":/assets/logo.svg")
        if logo_file.open(QIODevice.OpenModeFlag.ReadOnly):
            byte_array = logo_file.readAll()
            svg_data = bytes(byte_array.data())
            self.ui.logoLabel.setSvgData(svg_data)
            self.ui.logoLabel_2.setSvgData(svg_data)
            self.ui.logoLabel_3.setSvgData(svg_data)
            logo_file.close()
        else:
            logger.warning("Could not load logo from resources")

        self._setup_clickable_images()

        self.ui.copyVersion.clicked.connect(self._copy_version_to_clipboard)

    def _setup_clickable_images(self):
        """Set up clickable functionality for GitHub and Ko-fi links."""
        # Make labels look clickable
        self.ui.githubLink.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.kofiLink.setCursor(Qt.CursorShape.PointingHandCursor)

        # Override mouse events to handle clicks
        self.ui.githubLink.mousePressEvent = lambda event: self._open_github_link(event)
        self.ui.kofiLink.mousePressEvent = lambda event: self._open_kofi_link(event)

        # Configure GitHub link with light and dark images
        self.ui.githubLink.setImages(
            light_image_path=":/assets/GitHub_Lockup_Dark.png",
            dark_image_path=":/assets/GitHub_Lockup_Light.png",
        )

        # Connect to theme changes
        if self._theme_service:
            self._theme_service.theme_changed.connect(
                lambda: self._update_link_buttons()
            )

        self._update_link_buttons()

    def _update_link_buttons(self):
        current_theme = self._theme_service.get_current_theme()
        if current_theme and hasattr(current_theme, "category"):
            # Switch image based on theme category
            if current_theme.category == "dark":
                self.ui.githubLink.setMode(ThemeMode.DARK)
            else:
                self.ui.githubLink.setMode(ThemeMode.LIGHT)
        else:
            # Default to light mode if we can't determine theme
            self.ui.githubLink.setMode(ThemeMode.LIGHT)

    def _open_github_link(self, event):
        """Open the GitHub repository in the default browser."""
        if event.button() == Qt.MouseButton.LeftButton:
            QDesktopServices.openUrl(
                QUrl("https://github.com/KPandaK/metaeditor_safetensors")
            )

    def _open_kofi_link(self, event):
        """Open the Ko-fi page in the default browser."""
        if event.button() == Qt.MouseButton.LeftButton:
            QDesktopServices.openUrl(QUrl("https://ko-fi.com/kpandak"))

    def _copy_version_to_clipboard(self):
        """Copy the version string to the clipboard."""

        clipboard = QApplication.clipboard()
        app_version = get_app_version()
        version_text = f"v{app_version}"
        clipboard.setText(version_text)
