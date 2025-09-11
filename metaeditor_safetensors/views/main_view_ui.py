# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_view.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QDateTimeEdit, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QTextEdit,
    QVBoxLayout, QWidget)

from metaeditor_safetensors.widgets.image_widget import ImageWidget
from . import resources_rc

class Ui_EditorPanel(object):
    def setupUi(self, EditorPanel):
        if not EditorPanel.objectName():
            EditorPanel.setObjectName(u"EditorPanel")
        EditorPanel.resize(1100, 900)
        self.verticalLayout = QVBoxLayout(EditorPanel)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(15, 15, 15, 15)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.leftColumn = QVBoxLayout()
        self.leftColumn.setObjectName(u"leftColumn")
        self.generalBox = QGroupBox(EditorPanel)
        self.generalBox.setObjectName(u"generalBox")
        self.verticalLayout_2 = QVBoxLayout(self.generalBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.titleGroup = QVBoxLayout()
        self.titleGroup.setObjectName(u"titleGroup")
        self.titleLabel = QLabel(self.generalBox)
        self.titleLabel.setObjectName(u"titleLabel")

        self.titleGroup.addWidget(self.titleLabel)

        self.titleEdit = QLineEdit(self.generalBox)
        self.titleEdit.setObjectName(u"titleEdit")

        self.titleGroup.addWidget(self.titleEdit)


        self.verticalLayout_2.addLayout(self.titleGroup)

        self.descGroup = QVBoxLayout()
        self.descGroup.setSpacing(6)
        self.descGroup.setObjectName(u"descGroup")
        self.descriptionLabel = QLabel(self.generalBox)
        self.descriptionLabel.setObjectName(u"descriptionLabel")

        self.descGroup.addWidget(self.descriptionLabel)

        self.descriptionEdit = QTextEdit(self.generalBox)
        self.descriptionEdit.setObjectName(u"descriptionEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.descriptionEdit.sizePolicy().hasHeightForWidth())
        self.descriptionEdit.setSizePolicy(sizePolicy)
        self.descriptionEdit.setMinimumSize(QSize(0, 300))
        self.descriptionEdit.setMaximumSize(QSize(16777215, 16777215))

        self.descGroup.addWidget(self.descriptionEdit)

        self.descGroup.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.descGroup)

        self.tagGroup = QVBoxLayout()
        self.tagGroup.setObjectName(u"tagGroup")
        self.tagsLabel = QLabel(self.generalBox)
        self.tagsLabel.setObjectName(u"tagsLabel")

        self.tagGroup.addWidget(self.tagsLabel)

        self.tagsEdit = QLineEdit(self.generalBox)
        self.tagsEdit.setObjectName(u"tagsEdit")

        self.tagGroup.addWidget(self.tagsEdit)


        self.verticalLayout_2.addLayout(self.tagGroup)


        self.leftColumn.addWidget(self.generalBox)

        self.sourceBox = QGroupBox(EditorPanel)
        self.sourceBox.setObjectName(u"sourceBox")
        self.verticalLayout_3 = QVBoxLayout(self.sourceBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.authorDateLayout = QHBoxLayout()
        self.authorDateLayout.setObjectName(u"authorDateLayout")
        self.authorLayout = QVBoxLayout()
        self.authorLayout.setObjectName(u"authorLayout")
        self.authorLabel = QLabel(self.sourceBox)
        self.authorLabel.setObjectName(u"authorLabel")

        self.authorLayout.addWidget(self.authorLabel)

        self.authorEdit = QLineEdit(self.sourceBox)
        self.authorEdit.setObjectName(u"authorEdit")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.authorEdit.sizePolicy().hasHeightForWidth())
        self.authorEdit.setSizePolicy(sizePolicy1)

        self.authorLayout.addWidget(self.authorEdit)


        self.authorDateLayout.addLayout(self.authorLayout)

        self.dateLayout = QVBoxLayout()
        self.dateLayout.setObjectName(u"dateLayout")
        self.dateLabel = QLabel(self.sourceBox)
        self.dateLabel.setObjectName(u"dateLabel")
        self.dateLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.dateLayout.addWidget(self.dateLabel)

        self.dateTimeEdit = QDateTimeEdit(self.sourceBox)
        self.dateTimeEdit.setObjectName(u"dateTimeEdit")
        self.dateTimeEdit.setMinimumSize(QSize(140, 22))
        self.dateTimeEdit.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.dateTimeEdit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.dateTimeEdit.setCalendarPopup(True)

        self.dateLayout.addWidget(self.dateTimeEdit)


        self.authorDateLayout.addLayout(self.dateLayout)


        self.verticalLayout_3.addLayout(self.authorDateLayout)

        self.mergeGroup = QVBoxLayout()
        self.mergeGroup.setObjectName(u"mergeGroup")
        self.mergedFromLabel = QLabel(self.sourceBox)
        self.mergedFromLabel.setObjectName(u"mergedFromLabel")

        self.mergeGroup.addWidget(self.mergedFromLabel)

        self.mergedFromEdit = QLineEdit(self.sourceBox)
        self.mergedFromEdit.setObjectName(u"mergedFromEdit")

        self.mergeGroup.addWidget(self.mergedFromEdit)


        self.verticalLayout_3.addLayout(self.mergeGroup)


        self.leftColumn.addWidget(self.sourceBox)

        self.usageBox = QGroupBox(EditorPanel)
        self.usageBox.setObjectName(u"usageBox")
        self.verticalLayout_4 = QVBoxLayout(self.usageBox)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.usageGroup = QVBoxLayout()
        self.usageGroup.setObjectName(u"usageGroup")
        self.usageHintLabel = QLabel(self.usageBox)
        self.usageHintLabel.setObjectName(u"usageHintLabel")

        self.usageGroup.addWidget(self.usageHintLabel)

        self.usageHintEdit = QTextEdit(self.usageBox)
        self.usageHintEdit.setObjectName(u"usageHintEdit")
        self.usageHintEdit.setMaximumSize(QSize(16777215, 100))

        self.usageGroup.addWidget(self.usageHintEdit)


        self.verticalLayout_4.addLayout(self.usageGroup)

        self.licenseGroup = QVBoxLayout()
        self.licenseGroup.setObjectName(u"licenseGroup")
        self.licenseLabel = QLabel(self.usageBox)
        self.licenseLabel.setObjectName(u"licenseLabel")

        self.licenseGroup.addWidget(self.licenseLabel)

        self.licenseEdit = QLineEdit(self.usageBox)
        self.licenseEdit.setObjectName(u"licenseEdit")

        self.licenseGroup.addWidget(self.licenseEdit)


        self.verticalLayout_4.addLayout(self.licenseGroup)


        self.leftColumn.addWidget(self.usageBox)

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
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(1)
        sizePolicy2.setHeightForWidth(self.thumbnailDisplay.sizePolicy().hasHeightForWidth())
        self.thumbnailDisplay.setSizePolicy(sizePolicy2)

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
        self.generalBox.setTitle(QCoreApplication.translate("EditorPanel", u"General", None))
        self.titleLabel.setText(QCoreApplication.translate("EditorPanel", u"Title:", None))
        self.titleEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Enter model title...", None))
        self.descriptionLabel.setText(QCoreApplication.translate("EditorPanel", u"Description:", None))
        self.descriptionEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Describe your model...", None))
        self.tagsLabel.setText(QCoreApplication.translate("EditorPanel", u"Tags:", None))
        self.tagsEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"comma, separated, tags", None))
        self.sourceBox.setTitle(QCoreApplication.translate("EditorPanel", u"Source", None))
        self.authorLabel.setText(QCoreApplication.translate("EditorPanel", u"Author:", None))
        self.authorEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Author name...", None))
        self.dateLabel.setText(QCoreApplication.translate("EditorPanel", u"Date:", None))
        self.dateTimeEdit.setDisplayFormat(QCoreApplication.translate("EditorPanel", u"MM/dd/yyyy h:mm AP", None))
        self.mergedFromLabel.setText(QCoreApplication.translate("EditorPanel", u"Merged From:", None))
        self.mergedFromEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Source models if merged...", None))
        self.usageBox.setTitle(QCoreApplication.translate("EditorPanel", u"Usage", None))
        self.usageHintLabel.setText(QCoreApplication.translate("EditorPanel", u"Usage Hint:", None))
        self.usageHintEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"Usage instructions or hints...", None))
        self.licenseLabel.setText(QCoreApplication.translate("EditorPanel", u"License:", None))
        self.licenseEdit.setPlaceholderText(QCoreApplication.translate("EditorPanel", u"e.g. MIT, Apache 2.0, Custom...", None))
        self.thumbnailLabel.setText(QCoreApplication.translate("EditorPanel", u"Thumbnail:", None))
        self.setThumbnailBtn.setText(QCoreApplication.translate("EditorPanel", u"Set", None))
        self.viewThumbnailBtn.setText(QCoreApplication.translate("EditorPanel", u"View", None))
        self.clearThumbnailBtn.setText(QCoreApplication.translate("EditorPanel", u"Clear", None))
    # retranslateUi

