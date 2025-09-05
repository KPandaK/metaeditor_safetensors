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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QTabWidget, QVBoxLayout, QWidget)

from metaeditor_safetensors.widgets.svg_widget import SvgWidget
from . import resources_rc

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        if not AboutDialog.objectName():
            AboutDialog.setObjectName(u"AboutDialog")
        AboutDialog.resize(690, 425)
        AboutDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(AboutDialog)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(15, 15, 15, 15)
        self.tabWidget = QTabWidget(AboutDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setAutoFillBackground(True)
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.South)
        self.tabWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget.setDocumentMode(True)
        self.aboutTab = QWidget()
        self.aboutTab.setObjectName(u"aboutTab")
        self.horizontalLayout_2 = QHBoxLayout(self.aboutTab)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(0)
        self.topLayout.setObjectName(u"topLayout")
        self.logoLabel = SvgWidget(self.aboutTab)
        self.logoLabel.setObjectName(u"logoLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logoLabel.sizePolicy().hasHeightForWidth())
        self.logoLabel.setSizePolicy(sizePolicy)
        self.logoLabel.setMinimumSize(QSize(250, 250))
        self.logoLabel.setMaximumSize(QSize(250, 250))

        self.topLayout.addWidget(self.logoLabel)

        self.rightColumnLayout = QVBoxLayout()
        self.rightColumnLayout.setSpacing(6)
        self.rightColumnLayout.setObjectName(u"rightColumnLayout")
        self.aboutTitle = QLabel(self.aboutTab)
        self.aboutTitle.setObjectName(u"aboutTitle")
        sizePolicy.setHeightForWidth(self.aboutTitle.sizePolicy().hasHeightForWidth())
        self.aboutTitle.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(18)
        self.aboutTitle.setFont(font)

        self.rightColumnLayout.addWidget(self.aboutTitle)

        self.versionHLayout = QHBoxLayout()
        self.versionHLayout.setSpacing(0)
        self.versionHLayout.setObjectName(u"versionHLayout")
        self.aboutVersion = QLabel(self.aboutTab)
        self.aboutVersion.setObjectName(u"aboutVersion")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.aboutVersion.sizePolicy().hasHeightForWidth())
        self.aboutVersion.setSizePolicy(sizePolicy1)

        self.versionHLayout.addWidget(self.aboutVersion, 0, Qt.AlignmentFlag.AlignLeft)

        self.copyVersion = QPushButton(self.aboutTab)
        self.copyVersion.setObjectName(u"copyVersion")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.copyVersion.sizePolicy().hasHeightForWidth())
        self.copyVersion.setSizePolicy(sizePolicy2)
        self.copyVersion.setMinimumSize(QSize(24, 24))
        self.copyVersion.setMaximumSize(QSize(24, 24))
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.EditCopy))
        self.copyVersion.setIcon(icon)
        self.copyVersion.setIconSize(QSize(16, 16))

        self.versionHLayout.addWidget(self.copyVersion, 0, Qt.AlignmentFlag.AlignLeft)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.versionHLayout.addItem(self.horizontalSpacer)


        self.rightColumnLayout.addLayout(self.versionHLayout)

        self.aboutAuthor = QLabel(self.aboutTab)
        self.aboutAuthor.setObjectName(u"aboutAuthor")
        sizePolicy.setHeightForWidth(self.aboutAuthor.sizePolicy().hasHeightForWidth())
        self.aboutAuthor.setSizePolicy(sizePolicy)

        self.rightColumnLayout.addWidget(self.aboutAuthor)

        self.aboutDescription = QLabel(self.aboutTab)
        self.aboutDescription.setObjectName(u"aboutDescription")
        sizePolicy.setHeightForWidth(self.aboutDescription.sizePolicy().hasHeightForWidth())
        self.aboutDescription.setSizePolicy(sizePolicy)
        self.aboutDescription.setWordWrap(True)
        self.aboutDescription.setOpenExternalLinks(True)

        self.rightColumnLayout.addWidget(self.aboutDescription)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        self.rightColumnLayout.addItem(self.verticalSpacer_2)

        self.linksHLayout = QHBoxLayout()
        self.linksHLayout.setSpacing(10)
        self.linksHLayout.setObjectName(u"linksHLayout")
        self.kofiLink = QLabel(self.aboutTab)
        self.kofiLink.setObjectName(u"kofiLink")
        sizePolicy2.setHeightForWidth(self.kofiLink.sizePolicy().hasHeightForWidth())
        self.kofiLink.setSizePolicy(sizePolicy2)
        self.kofiLink.setMaximumSize(QSize(100, 56))
        self.kofiLink.setPixmap(QPixmap(u":/assets/support_me.png"))
        self.kofiLink.setScaledContents(True)

        self.linksHLayout.addWidget(self.kofiLink)

        self.githubLink = QLabel(self.aboutTab)
        self.githubLink.setObjectName(u"githubLink")
        sizePolicy2.setHeightForWidth(self.githubLink.sizePolicy().hasHeightForWidth())
        self.githubLink.setSizePolicy(sizePolicy2)
        self.githubLink.setMaximumSize(QSize(163, 40))
        self.githubLink.setPixmap(QPixmap(u":/assets/GitHub_Lockup_Dark.png"))
        self.githubLink.setScaledContents(True)

        self.linksHLayout.addWidget(self.githubLink)


        self.rightColumnLayout.addLayout(self.linksHLayout)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.rightColumnLayout.addItem(self.verticalSpacer)


        self.topLayout.addLayout(self.rightColumnLayout)

        self.topLayout.setStretch(1, 1)

        self.horizontalLayout_2.addLayout(self.topLayout)

        self.tabWidget.addTab(self.aboutTab, "")
        self.creditsTab = QWidget()
        self.creditsTab.setObjectName(u"creditsTab")
        self.horizontalLayout_4 = QHBoxLayout(self.creditsTab)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.topLayout_2 = QHBoxLayout()
        self.topLayout_2.setSpacing(0)
        self.topLayout_2.setObjectName(u"topLayout_2")
        self.logoLabel_2 = SvgWidget(self.creditsTab)
        self.logoLabel_2.setObjectName(u"logoLabel_2")
        sizePolicy.setHeightForWidth(self.logoLabel_2.sizePolicy().hasHeightForWidth())
        self.logoLabel_2.setSizePolicy(sizePolicy)
        self.logoLabel_2.setMinimumSize(QSize(250, 250))
        self.logoLabel_2.setMaximumSize(QSize(250, 250))

        self.topLayout_2.addWidget(self.logoLabel_2)

        self.textLayout_2 = QVBoxLayout()
        self.textLayout_2.setObjectName(u"textLayout_2")
        self.textLayout_2.setContentsMargins(0, -1, -1, -1)
        self.creditsTitle = QLabel(self.creditsTab)
        self.creditsTitle.setObjectName(u"creditsTitle")
        sizePolicy.setHeightForWidth(self.creditsTitle.sizePolicy().hasHeightForWidth())
        self.creditsTitle.setSizePolicy(sizePolicy)
        self.creditsTitle.setFont(font)

        self.textLayout_2.addWidget(self.creditsTitle)

        self.creditsText = QLabel(self.creditsTab)
        self.creditsText.setObjectName(u"creditsText")
        sizePolicy.setHeightForWidth(self.creditsText.sizePolicy().hasHeightForWidth())
        self.creditsText.setSizePolicy(sizePolicy)
        self.creditsText.setWordWrap(True)
        self.creditsText.setOpenExternalLinks(True)

        self.textLayout_2.addWidget(self.creditsText)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.textLayout_2.addItem(self.verticalSpacer_4)


        self.topLayout_2.addLayout(self.textLayout_2)

        self.topLayout_2.setStretch(1, 1)

        self.horizontalLayout_4.addLayout(self.topLayout_2)

        self.tabWidget.addTab(self.creditsTab, "")
        self.licenseTab = QWidget()
        self.licenseTab.setObjectName(u"licenseTab")
        self.horizontalLayout_6 = QHBoxLayout(self.licenseTab)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.topLayout_3 = QHBoxLayout()
        self.topLayout_3.setSpacing(0)
        self.topLayout_3.setObjectName(u"topLayout_3")
        self.logoLabel_3 = SvgWidget(self.licenseTab)
        self.logoLabel_3.setObjectName(u"logoLabel_3")
        sizePolicy.setHeightForWidth(self.logoLabel_3.sizePolicy().hasHeightForWidth())
        self.logoLabel_3.setSizePolicy(sizePolicy)
        self.logoLabel_3.setMinimumSize(QSize(250, 250))
        self.logoLabel_3.setMaximumSize(QSize(250, 250))

        self.topLayout_3.addWidget(self.logoLabel_3)

        self.textLayout_3 = QVBoxLayout()
        self.textLayout_3.setObjectName(u"textLayout_3")
        self.textLayout_3.setContentsMargins(0, -1, -1, -1)
        self.licenseTitle = QLabel(self.licenseTab)
        self.licenseTitle.setObjectName(u"licenseTitle")
        sizePolicy.setHeightForWidth(self.licenseTitle.sizePolicy().hasHeightForWidth())
        self.licenseTitle.setSizePolicy(sizePolicy)

        self.textLayout_3.addWidget(self.licenseTitle)

        self.scrollArea = QScrollArea(self.licenseTab)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy3)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 359, 358))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.creditsText_2 = QLabel(self.scrollAreaWidgetContents)
        self.creditsText_2.setObjectName(u"creditsText_2")
        sizePolicy3.setHeightForWidth(self.creditsText_2.sizePolicy().hasHeightForWidth())
        self.creditsText_2.setSizePolicy(sizePolicy3)
        self.creditsText_2.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.creditsText_2)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.textLayout_3.addWidget(self.scrollArea)


        self.topLayout_3.addLayout(self.textLayout_3)

        self.topLayout_3.setStretch(1, 1)

        self.horizontalLayout_6.addLayout(self.topLayout_3)

        self.tabWidget.addTab(self.licenseTab, "")

        self.verticalLayout.addWidget(self.tabWidget)


        self.retranslateUi(AboutDialog)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AboutDialog)
    # setupUi

    def retranslateUi(self, AboutDialog):
        self.aboutTitle.setText(QCoreApplication.translate("AboutDialog", u"Safetensors Metadata Editor", None))
        self.aboutVersion.setText(QCoreApplication.translate("AboutDialog", u"v1.0.0", None))
