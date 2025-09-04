# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from metaeditor_safetensors.widgets.svg_widget import SvgWidget
from . import resources_rc

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        if not AboutDialog.objectName():
            AboutDialog.setObjectName(u"AboutDialog")
        AboutDialog.resize(639, 351)
        AboutDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(AboutDialog)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(12, 12, 12, 12)
        self.topLayout = QHBoxLayout()
        self.topLayout.setObjectName(u"topLayout")
        self.logoLabel = SvgWidget(AboutDialog)
        self.logoLabel.setObjectName(u"logoLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logoLabel.sizePolicy().hasHeightForWidth())
        self.logoLabel.setSizePolicy(sizePolicy)
        self.logoLabel.setMinimumSize(QSize(64, 64))
        self.logoLabel.setMaximumSize(QSize(1024, 1024))

        self.topLayout.addWidget(self.logoLabel)

        self.textLayout = QVBoxLayout()
        self.textLayout.setObjectName(u"textLayout")
        self.textLayout.setContentsMargins(10, -1, -1, -1)
        self.aboutTitle = QLabel(AboutDialog)
        self.aboutTitle.setObjectName(u"aboutTitle")

        self.textLayout.addWidget(self.aboutTitle)

        self.aboutVersion = QLabel(AboutDialog)
        self.aboutVersion.setObjectName(u"aboutVersion")

        self.textLayout.addWidget(self.aboutVersion)

        self.aboutAuthor = QLabel(AboutDialog)
        self.aboutAuthor.setObjectName(u"aboutAuthor")

        self.textLayout.addWidget(self.aboutAuthor)

        self.aboutDescription = QLabel(AboutDialog)
        self.aboutDescription.setObjectName(u"aboutDescription")
        self.aboutDescription.setWordWrap(True)

        self.textLayout.addWidget(self.aboutDescription)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.textLayout.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.kofiLink = QLabel(AboutDialog)
        self.kofiLink.setObjectName(u"kofiLink")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.kofiLink.sizePolicy().hasHeightForWidth())
        self.kofiLink.setSizePolicy(sizePolicy1)
        self.kofiLink.setMaximumSize(QSize(100, 56))
        self.kofiLink.setPixmap(QPixmap(u":/assets/support_me.png"))
        self.kofiLink.setScaledContents(True)

        self.horizontalLayout.addWidget(self.kofiLink)


        self.textLayout.addLayout(self.horizontalLayout)


        self.topLayout.addLayout(self.textLayout)

        self.topLayout.setStretch(0, 45)
        self.topLayout.setStretch(1, 55)

        self.verticalLayout.addLayout(self.topLayout)

        self.separatorLine = QFrame(AboutDialog)
        self.separatorLine.setObjectName(u"separatorLine")
        self.separatorLine.setFrameShape(QFrame.Shape.HLine)
        self.separatorLine.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.separatorLine)

        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setObjectName(u"bottomLayout")
        self.aboutLink = QLabel(AboutDialog)
        self.aboutLink.setObjectName(u"aboutLink")
        self.aboutLink.setOpenExternalLinks(True)

        self.bottomLayout.addWidget(self.aboutLink)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottomLayout.addItem(self.horizontalSpacer)

        self.closeButton = QPushButton(AboutDialog)
        self.closeButton.setObjectName(u"closeButton")

        self.bottomLayout.addWidget(self.closeButton)


        self.verticalLayout.addLayout(self.bottomLayout)


        self.retranslateUi(AboutDialog)

        QMetaObject.connectSlotsByName(AboutDialog)
    # setupUi

    def retranslateUi(self, AboutDialog):
        self.aboutTitle.setText(QCoreApplication.translate("AboutDialog", u"Safetensors Metadata Editor", None))
        self.aboutVersion.setText(QCoreApplication.translate("AboutDialog", u"Version: v1.0.0", None))
        self.aboutAuthor.setText(QCoreApplication.translate("AboutDialog", u"Created by: KPandaK", None))
        self.aboutDescription.setText(QCoreApplication.translate("AboutDialog", u"A simple, intuitive tool for viewing and editing metadata in Safetensors model files.", None))
        self.kofiLink.setText("")
        self.aboutLink.setText(QCoreApplication.translate("AboutDialog", u"<a href='https://github.com/KPandaK/metaeditor_safetensors'>GitHub Repository</a>", None))
        self.closeButton.setText(QCoreApplication.translate("AboutDialog", u"Close", None))
        pass
    # retranslateUi

