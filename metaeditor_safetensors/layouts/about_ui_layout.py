from PySide6.QtCore import (
    QCoreApplication,
    QMetaObject,
    QRect,
    QSize,
    Qt,
)
from PySide6.QtGui import (
    QIcon,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from metaeditor_safetensors.widgets.clickable_image import ClickableImage
from metaeditor_safetensors.widgets.svg_widget import SvgWidget


def create_size_policy_for_widget(
    widget, horizontal_policy, vertical_policy, horizontal_stretch=0, vertical_stretch=0
):
    size_policy = QSizePolicy(horizontal_policy, vertical_policy)
    size_policy.setHorizontalStretch(horizontal_stretch)
    size_policy.setVerticalStretch(vertical_stretch)
    size_policy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
    widget.setSizePolicy(size_policy)
    return size_policy


class Ui_AboutDialog(object):
    def setup_ui(self, dialog):
        if not dialog.objectName():
            dialog.setObjectName("AboutDialog")
        dialog.resize(690, 425)
        dialog.setModal(True)

        # Main vertical layout
        vertical_layout = QVBoxLayout(dialog)
        vertical_layout.setSpacing(12)
        vertical_layout.setContentsMargins(15, 15, 15, 15)

        # Create tab widget
        self.tab_widget = QTabWidget(dialog)
        self.tab_widget.setObjectName("tabWidget")
        self.tab_widget.setAutoFillBackground(True)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.South)
        self.tab_widget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tab_widget.setDocumentMode(True)

        vertical_layout.addWidget(self.tab_widget)

        # Create tabs
        self.about_tab = self.create_about_tab()
        self.tab_widget.addTab(self.about_tab, "")

        self.credits_tab = self.create_credits_tab()
        self.tab_widget.addTab(self.credits_tab, "")

        self.license_tab = self.create_license_tab()
        self.tab_widget.addTab(self.license_tab, "")

        self.tab_widget.setCurrentIndex(0)
        self.tab_widget.tabBar().setExpanding(True)
        self.retranslate_ui()
        QMetaObject.connectSlotsByName(dialog)

    def create_about_tab(self):
        about_tab = QWidget()
        about_tab.setObjectName("aboutTab")

        horizontal_layout = QHBoxLayout(about_tab)
        horizontal_layout.setSpacing(0)

        # Setup logo
        logo = SvgWidget(about_tab)
        logo.setObjectName("aboutLogo")
        create_size_policy_for_widget(
            logo,
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred,
        )
        logo.setMinimumSize(QSize(250, 250))
        logo.setMaximumSize(QSize(250, 250))
        logo.loadSvg(":/assets/logo.svg")
        horizontal_layout.addWidget(logo)

        vertical_layout = QVBoxLayout()
        vertical_layout.setSpacing(6)

        # Title
        self.about_title = QLabel(about_tab)
        self.about_title.setObjectName("aboutTitle")
        self.about_title.setProperty("class", "title")
        vertical_layout.addWidget(self.about_title)

        # Version
        version_layout = QHBoxLayout()
        version_layout.setSpacing(6)
        self.about_version = QLabel(about_tab)
        self.about_version.setObjectName("aboutVersion")
        self.about_version.setProperty("class", "description")
        create_size_policy_for_widget(
            self.about_version, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        version_layout.addWidget(self.about_version, 0, Qt.AlignmentFlag.AlignLeft)

        # Copy button
        self.copy_version_btn = QPushButton(about_tab)
        self.copy_version_btn.setObjectName("copyVersionBtn")
        create_size_policy_for_widget(
            self.copy_version_btn, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.copy_version_btn.setMinimumSize(QSize(24, 24))
        self.copy_version_btn.setMaximumSize(QSize(24, 24))
        self.copy_version_btn.setIcon(QIcon(QIcon.fromTheme(QIcon.ThemeIcon.EditCopy)))
        self.copy_version_btn.setIconSize(QSize(16, 16))
        self.copy_version_btn.setProperty("class", "icon-small")

        version_layout.addWidget(
            self.copy_version_btn,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )

        version_layout.addItem(
            QSpacerItem(
                40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
            )
        )
        vertical_layout.addLayout(version_layout)

        # Author
        self.about_author = QLabel(about_tab)
        self.about_author.setObjectName("aboutAuthor")
        self.about_author.setProperty("class", "note")
        vertical_layout.addWidget(self.about_author)

        vertical_layout.addItem(
            QSpacerItem(
                20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        # Description
        self.about_description = QLabel(about_tab)
        self.about_description.setObjectName("aboutDescription")
        self.about_description.setWordWrap(True)
        self.about_description.setOpenExternalLinks(True)
        vertical_layout.addWidget(self.about_description)

        vertical_layout.addItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred
            )
        )

        # Links
        links_layout = QHBoxLayout()
        links_layout.setSpacing(10)
        self.kofi_link = ClickableImage(about_tab)
        self.kofi_link.setObjectName("kofiLink")
        self.kofi_link.setMaximumSize(QSize(100, 56))
        self.kofi_link.setFrameShadow(QFrame.Shadow.Sunken)
        self.kofi_link.setPixmap(QPixmap(":/assets/support_me.png"))
        self.kofi_link.setScaledContents(True)
        self.kofi_link.setProperty("class", "clickable-image")
        links_layout.addWidget(self.kofi_link)

        self.github_link = ClickableImage(about_tab)
        self.github_link.setObjectName("githubLink")
        self.github_link.setMaximumSize(QSize(163, 40))
        self.github_link.setPixmap(QPixmap(":/assets/GitHub_Lockup_Dark.png"))
        self.github_link.setScaledContents(True)
        self.github_link.setProperty("class", "clickable-image")
        links_layout.addWidget(self.github_link)

        vertical_layout.addLayout(links_layout)

        vertical_layout.addItem(
            QSpacerItem(
                20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        horizontal_layout.addLayout(vertical_layout)
        horizontal_layout.setStretch(1, 1)
        return about_tab

    def create_credits_tab(self):
        credits_tab = QWidget()
        credits_tab.setObjectName("creditsTab")

        horizontal_layout = QHBoxLayout(credits_tab)
        horizontal_layout.setSpacing(0)

        # Setup logo
        logo = SvgWidget(credits_tab)
        logo.setObjectName("creditsLogo")
        create_size_policy_for_widget(
            logo, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        logo.setMinimumSize(QSize(250, 250))
        logo.setMaximumSize(QSize(250, 250))
        logo.loadSvg(":/assets/logo.svg")
        horizontal_layout.addWidget(logo)

        vertical_layout = QVBoxLayout()
        vertical_layout.setSpacing(6)

        # Title
        self.credits_title = QLabel(credits_tab)
        self.credits_title.setObjectName("creditsTitle")
        self.credits_title.setProperty("class", "title")
        vertical_layout.addWidget(self.credits_title)

        # Credits
        self.credits_text = QLabel(credits_tab)
        self.credits_text.setObjectName("creditsText")
        self.credits_text.setWordWrap(True)
        self.credits_text.setOpenExternalLinks(True)
        vertical_layout.addWidget(self.credits_text)

        vertical_layout.addItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        horizontal_layout.addLayout(vertical_layout)
        horizontal_layout.setStretch(1, 1)
        return credits_tab

    def create_license_tab(self):
        license_tab = QWidget()
        license_tab.setObjectName("licenseTab")

        horizontal_layout = QHBoxLayout(license_tab)
        horizontal_layout.setSpacing(0)

        # Setup logo
        logo = SvgWidget(license_tab)
        logo.setObjectName("licenseLogo")
        create_size_policy_for_widget(
            logo, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        logo.setMinimumSize(QSize(250, 250))
        logo.setMaximumSize(QSize(250, 250))
        logo.loadSvg(":/assets/logo.svg")
        horizontal_layout.addWidget(logo)

        vertical_layout = QVBoxLayout()
        vertical_layout.setSpacing(6)

        # Title
        self.license_title = QLabel(license_tab)
        self.license_title.setObjectName("licenseTitle")
        self.license_title.setProperty("class", "title")
        vertical_layout.addWidget(self.license_title)

        # License Text
        scroll_area = QScrollArea(license_tab)
        scroll_area.setObjectName("licenseScrollArea")
        create_size_policy_for_widget(
            scroll_area, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        scroll_area.setWidgetResizable(True)

        contents = QWidget()
        contents.setObjectName("licenseScrollContents")
        contents.setGeometry(QRect(0, 0, 132, 1046))

        vertical_contents_layout = QVBoxLayout(contents)
        self.license_text = QLabel(contents)
        self.license_text.setObjectName("licenseText")
        self.license_text.setWordWrap(True)
        vertical_contents_layout.addWidget(self.license_text)
        contents.setLayout(vertical_contents_layout)

        scroll_area.setWidget(contents)
        vertical_layout.addWidget(scroll_area)

        horizontal_layout.addLayout(vertical_layout)
        horizontal_layout.setStretch(1, 1)
        return license_tab

    def retranslate_ui(self):
        # About tab
        self.about_title.setText(
            QCoreApplication.translate(
                "AboutDialog", "Safetensors Metadata Editor", None
            )
        )
        self.about_version.setText(
            QCoreApplication.translate("AboutDialog", "v1.0.0", None)
        )
        # if QT_CONFIG(tooltip)
        self.copy_version_btn.setToolTip(
            QCoreApplication.translate(
                "AboutDialog", "Copy version to clipboard.", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.copy_version_btn.setText("")
        self.about_author.setText(
            QCoreApplication.translate("AboutDialog", "Created by: KPandaK", None)
        )
        self.about_description.setText(
            QCoreApplication.translate(
                "AboutDialog",
                '<html><head/><body><p>This is a free and open source app for viewing and editing metadata in safetensors model files. </p><p>It implements v1.01 of Stability.AI\'s model metadata standard <a href="https://github.com/Stability-AI/ModelSpec"><span style=" text-decoration: underline; color:#92ebff;">specification</span></a>.</p><p>If you enjoy this app, feel free to tip me for a coffee!</p></body></html>',
                None,
            )
        )
        self.kofi_link.setText("")
        self.github_link.setText("")
        self.tab_widget.setTabText(
            self.tab_widget.indexOf(self.about_tab),
            QCoreApplication.translate("AboutDialog", "About", None),
        )

        # Credits tab
        self.credits_title.setText(
            QCoreApplication.translate("AboutDialog", "Credits", None)
        )
        self.credits_text.setText(
            QCoreApplication.translate(
                "AboutDialog",
                '<html><head/><body><p>Original Safetensors Icon by <a href="https://github.com/SHADOW-LIGHTS"><span style=" text-decoration: underline; color:#92ebff;">SHADOW-LIGHTS</span></a></p></body></html>',
                None,
            )
        )
        self.tab_widget.setTabText(
            self.tab_widget.indexOf(self.credits_tab),
            QCoreApplication.translate("AboutDialog", "Credits", None),
        )

        # License tab
        self.license_title.setText(
            QCoreApplication.translate("AboutDialog", "The MIT License (MIT)", None)
        )
        self.license_text.setText(
            QCoreApplication.translate(
                "AboutDialog",
                "<html><head/><body><p>Copyright \u00a9 2025 KPandaK</p><p>Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \u201cSoftware\u201d), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:</p><p>The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.</p><p>THE SOFTWARE IS PROVIDED \u201cAS IS\u201d, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OU"
                "T OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</p></body></html>",
                None,
            )
        )
        self.tab_widget.setTabText(
            self.tab_widget.indexOf(self.license_tab),
            QCoreApplication.translate("AboutDialog", "License", None),
        )