#if QT_CONFIG(tooltip)
        self.copyVersion.setToolTip(QCoreApplication.translate("AboutDialog", u"Copy version to clipboard.", None))
#endif // QT_CONFIG(tooltip)
        self.copyVersion.setText("")
        self.aboutAuthor.setText(QCoreApplication.translate("AboutDialog", u"Created by: KPandaK", None))
        self.aboutDescription.setText(QCoreApplication.translate("AboutDialog", u"<html><head/><body><p>This is a free and open source app for viewing and editing metadata in safetensors model files. </p><p>It implements v1.01 of Stability.AI's model metadata standard <a href=\"https://github.com/Stability-AI/ModelSpec\"><span style=\" text-decoration: underline; color:#92ebff;\">specification</span></a>.</p><p>If you enjoy this app, feel free to tip me for a coffee!</p></body></html>", None))
        self.kofiLink.setText("")
        self.githubLink.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.aboutTab), QCoreApplication.translate("AboutDialog", u"About", None))
        self.creditsTitle.setText(QCoreApplication.translate("AboutDialog", u"Credits", None))
        self.creditsText.setText(QCoreApplication.translate("AboutDialog", u"<html><head/><body><p>Original Safetensors Icon by <a href=\"https://github.com/SHADOW-LIGHTS\"><span style=\" text-decoration: underline; color:#92ebff;\">SHADOW-LIGHTS</span></a></p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.creditsTab), QCoreApplication.translate("AboutDialog", u"Credits", None))
        self.licenseTitle.setText(QCoreApplication.translate("AboutDialog", u"The MIT License (MIT)", None))
        self.creditsText_2.setText(QCoreApplication.translate("AboutDialog", u"<html><head/><body><p>Copyright \u00a9 2025 KPandaK</p><p>Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \u201cSoftware\u201d), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:</p><p>The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.</p><p>THE SOFTWARE IS PROVIDED \u201cAS IS\u201d, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OU"
                        "T OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.licenseTab), QCoreApplication.translate("AboutDialog", u"License", None))
        pass
    # retranslateUi

