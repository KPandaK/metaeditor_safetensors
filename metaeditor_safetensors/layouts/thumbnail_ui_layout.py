from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QHBoxLayout

from ..widgets.image_widget import ImageWidget


class Ui_ThumbnailDialog(object):
    def setup_ui(self, dialog):
        if not dialog.objectName():
            dialog.setObjectName("ThumbnailDialog")
        # dialog.resize(363, 312)

        # Main layout
        horizontal_layout = QHBoxLayout(dialog)
        self.image = ImageWidget(dialog)
        self.image.setObjectName("image")
        horizontal_layout.addWidget(self.image)

        self.retranslateUi(dialog)

    def retranslateUi(self, dialog):
        dialog.setWindowTitle(
            QCoreApplication.translate("ThumbnailDialog", "Thumbnail Preview", None)
        )
