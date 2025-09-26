from __future__ import annotations

import logging
from importlib.metadata import PackageNotFoundError, version

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QDialog

from ..layouts.about_ui_layout import Ui_AboutDialog

logger = logging.getLogger(__name__)


def get_app_version() -> str:
    try:
        return version("metaeditor_safetensors")
    except PackageNotFoundError:
        return "dev"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_AboutDialog()
        self.ui.setup_ui(self)

        # Ensure the dialog uses the current application stylesheet
        app = QApplication.instance()
        if isinstance(app, QApplication):
            self.setStyleSheet(app.styleSheet())

        self.setWindowTitle("About")
        self.setFixedSize(690, 425)

        # Set version from package metadata
        self.ui.about_version.setText(f"v{get_app_version()}")

        self._setup_clickable_images()

        self.ui.copy_version_btn.clicked.connect(self._copy_version_to_clipboard)

    def _setup_clickable_images(self) -> None:
        # Override mouse events to handle clicks
        self.ui.github_link.mousePressEvent = lambda event: self._open_github_link(
            event
        )
        self.ui.kofi_link.mousePressEvent = lambda event: self._open_kofi_link(event)

    def _open_github_link(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            QDesktopServices.openUrl(
                QUrl("https://github.com/KPandaK/metaeditor_safetensors")
            )

    def _open_kofi_link(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            QDesktopServices.openUrl(QUrl("https://ko-fi.com/kpandak"))

    def _copy_version_to_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(f"v{get_app_version()}")
