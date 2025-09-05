from PySide6.QtWidgets import QDialog
from .thumbnail_dialog_ui import Ui_ThumbnailDialog
from PySide6.QtGui import QPixmap


class ThumbnailDialog(QDialog, Ui_ThumbnailDialog):
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.image.setPixmap(pixmap)
        self.resize(pixmap.size())
