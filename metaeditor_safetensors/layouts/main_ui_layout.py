from PySide6.QtCore import (
    QCoreApplication,
    QSize,
)
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDateTimeEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
)

from metaeditor_safetensors.widgets.collapsible_section import CollapsibleSection
from metaeditor_safetensors.widgets.image_widget import ImageWidget

from ..services.widget_binding_service import (
    FieldBinding,
    WidgetBindingService,
    data_uri_to_pixmap,
    datetime_to_iso_string,
    iso_string_to_datetime,
    model_type_to_string,
    pixmap_to_data_uri,
    string_to_model_type,
    string_to_tags,
    tags_to_string,
)


def create_size_policy_for_widget(
    widget, horizontal_policy, vertical_policy, horizontal_stretch=0, vertical_stretch=0
):
    size_policy = QSizePolicy(horizontal_policy, vertical_policy)
    size_policy.setHorizontalStretch(horizontal_stretch)
    size_policy.setVerticalStretch(vertical_stretch)
    size_policy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
    widget.setSizePolicy(size_policy)
    return size_policy


class Ui_EditorPanel(object):
    def setup_ui(self, panel):
        if not panel.objectName():
            panel.setObjectName("EditorPanel")
        panel.resize(1100, 900)

        # Main vertical layout
        vertical_layout = QVBoxLayout(panel)
        vertical_layout.setContentsMargins(15, 15, 15, 15)

        # Horizontal layout for the main content
        horizontal_layout = QHBoxLayout()

        # Left column
        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 8, 0, 0)

        self.general_section = self._create_general_section(panel)
        self.general_section.setExpanded(True)
        left_column.addWidget(self.general_section)

        self.source_section = self._create_source_section(panel)
        self.source_section.setExpanded(True)
        left_column.addWidget(self.source_section)

        self.usage_section = self._create_usage_section(panel)
        self.usage_section.setExpanded(True)
        left_column.addWidget(self.usage_section)

        left_column.addItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        horizontal_layout.addLayout(left_column)

        # Right column
        thumbnail_column = self._create_thumbnail(panel)
        horizontal_layout.addLayout(thumbnail_column)

        # Set column stretches
        horizontal_layout.setStretch(0, 6)
        horizontal_layout.setStretch(1, 4)

        vertical_layout.addLayout(horizontal_layout)

        self.progress_bar = QProgressBar(panel)
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setMaximumSize(QSize(16777215, 6))
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        vertical_layout.addWidget(self.progress_bar)

        self.retranslate_ui(panel)

        self._setup_bindings()

    def _create_general_section(self, parent):
        section = CollapsibleSection(parent)
        section.setMinimumSize(QSize(0, 0))

        # Title & Type layout
        title_type_layout = QHBoxLayout()

        # Title
        title_layout = QVBoxLayout()
        self.title_label = QLabel(section)
        self.title_label.setObjectName("titleLabel")
        title_layout.addWidget(self.title_label)

        self.title_edit = QLineEdit(section)
        self.title_edit.setObjectName("titleEdit")
        title_layout.addWidget(self.title_edit)

        title_type_layout.addLayout(title_layout)

        # Type
        type_layout = QVBoxLayout()
        self.type_label = QLabel(section)
        self.type_label.setObjectName("typeLabel")
        type_layout.addWidget(self.type_label)

        self.type_select = QComboBox(section)
        self.type_select.setObjectName("typeSelect")
        type_layout.addWidget(self.type_select)

        title_type_layout.addLayout(type_layout)
        section.add_layout(title_type_layout)

        # Description
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(6)
        self.description_label = QLabel(section)
        self.description_label.setObjectName("descriptionLabel")
        desc_layout.addWidget(self.description_label)

        self.description_edit = QTextEdit(section)
        self.description_edit.setObjectName("descriptionEdit")
        create_size_policy_for_widget(
            self.description_edit,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.description_edit.setMinimumSize(QSize(0, 300))
        desc_layout.addWidget(self.description_edit)
        desc_layout.setStretch(1, 1)

        section.add_layout(desc_layout)

        # Tags
        tag_layout = QVBoxLayout()
        self.tags_label = QLabel(section)
        self.tags_label.setObjectName("tagsLabel")
        tag_layout.addWidget(self.tags_label)

        self.tags_edit = QLineEdit(section)
        self.tags_edit.setObjectName("tagsEdit")
        tag_layout.addWidget(self.tags_edit)
        section.add_layout(tag_layout)

        return section

    def _create_source_section(self, parent):
        section = CollapsibleSection(parent)
        section.setMinimumSize(QSize(0, 0))

        author_date_layout = QHBoxLayout()

        # Author
        author_layout = QVBoxLayout()
        self.author_label = QLabel(section)
        self.author_label.setObjectName("authorLabel")
        author_layout.addWidget(self.author_label)

        self.author_edit = QLineEdit(section)
        self.author_edit.setObjectName("authorEdit")
        create_size_policy_for_widget(
            self.author_edit, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        author_layout.addWidget(self.author_edit)

        author_date_layout.addLayout(author_layout)

        # Date
        date_layout = QVBoxLayout()
        self.date_label = QLabel(section)
        self.date_label.setObjectName("dateLabel")
        date_layout.addWidget(self.date_label)

        self.date_time_edit = QDateTimeEdit(section)
        self.date_time_edit.setObjectName("dateTimeEdit")
        self.date_time_edit.setMinimumSize(QSize(140, 22))

        self.date_time_edit.setButtonSymbols(
            QAbstractSpinBox.ButtonSymbols.UpDownArrows
        )
        self.date_time_edit.setCalendarPopup(True)
        date_layout.addWidget(self.date_time_edit)

        author_date_layout.addLayout(date_layout)

        section.add_layout(author_date_layout)

        # Merged From
        merged_layout = QVBoxLayout()
        self.merged_from_label = QLabel(section)
        self.merged_from_label.setObjectName("mergedFromLabel")
        merged_layout.addWidget(self.merged_from_label)

        self.merged_from_edit = QLineEdit(section)
        self.merged_from_edit.setObjectName("mergedFromEdit")
        merged_layout.addWidget(self.merged_from_edit)

        section.add_layout(merged_layout)

        return section

    def _create_usage_section(self, parent):
        section = CollapsibleSection(parent)
        section.setMinimumSize(QSize(0, 0))

        # Usage Hint
        usage_hint_layout = QVBoxLayout()
        self.usage_hint_label = QLabel(section)
        self.usage_hint_label.setObjectName("usageHintLabel")
        usage_hint_layout.addWidget(self.usage_hint_label)

        self.usage_hint_edit = QTextEdit(section)
        self.usage_hint_edit.setObjectName("usageHintEdit")
        self.usage_hint_edit.setMaximumSize(QSize(16777215, 100))
        usage_hint_layout.addWidget(self.usage_hint_edit)

        section.add_layout(usage_hint_layout)

        # License
        license_layout = QVBoxLayout()
        self.license_label = QLabel(section)
        self.license_label.setObjectName("licenseLabel")
        license_layout.addWidget(self.license_label)

        self.license_edit = QLineEdit(section)
        self.license_edit.setObjectName("licenseEdit")
        license_layout.addWidget(self.license_edit)

        section.add_layout(license_layout)

        return section

    def _create_thumbnail(self, parent):
        layout = QVBoxLayout()
        layout.setObjectName("thumbnailLayout")

        # Thumbnail group box
        self.thumbnail_group = QGroupBox()
        self.thumbnail_group.setObjectName("thumbnailGroup")
        create_size_policy_for_widget(
            self.thumbnail_group,
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred,
        )

        group_layout = QVBoxLayout(self.thumbnail_group)
        group_layout.setSpacing(6)

        # Thumbnail display widget
        self.thumbnail_display = ImageWidget(parent)
        self.thumbnail_display.setObjectName("thumbnailDisplay")
        self.thumbnail_display.setPrimaryDimension("width")
        create_size_policy_for_widget(
            self.thumbnail_display,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
            vertical_stretch=1,
        )
        group_layout.addWidget(self.thumbnail_display)

        # Thumbnail buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setObjectName("thumbnailButtonsLayout")

        self.set_thumbnail_btn = QPushButton(self.thumbnail_group)
        self.set_thumbnail_btn.setObjectName("setThumbnailBtn")
        self.set_thumbnail_btn.setMaximumSize(QSize(16777215, 24))
        buttons_layout.addWidget(self.set_thumbnail_btn)

        self.view_thumbnail_btn = QPushButton(self.thumbnail_group)
        self.view_thumbnail_btn.setObjectName("viewThumbnailBtn")
        self.view_thumbnail_btn.setMaximumSize(QSize(16777215, 24))
        buttons_layout.addWidget(self.view_thumbnail_btn)

        self.clear_thumbnail_btn = QPushButton(self.thumbnail_group)
        self.clear_thumbnail_btn.setObjectName("clearThumbnailBtn")
        self.clear_thumbnail_btn.setMaximumSize(QSize(16777215, 24))
        buttons_layout.addWidget(self.clear_thumbnail_btn)

        group_layout.addLayout(buttons_layout)

        # Set stretch so thumbnail display takes most space
        group_layout.setStretch(0, 1)

        layout.addWidget(self.thumbnail_group)

        layout.addItem(
            QSpacerItem(
                20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        return layout

    def retranslate_ui(self, panel):
        panel.setWindowTitle(
            QCoreApplication.translate("EditorPanel", "Metadata Editor", None)
        )
        self.title_label.setText(
            QCoreApplication.translate("EditorPanel", "Title:", None)
        )
        self.title_edit.setPlaceholderText(
            QCoreApplication.translate("EditorPanel", "Name of the model.", None)
        )
        self.type_label.setText(
            QCoreApplication.translate("EditorPanel", "Model Type:", None)
        )
        self.description_label.setText(
            QCoreApplication.translate("EditorPanel", "Description:", None)
        )
        self.description_edit.setPlaceholderText(
            QCoreApplication.translate(
                "EditorPanel",
                "Describe the model's purpose, training data, and capabilities.",
                None,
            )
        )
        self.tags_label.setText(
            QCoreApplication.translate("EditorPanel", "Tags:", None)
        )
        self.tags_edit.setPlaceholderText(
            QCoreApplication.translate("EditorPanel", "comma, separated, tags", None)
        )
        self.general_section.setTitle(
            QCoreApplication.translate("EditorPanel", "General", None)
        )
        self.author_label.setText(
            QCoreApplication.translate("EditorPanel", "Author:", None)
        )
        self.author_edit.setPlaceholderText(
            QCoreApplication.translate(
                "EditorPanel", "Author name or organization.", None
            )
        )
        self.date_label.setText(
            QCoreApplication.translate("EditorPanel", "Date:", None)
        )
        self.date_time_edit.setDisplayFormat(
            QCoreApplication.translate("EditorPanel", "MM/dd/yyyy h:mm AP", None)
        )
        self.merged_from_label.setText(
            QCoreApplication.translate("EditorPanel", "Merged From:", None)
        )
        self.merged_from_edit.setPlaceholderText(
            QCoreApplication.translate(
                "EditorPanel", "Source models, if merged from other models.", None
            )
        )
        self.source_section.setTitle(
            QCoreApplication.translate("EditorPanel", "Source", None)
        )
        self.usage_section.setTitle(
            QCoreApplication.translate("EditorPanel", "Usage", None)
        )
        self.usage_hint_label.setText(
            QCoreApplication.translate("EditorPanel", "Usage Hint:", None)
        )
        self.usage_hint_edit.setPlaceholderText(
            QCoreApplication.translate(
                "EditorPanel", "Usage instructions or tips for using the model.", None
            )
        )
        self.license_label.setText(
            QCoreApplication.translate("EditorPanel", "License:", None)
        )
        self.license_edit.setPlaceholderText(
            QCoreApplication.translate(
                "EditorPanel", "License type (e.g., MIT, Apache-2.0, CC-BY-4.0).", None
            )
        )
        self.thumbnail_group.setTitle(
            QCoreApplication.translate("EditorPanel", "Thumbnail", None)
        )
        self.set_thumbnail_btn.setText(
            QCoreApplication.translate("EditorPanel", "Set", None)
        )
        self.view_thumbnail_btn.setText(
            QCoreApplication.translate("EditorPanel", "View", None)
        )
        self.clear_thumbnail_btn.setText(
            QCoreApplication.translate("EditorPanel", "Clear", None)
        )

    def _setup_bindings(self):
        binding_service = WidgetBindingService()

        binding_service.add_binding(
            FieldBinding(
                "modelspec.title",
                self.title_edit,
                "text",
                "setText",
                "textChanged",
            )
        )

        binding_service.add_binding(
            FieldBinding(
                "metaeditor.model_type_override",
                self.type_select,
                "currentText",
                "setCurrentText",
                "currentTextChanged",
                to_metadata_converter=string_to_model_type,
                from_metadata_converter=model_type_to_string,
            )
        )

        binding_service.add_binding(
            FieldBinding(
                "modelspec.description",
                self.description_edit,
                "toPlainText",
                "setPlainText",
                "textChanged",
            )
        )

        binding_service.add_binding(
            FieldBinding(
                "modelspec.tags",
                self.tags_edit,
                "text",
                "setText",
                "textChanged",
                to_metadata_converter=string_to_tags,
                from_metadata_converter=tags_to_string,
            )
        )

        binding_service.add_binding(
            FieldBinding(
                "modelspec.author",
                self.author_edit,
                "text",
                "setText",
                "textChanged",
            )
        )

        binding_service.add_binding(
            FieldBinding(
                "modelspec.date",
                self.date_time_edit,
                "dateTime",
                "setDateTime",
                "dateTimeChanged",
                to_metadata_converter=datetime_to_iso_string,
                from_metadata_converter=iso_string_to_datetime,
            )
        )

        binding_service.add_binding(
            FieldBinding(
                "modelspec.merged_from",
                self.merged_from_edit,
                "text",
                "setText",
                "textChanged",
            )
        )

        binding_service.add_binding(
            FieldBinding(
                "modelspec.usage_hint",
                self.usage_hint_edit,
                "toPlainText",
                "setPlainText",
                "textChanged",
            )
        )

        binding_service.add_binding(
            FieldBinding(
                "modelspec.license",
                self.license_edit,
                "text",
                "setText",
                "textChanged",
            )
        )

        binding_service.add_binding(
            FieldBinding(
                "modelspec.thumbnail",
                self.thumbnail_display,
                "pixmap",
                "setPixmap",
                "pixmapChanged",
                to_metadata_converter=pixmap_to_data_uri,
                from_metadata_converter=data_uri_to_pixmap,
            )
        )
