import os
from PySide6.QtWidgets import QDialog
from ..resources.about_dialog_ui import Ui_AboutDialog
from .._version import __version__
from ..components.svg_widget import SvgWidget

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)

        self.setWindowTitle("About")
        self.setFixedSize(640,350)
        
        # Set version from _version.py
        self.ui.aboutVersion.setText(f"Version {__version__}")
        # Set icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.svg")
        if os.path.exists(icon_path):
            self.ui.iconLabel.loadSvg(icon_path)

        # Connect close button
        self.ui.closeButton.clicked.connect(self.close)