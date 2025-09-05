from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog

from .thumbnail_dialog_ui import Ui_ThumbnailDialog


class ThumbnailDialog(QDialog, Ui_ThumbnailDialog):
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_size = screen_geometry.size()

        # Add a buffer
        max_width = screen_size.width() * 0.9
        max_height = screen_size.height() * 0.9

        scaled_pixmap = pixmap
        if pixmap.width() > max_width or pixmap.height() > max_height:
            scaled_pixmap = pixmap.scaled(
                int(max_width),
                int(max_height),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        self.image.setPixmap(scaled_pixmap)
        self.resize(scaled_pixmap.size())
