from typing import Any

from PySide6.QtCore import QCoreApplication, QSize
from PySide6.QtWidgets import (
    QHBoxLayout,
    QProgressBar,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from .sections.general_section import build_general_section
from .sections.source_section import build_source_section
from .sections.thumbnail_section import build_thumbnail_section
from .sections.usage_section import build_usage_section


class Ui_EditorPanel(object):
    def __init__(self) -> None:
        self.title_label: Any = None
        self.title_edit: Any = None
        self.type_label: Any = None
        self.type_select: Any = None
        self.description_label: Any = None
        self.description_edit: Any = None
        self.tags_label: Any = None
        self.tags_edit: Any = None
        self.author_label: Any = None
        self.author_edit: Any = None
        self.date_label: Any = None
        self.date_time_edit: Any = None
        self.merged_from_label: Any = None
        self.merged_from_edit: Any = None
        self.usage_hint_label: Any = None
        self.usage_hint_edit: Any = None
        self.license_label: Any = None
        self.license_edit: Any = None
        self.thumbnail_group: Any = None
        self.thumbnail_display: Any = None
        self.set_thumbnail_btn: Any = None
        self.view_thumbnail_btn: Any = None
        self.clear_thumbnail_btn: Any = None
        self.general_section: Any = None
        self.source_section: Any = None
        self.usage_section: Any = None
        self.progress_bar: Any = None

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

        self.general_section = build_general_section(self, panel)
        self.general_section.expand(animate=False)
        left_column.addWidget(self.general_section)

        self.source_section = build_source_section(self, panel)
        self.source_section.expand(animate=False)
        left_column.addWidget(self.source_section)

        self.usage_section = build_usage_section(self, panel)
        self.usage_section.expand(animate=False)
        left_column.addWidget(self.usage_section)

        left_column.addItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        horizontal_layout.addLayout(left_column)

        # Right column
        thumbnail_column = build_thumbnail_section(self, panel)
        horizontal_layout.addLayout(thumbnail_column)

        # Set column stretches
        horizontal_layout.setStretch(0, 6)
        horizontal_layout.setStretch(1, 4)

        vertical_layout.addLayout(horizontal_layout)

        self.progress_bar = QProgressBar(panel)
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        vertical_layout.addWidget(self.progress_bar)

        self.retranslate_ui(panel)

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
        self.general_section.setText(
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
        self.source_section.setText(
            QCoreApplication.translate("EditorPanel", "Source", None)
        )
        self.usage_section.setText(
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
