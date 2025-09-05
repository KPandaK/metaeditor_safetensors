from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QClipboard, QDesktopServices
from PySide6.QtWidgets import QDialog

from .._version import __version__
from ..widgets.svg_widget import SvgWidget
from .about_dialog_ui import Ui_AboutDialog


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)

        self.setWindowTitle("About")
        self.setFixedSize(690, 425)
        self.ui.tabWidget.tabBar().setExpanding(True)

        # Always start on the first tab (About)
        self.ui.tabWidget.setCurrentIndex(0)

        # Set version from _version.py
        self.ui.aboutVersion.setText(f"v{__version__}")

        # Set logo from Qt resources for all tabs
        from PySide6.QtCore import QFile, QIODevice

        style_file = QFile(":/assets/logo.svg")
        if style_file.open(QIODevice.ReadOnly):
            svg_data = style_file.readAll()
            self.ui.logoLabel.setSvgData(svg_data)  # About tab
            self.ui.logoLabel_2.setSvgData(svg_data)  # Credits tab
            self.ui.logoLabel_3.setSvgData(svg_data)  # License tab
            style_file.close()
        else:
            print("Warning: Could not load logo from resources")

        # Make GitHub and Ko-fi links clickable
        self._setup_clickable_links()

        self.ui.copyVersion.clicked.connect(self._copy_version_to_clipboard)

    def _setup_clickable_links(self):
        """Set up clickable functionality for GitHub and Ko-fi links."""
        # Make labels look clickable
        self.ui.githubLink.setCursor(Qt.PointingHandCursor)
        self.ui.kofiLink.setCursor(Qt.PointingHandCursor)

        # Add tooltips
        self.ui.githubLink.setToolTip("Visit the GitHub repository")
        self.ui.kofiLink.setToolTip(
            "If you like this, consider buying me a coffee on Ko-fi!"
        )

        # Override mouse events to handle clicks
        self.ui.githubLink.mousePressEvent = lambda event: self._open_github_link(event)
        self.ui.kofiLink.mousePressEvent = lambda event: self._open_kofi_link(event)

    def _open_github_link(self, event):
        """Open the GitHub repository in the default browser."""
        if event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(
                QUrl("https://github.com/KPandaK/metaeditor_safetensors")
            )

    def _open_kofi_link(self, event):
        """Open the Ko-fi page in the default browser."""
        if event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(QUrl("https://ko-fi.com/kpandak"))

    def _copy_version_to_clipboard(self):
        """Copy the version string to the clipboard."""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        version_text = f"v{__version__}"
        clipboard.setText(version_text)
