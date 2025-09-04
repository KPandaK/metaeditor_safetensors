from PySide6.QtWidgets import QDialog
from .about_dialog_ui import Ui_AboutDialog
from .._version import __version__
from ..widgets.svg_widget import SvgWidget

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)

        self.setWindowTitle("About")
        self.setFixedSize(640, 350)
        
        # Set version from _version.py
        self.ui.aboutVersion.setText(f"Version: v{__version__}")
        
        # Set logo from Qt resources
        from PySide6.QtCore import QFile, QIODevice
        style_file = QFile(":/assets/logo.svg")
        if style_file.open(QIODevice.ReadOnly):
            svg_data = style_file.readAll()
            self.ui.logoLabel.setSvgData(svg_data)
            style_file.close()
        else:
            print("Warning: Could not load logo from resources")

        # Connect close button
        self.ui.closeButton.clicked.connect(self.close)