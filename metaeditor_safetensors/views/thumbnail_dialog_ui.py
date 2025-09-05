# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'thumbnail_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QSizePolicy,
    QWidget)

from metaeditor_safetensors.widgets.image_widget import ImageWidget

class Ui_ThumbnailDialog(object):
    def setupUi(self, ThumbnailDialog):
        if not ThumbnailDialog.objectName():
            ThumbnailDialog.setObjectName(u"ThumbnailDialog")
        ThumbnailDialog.resize(363, 312)
        self.horizontalLayout = QHBoxLayout(ThumbnailDialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.image = ImageWidget(ThumbnailDialog)
        self.image.setObjectName(u"image")

        self.horizontalLayout.addWidget(self.image)


        self.retranslateUi(ThumbnailDialog)

        QMetaObject.connectSlotsByName(ThumbnailDialog)
    # setupUi

    def retranslateUi(self, ThumbnailDialog):
        ThumbnailDialog.setWindowTitle(QCoreApplication.translate("ThumbnailDialog", u"Thumbnail Preview", None))
    # retranslateUi

