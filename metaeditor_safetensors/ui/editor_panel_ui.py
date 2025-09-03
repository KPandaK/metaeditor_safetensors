# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'editor_panel.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QDateTimeEdit, QHBoxLayout,
    QLabel, QLineEdit, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QTextEdit, QVBoxLayout,
    QWidget)

from metaeditor_safetensors.ui.image_widget import ImageWidget

class Ui_EditorPanel(object):
    def setupUi(self, EditorPanel):
        if not EditorPanel.objectName():
            EditorPanel.setObjectName(u"EditorPanel")
        EditorPanel.resize(900, 450)
        self.verticalLayout = QVBoxLayout(EditorPanel)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.leftColumn = QVBoxLayout()
        self.leftColumn.setObjectName(u"leftColumn")
        self.titleLabel = QLabel(EditorPanel)
        self.titleLabel.setObjectName(u"titleLabel")

        self.leftColumn.addWidget(self.titleLabel)

        self.titleEdit = QLineEdit(EditorPanel)
        self.titleEdit.setObjectName(u"titleEdit")

        self.leftColumn.addWidget(self.titleEdit)

        self.descriptionLabel = QLabel(EditorPanel)
        self.descriptionLabel.setObjectName(u"descriptionLabel")

        self.leftColumn.addWidget(self.descriptionLabel)

        self.descriptionEdit = QTextEdit(EditorPanel)
        self.descriptionEdit.setObjectName(u"descriptionEdit")
        self.descriptionEdit.setMaximumSize(QSize(16777215, 100))

        self.leftColumn.addWidget(self.descriptionEdit)

        self.authorDateLayout = QHBoxLayout()
        self.authorDateLayout.setObjectName(u"authorDateLayout")
        self.authorLayout = QVBoxLayout()
        self.authorLayout.setObjectName(u"authorLayout")
        self.authorLabel = QLabel(EditorPanel)
        self.authorLabel.setObjectName(u"authorLabel")

        self.authorLayout.addWidget(self.authorLabel)

        self.authorEdit = QLineEdit(EditorPanel)
        self.authorEdit.setObjectName(u"authorEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.authorEdit.sizePolicy().hasHeightForWidth())
        self.authorEdit.setSizePolicy(sizePolicy)

        self.authorLayout.addWidget(self.authorEdit)


        self.authorDateLayout.addLayout(self.authorLayout)

        self.dateLayout = QVBoxLayout()
        self.dateLayout.setObjectName(u"dateLayout")
        self.dateLabel = QLabel(EditorPanel)
        self.dateLabel.setObjectName(u"dateLabel")
        self.dateLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.dateLayout.addWidget(self.dateLabel)

        self.dateTimeEdit = QDateTimeEdit(EditorPanel)
        self.dateTimeEdit.setObjectName(u"dateTimeEdit")
        self.dateTimeEdit.setMinimumSize(QSize(140, 22))
        self.dateTimeEdit.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.dateTimeEdit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.dateTimeEdit.setCalendarPopup(True)

        self.dateLayout.addWidget(self.dateTimeEdit)


        self.authorDateLayout.addLayout(self.dateLayout)


        self.leftColumn.addLayout(self.authorDateLayout)

        self.licenseLabel = QLabel(EditorPanel)
        self.licenseLabel.setObjectName(u"licenseLabel")

        self.leftColumn.addWidget(self.licenseLabel)

        self.licenseEdit = QLineEdit(EditorPanel)
        self.licenseEdit.setObjectName(u"licenseEdit")

        self.leftColumn.addWidget(self.licenseEdit)

        self.usageHintLabel = QLabel(EditorPanel)
        self.usageHintLabel.setObjectName(u"usageHintLabel")

        self.leftColumn.addWidget(self.usageHintLabel)

        self.usageHintEdit = QLineEdit(EditorPanel)
        self.usageHintEdit.setObjectName(u"usageHintEdit")

        self.leftColumn.addWidget(self.usageHintEdit)

        self.tagsLabel = QLabel(EditorPanel)
        self.tagsLabel.setObjectName(u"tagsLabel")

        self.leftColumn.addWidget(self.tagsLabel)

        self.tagsEdit = QLineEdit(EditorPanel)
        self.tagsEdit.setObjectName(u"tagsEdit")

        self.leftColumn.addWidget(self.tagsEdit)

        self.mergedFromLabel = QLabel(EditorPanel)
        self.mergedFromLabel.setObjectName(u"mergedFromLabel")

        self.leftColumn.addWidget(self.mergedFromLabel)

        self.mergedFromEdit = QLineEdit(EditorPanel)
        self.mergedFromEdit.setObjectName(u"mergedFromEdit")

        self.leftColumn.addWidget(self.mergedFromEdit)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.leftColumn.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.leftColumn)

        self.thumbnailColumn = QVBoxLayout()
        self.thumbnailColumn.setObjectName(u"thumbnailColumn")
        self.thumbnailLabel = QLabel(EditorPanel)
        self.thumbnailLabel.setObjectName(u"thumbnailLabel")

        self.thumbnailColumn.addWidget(self.thumbnailLabel)

        self.thumbnailDisplay = ImageWidget(EditorPanel)
        self.thumbnailDisplay.setObjectName(u"thumbnailDisplay")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(1)
        sizePolicy1.setHeightForWidth(self.thumbnailDisplay.sizePolicy().hasHeightForWidth())
        self.thumbnailDisplay.setSizePolicy(sizePolicy1)

        self.thumbnailColumn.addWidget(self.thumbnailDisplay)

        self.thumbnailButtonsLayout = QHBoxLayout()
        self.thumbnailButtonsLayout.setObjectName(u"thumbnailButtonsLayout")
        self.setThumbnailBtn = QPushButton(EditorPanel)
        self.setThumbnailBtn.setObjectName(u"setThumbnailBtn")
        self.setThumbnailBtn.setMaximumSize(QSize(16777215, 24))

        self.thumbnailButtonsLayout.addWidget(self.setThumbnailBtn)

        self.viewThumbnailBtn = QPushButton(EditorPanel)
        self.viewThumbnailBtn.setObjectName(u"viewThumbnailBtn")
        self.viewThumbnailBtn.setMaximumSize(QSize(16777215, 24))

        self.thumbnailButtonsLayout.addWidget(self.viewThumbnailBtn)

        self.clearThumbnailBtn = QPushButton(EditorPanel)
        self.clearThumbnailBtn.setObjectName(u"clearThumbnailBtn")
        self.clearThumbnailBtn.setMaximumSize(QSize(16777215, 24))

        self.thumbnailButtonsLayout.addWidget(self.clearThumbnailBtn)


        self.thumbnailColumn.addLayout(self.thumbnailButtonsLayout)

        self.thumbnailSpacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.thumbnailColumn.addItem(self.thumbnailSpacer)


        self.horizontalLayout.addLayout(self.thumbnailColumn)

        self.horizontalLayout.setStretch(0, 6)
        self.horizontalLayout.setStretch(1, 4)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.progressBar = QProgressBar(EditorPanel)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMaximumSize(QSize(16777215, 6))
        self.progressBar.setVisible(False)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)

        self.verticalLayout.addWidget(self.progressBar)


        self.retranslateUi(EditorPanel)

        QMetaObject.connectSlotsByName(EditorPanel)
    # setupUi

    def retranslateUi(self, EditorPanel):
        EditorPanel.setWindowTitle(QCoreApplication.translate("EditorPanel", u"Metadata Editor", None))
        self.titleLabel.setText(QCoreApplication.translate("EditorPanel", u"Title:", None))
        self.titleEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Enter model title...", None))
        self.descriptionLabel.setText(QCoreApplication.translate("EditorPanel", u"Description:", None))
        self.descriptionEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Describe your model...", None))
        self.authorLabel.setText(QCoreApplication.translate("EditorPanel", u"Author:", None))
        self.authorEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Author name...", None))
        self.dateLabel.setText(QCoreApplication.translate("EditorPanel", u"Date:", None))
        self.dateTimeEdit.setDisplayFormat(QCoreApplication.translate("EditorPanel", u"MM/dd/yyyy h:mm AP", None))
        self.licenseLabel.setText(QCoreApplication.translate("EditorPanel", u"License:", None))
        self.licenseEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"e.g. MIT, Apache 2.0, Custom...", None))
        self.usageHintLabel.setText(QCoreApplication.translate("EditorPanel", u"Usage Hint:", None))
        self.usageHintEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Usage instructions or hints...", None))
        self.tagsLabel.setText(QCoreApplication.translate("EditorPanel", u"Tags:", None))
        self.tagsEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"comma, separated, tags", None))
        self.mergedFromLabel.setText(QCoreApplication.translate("EditorPanel", u"Merged From:", None))
        self.mergedFromEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Source models if merged...", None))
        self.thumbnailLabel.setText(QCoreApplication.translate("EditorPanel", u"Thumbnail:", None))
        self.setThumbnailBtn.setText(QCoreApplication.translate("EditorPanel", u"Set", None))
        self.viewThumbnailBtn.setText(QCoreApplication.translate("EditorPanel", u"View", None))
        self.clearThumbnailBtn.setText(QCoreApplication.translate("EditorPanel", u"Clear", None))
    # retranslateUi

