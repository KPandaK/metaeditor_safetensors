# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'metadata_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
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
from PySide6.QtWidgets import (QApplication, QDateTimeEdit, QHBoxLayout, QLabel,
    QLineEdit, QProgressBar, QPushButton, QSizePolicy,
    QSpacerItem, QTextEdit, QVBoxLayout, QWidget)

class Ui_MetadataEditor(object):
    def setupUi(self, MetadataEditor):
        if not MetadataEditor.objectName():
            MetadataEditor.setObjectName(u"MetadataEditor")
        MetadataEditor.resize(800, 600)
        self.verticalLayout = QVBoxLayout(MetadataEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.leftColumn = QVBoxLayout()
        self.leftColumn.setObjectName(u"leftColumn")
        self.titleLabel = QLabel(MetadataEditor)
        self.titleLabel.setObjectName(u"titleLabel")

        self.leftColumn.addWidget(self.titleLabel)

        self.titleEdit = QLineEdit(MetadataEditor)
        self.titleEdit.setObjectName(u"titleEdit")

        self.leftColumn.addWidget(self.titleEdit)

        self.descriptionLabel = QLabel(MetadataEditor)
        self.descriptionLabel.setObjectName(u"descriptionLabel")

        self.leftColumn.addWidget(self.descriptionLabel)

        self.descriptionEdit = QTextEdit(MetadataEditor)
        self.descriptionEdit.setObjectName(u"descriptionEdit")
        self.descriptionEdit.setMaximumSize(QSize(16777215, 100))

        self.leftColumn.addWidget(self.descriptionEdit)

        self.authorDateLayout = QHBoxLayout()
        self.authorDateLayout.setObjectName(u"authorDateLayout")
        self.authorLayout = QVBoxLayout()
        self.authorLayout.setObjectName(u"authorLayout")
        self.authorLabel = QLabel(MetadataEditor)
        self.authorLabel.setObjectName(u"authorLabel")

        self.authorLayout.addWidget(self.authorLabel)

        self.authorEdit = QLineEdit(MetadataEditor)
        self.authorEdit.setObjectName(u"authorEdit")

        self.authorLayout.addWidget(self.authorEdit)


        self.authorDateLayout.addLayout(self.authorLayout)

        self.dateLayout = QVBoxLayout()
        self.dateLayout.setObjectName(u"dateLayout")
        self.dateLabel = QLabel(MetadataEditor)
        self.dateLabel.setObjectName(u"dateLabel")

        self.dateLayout.addWidget(self.dateLabel)

        self.dateTimeEdit = QDateTimeEdit(MetadataEditor)
        self.dateTimeEdit.setObjectName(u"dateTimeEdit")

        self.dateLayout.addWidget(self.dateTimeEdit)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")

        self.dateLayout.addLayout(self.horizontalLayout_2)


        self.authorDateLayout.addLayout(self.dateLayout)


        self.leftColumn.addLayout(self.authorDateLayout)

        self.licenseLabel = QLabel(MetadataEditor)
        self.licenseLabel.setObjectName(u"licenseLabel")

        self.leftColumn.addWidget(self.licenseLabel)

        self.licenseEdit = QLineEdit(MetadataEditor)
        self.licenseEdit.setObjectName(u"licenseEdit")

        self.leftColumn.addWidget(self.licenseEdit)

        self.usageHintLabel = QLabel(MetadataEditor)
        self.usageHintLabel.setObjectName(u"usageHintLabel")

        self.leftColumn.addWidget(self.usageHintLabel)

        self.usageHintEdit = QLineEdit(MetadataEditor)
        self.usageHintEdit.setObjectName(u"usageHintEdit")

        self.leftColumn.addWidget(self.usageHintEdit)

        self.tagsLabel = QLabel(MetadataEditor)
        self.tagsLabel.setObjectName(u"tagsLabel")

        self.leftColumn.addWidget(self.tagsLabel)

        self.tagsEdit = QLineEdit(MetadataEditor)
        self.tagsEdit.setObjectName(u"tagsEdit")

        self.leftColumn.addWidget(self.tagsEdit)

        self.mergedFromLabel = QLabel(MetadataEditor)
        self.mergedFromLabel.setObjectName(u"mergedFromLabel")

        self.leftColumn.addWidget(self.mergedFromLabel)

        self.mergedFromEdit = QLineEdit(MetadataEditor)
        self.mergedFromEdit.setObjectName(u"mergedFromEdit")

        self.leftColumn.addWidget(self.mergedFromEdit)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.leftColumn.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.leftColumn)

        self.thumbnailColumn = QVBoxLayout()
        self.thumbnailColumn.setObjectName(u"thumbnailColumn")
        self.thumbnailLabel = QLabel(MetadataEditor)
        self.thumbnailLabel.setObjectName(u"thumbnailLabel")

        self.thumbnailColumn.addWidget(self.thumbnailLabel)

        self.thumbnailDisplay = QLabel(MetadataEditor)
        self.thumbnailDisplay.setObjectName(u"thumbnailDisplay")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.thumbnailDisplay.sizePolicy().hasHeightForWidth())
        self.thumbnailDisplay.setSizePolicy(sizePolicy)
        self.thumbnailDisplay.setMinimumSize(QSize(200, 200))
        self.thumbnailDisplay.setScaledContents(True)
        self.thumbnailDisplay.setStyleSheet(u"border: 2px dashed #cccccc; border-radius: 5px; background-color: #fafafa;")
        self.thumbnailDisplay.setAlignment(Qt.AlignCenter)

        self.thumbnailColumn.addWidget(self.thumbnailDisplay)

        self.thumbnailButtonsLayout = QHBoxLayout()
        self.thumbnailButtonsLayout.setObjectName(u"thumbnailButtonsLayout")
        self.setThumbnailBtn = QPushButton(MetadataEditor)
        self.setThumbnailBtn.setObjectName(u"setThumbnailBtn")
        self.setThumbnailBtn.setMaximumSize(QSize(16777215, 24))

        self.thumbnailButtonsLayout.addWidget(self.setThumbnailBtn)

        self.viewThumbnailBtn = QPushButton(MetadataEditor)
        self.viewThumbnailBtn.setObjectName(u"viewThumbnailBtn")
        self.viewThumbnailBtn.setMaximumSize(QSize(16777215, 24))

        self.thumbnailButtonsLayout.addWidget(self.viewThumbnailBtn)

        self.clearThumbnailBtn = QPushButton(MetadataEditor)
        self.clearThumbnailBtn.setObjectName(u"clearThumbnailBtn")
        self.clearThumbnailBtn.setMaximumSize(QSize(16777215, 24))

        self.thumbnailButtonsLayout.addWidget(self.clearThumbnailBtn)


        self.thumbnailColumn.addLayout(self.thumbnailButtonsLayout)

        self.thumbnailSpacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.thumbnailColumn.addItem(self.thumbnailSpacer)


        self.horizontalLayout.addLayout(self.thumbnailColumn)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.progressBar = QProgressBar(MetadataEditor)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        self.verticalLayout.addWidget(self.progressBar)

        self.statusLog = QTextEdit(MetadataEditor)
        self.statusLog.setObjectName(u"statusLog")
        self.statusLog.setMaximumSize(QSize(16777215, 120))
        self.statusLog.setReadOnly(True)

        self.verticalLayout.addWidget(self.statusLog)


        self.retranslateUi(MetadataEditor)

        QMetaObject.connectSlotsByName(MetadataEditor)
    # setupUi

    def retranslateUi(self, MetadataEditor):
        MetadataEditor.setWindowTitle(QCoreApplication.translate("MetadataEditor", u"Metadata Editor", None))
        self.titleLabel.setText(QCoreApplication.translate("MetadataEditor", u"Title:", None))
        self.titleEdit.setPlaceholderText(QCoreApplication.translate("MetadataEditor", u"Enter model title...", None))
        self.descriptionLabel.setText(QCoreApplication.translate("MetadataEditor", u"Description:", None))
        self.descriptionEdit.setPlaceholderText(QCoreApplication.translate("MetadataEditor", u"Describe your model...", None))
        self.authorLabel.setText(QCoreApplication.translate("MetadataEditor", u"Author:", None))
        self.authorEdit.setPlaceholderText(QCoreApplication.translate("MetadataEditor", u"Author name...", None))
        self.dateLabel.setText(QCoreApplication.translate("MetadataEditor", u"Date:", None))
        self.licenseLabel.setText(QCoreApplication.translate("MetadataEditor", u"License:", None))
        self.licenseEdit.setPlaceholderText(QCoreApplication.translate("MetadataEditor", u"e.g. MIT, Apache 2.0, Custom...", None))
        self.usageHintLabel.setText(QCoreApplication.translate("MetadataEditor", u"Usage Hint:", None))
        self.usageHintEdit.setPlaceholderText(QCoreApplication.translate("MetadataEditor", u"Usage instructions or hints...", None))
        self.tagsLabel.setText(QCoreApplication.translate("MetadataEditor", u"Tags:", None))
        self.tagsEdit.setPlaceholderText(QCoreApplication.translate("MetadataEditor", u"comma, separated, tags", None))
        self.mergedFromLabel.setText(QCoreApplication.translate("MetadataEditor", u"Merged From:", None))
        self.mergedFromEdit.setPlaceholderText(QCoreApplication.translate("MetadataEditor", u"Source models if merged...", None))
        self.thumbnailLabel.setText(QCoreApplication.translate("MetadataEditor", u"Thumbnail:", None))
        self.thumbnailDisplay.setText(QCoreApplication.translate("MetadataEditor", u"No thumbnail", None))
        self.setThumbnailBtn.setText(QCoreApplication.translate("MetadataEditor", u"Set", None))
        self.viewThumbnailBtn.setText(QCoreApplication.translate("MetadataEditor", u"View", None))
        self.clearThumbnailBtn.setText(QCoreApplication.translate("MetadataEditor", u"Clear", None))
        self.progressBar.setFormat(QCoreApplication.translate("MetadataEditor", u"Ready", None))
        self.statusLog.setPlaceholderText(QCoreApplication.translate("MetadataEditor", u"Status messages will appear here...", None))
    # retranslateUi

