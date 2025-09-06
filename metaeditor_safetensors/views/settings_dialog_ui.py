# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QLabel,
    QRadioButton, QSizePolicy, QSpacerItem, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        if not SettingsDialog.objectName():
            SettingsDialog.setObjectName(u"SettingsDialog")
        SettingsDialog.resize(500, 400)
        SettingsDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(SettingsDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(SettingsDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.themeTab = QWidget()
        self.themeTab.setObjectName(u"themeTab")
        self.themeTabLayout = QVBoxLayout(self.themeTab)
        self.themeTabLayout.setObjectName(u"themeTabLayout")
        self.themeSelectionGroup = QGroupBox(self.themeTab)
        self.themeSelectionGroup.setObjectName(u"themeSelectionGroup")
        self.themeGroupLayout = QVBoxLayout(self.themeSelectionGroup)
        self.themeGroupLayout.setObjectName(u"themeGroupLayout")
        self.autoThemeRadio = QRadioButton(self.themeSelectionGroup)
        self.autoThemeRadio.setObjectName(u"autoThemeRadio")
        self.autoThemeRadio.setChecked(True)

        self.themeGroupLayout.addWidget(self.autoThemeRadio)

        self.lightThemeRadio = QRadioButton(self.themeSelectionGroup)
        self.lightThemeRadio.setObjectName(u"lightThemeRadio")

        self.themeGroupLayout.addWidget(self.lightThemeRadio)

        self.darkThemeRadio = QRadioButton(self.themeSelectionGroup)
        self.darkThemeRadio.setObjectName(u"darkThemeRadio")

        self.themeGroupLayout.addWidget(self.darkThemeRadio)

        self.customThemeRadio = QRadioButton(self.themeSelectionGroup)
        self.customThemeRadio.setObjectName(u"customThemeRadio")

        self.themeGroupLayout.addWidget(self.customThemeRadio)


        self.themeTabLayout.addWidget(self.themeSelectionGroup)

        self.themeDetailsGroup = QGroupBox(self.themeTab)
        self.themeDetailsGroup.setObjectName(u"themeDetailsGroup")
        self.themeDetailsLayout = QVBoxLayout(self.themeDetailsGroup)
        self.themeDetailsLayout.setObjectName(u"themeDetailsLayout")
        self.themeSelectionLabel = QLabel(self.themeDetailsGroup)
        self.themeSelectionLabel.setObjectName(u"themeSelectionLabel")

        self.themeDetailsLayout.addWidget(self.themeSelectionLabel)

        self.themeComboBox = QComboBox(self.themeDetailsGroup)
        self.themeComboBox.setObjectName(u"themeComboBox")
        self.themeComboBox.setEnabled(False)

        self.themeDetailsLayout.addWidget(self.themeComboBox)


        self.themeTabLayout.addWidget(self.themeDetailsGroup)

        self.themeInfoGroup = QGroupBox(self.themeTab)
        self.themeInfoGroup.setObjectName(u"themeInfoGroup")
        self.themeInfoLayout = QFormLayout(self.themeInfoGroup)
        self.themeInfoLayout.setObjectName(u"themeInfoLayout")
        self.currentThemeLabel = QLabel(self.themeInfoGroup)
        self.currentThemeLabel.setObjectName(u"currentThemeLabel")

        self.themeInfoLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.currentThemeLabel)

        self.currentThemeValue = QLabel(self.themeInfoGroup)
        self.currentThemeValue.setObjectName(u"currentThemeValue")

        self.themeInfoLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.currentThemeValue)

        self.systemThemeLabel = QLabel(self.themeInfoGroup)
        self.systemThemeLabel.setObjectName(u"systemThemeLabel")

        self.themeInfoLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.systemThemeLabel)

        self.systemThemeValue = QLabel(self.themeInfoGroup)
        self.systemThemeValue.setObjectName(u"systemThemeValue")

        self.themeInfoLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.systemThemeValue)


        self.themeTabLayout.addWidget(self.themeInfoGroup)

        self.themeVerticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.themeTabLayout.addItem(self.themeVerticalSpacer)

        self.tabWidget.addTab(self.themeTab, "")
        self.generalTab = QWidget()
        self.generalTab.setObjectName(u"generalTab")
        self.generalTabLayout = QVBoxLayout(self.generalTab)
        self.generalTabLayout.setObjectName(u"generalTabLayout")
        self.generalPlaceholder = QLabel(self.generalTab)
        self.generalPlaceholder.setObjectName(u"generalPlaceholder")
        self.generalPlaceholder.setAlignment(Qt.AlignCenter)

        self.generalTabLayout.addWidget(self.generalPlaceholder)

        self.generalVerticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.generalTabLayout.addItem(self.generalVerticalSpacer)

        self.tabWidget.addTab(self.generalTab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.buttonBox = QDialogButtonBox(SettingsDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(SettingsDialog)
        self.buttonBox.accepted.connect(SettingsDialog.accept)
        self.buttonBox.rejected.connect(SettingsDialog.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(SettingsDialog)
    # setupUi

    def retranslateUi(self, SettingsDialog):
        SettingsDialog.setWindowTitle(QCoreApplication.translate("SettingsDialog", u"Settings", None))
        self.themeSelectionGroup.setTitle(QCoreApplication.translate("SettingsDialog", u"Theme Selection", None))
        self.autoThemeRadio.setText(QCoreApplication.translate("SettingsDialog", u"Auto (Follow System Theme)", None))
        self.lightThemeRadio.setText(QCoreApplication.translate("SettingsDialog", u"Light Theme", None))
        self.darkThemeRadio.setText(QCoreApplication.translate("SettingsDialog", u"Dark Theme", None))
        self.customThemeRadio.setText(QCoreApplication.translate("SettingsDialog", u"Custom Theme", None))
        self.themeDetailsGroup.setTitle(QCoreApplication.translate("SettingsDialog", u"Theme Details", None))
        self.themeSelectionLabel.setText(QCoreApplication.translate("SettingsDialog", u"Select specific theme:", None))
        self.themeInfoGroup.setTitle(QCoreApplication.translate("SettingsDialog", u"Current Theme Information", None))
        self.currentThemeLabel.setText(QCoreApplication.translate("SettingsDialog", u"Current Theme:", None))
        self.currentThemeValue.setText(QCoreApplication.translate("SettingsDialog", u"Auto (System Default)", None))
        self.systemThemeLabel.setText(QCoreApplication.translate("SettingsDialog", u"System Theme:", None))
        self.systemThemeValue.setText(QCoreApplication.translate("SettingsDialog", u"Light", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.themeTab), QCoreApplication.translate("SettingsDialog", u"Theme", None))
        self.generalPlaceholder.setText(QCoreApplication.translate("SettingsDialog", u"General settings will be added in future versions.", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.generalTab), QCoreApplication.translate("SettingsDialog", u"General", None))
    # retranslateUi

