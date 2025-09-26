from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
)

from ...widgets.collapsible_section import CollapsibleSection
from ..layout_utils import create_size_policy


def build_general_section(ui, parent) -> CollapsibleSection:
    section = CollapsibleSection(parent)
    section.setMinimumSize(QSize(0, 0))

    title_type_layout = QHBoxLayout()

    title_layout = QVBoxLayout()
    ui.title_label = QLabel(section)
    ui.title_label.setObjectName("titleLabel")
    title_layout.addWidget(ui.title_label)

    ui.title_edit = QLineEdit(section)
    ui.title_edit.setObjectName("titleEdit")
    title_layout.addWidget(ui.title_edit)
    title_type_layout.addLayout(title_layout)

    type_layout = QVBoxLayout()
    ui.type_label = QLabel(section)
    ui.type_label.setObjectName("typeLabel")
    type_layout.addWidget(ui.type_label)

    ui.type_select = QComboBox(section)
    ui.type_select.setObjectName("typeSelect")
    type_layout.addWidget(ui.type_select)
    title_type_layout.addLayout(type_layout)

    section.add_layout(title_type_layout)

    desc_layout = QVBoxLayout()
    desc_layout.setSpacing(6)
    ui.description_label = QLabel(section)
    ui.description_label.setObjectName("descriptionLabel")
    desc_layout.addWidget(ui.description_label)

    ui.description_edit = QTextEdit(section)
    ui.description_edit.setObjectName("descriptionEdit")
    create_size_policy(
        ui.description_edit,
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    ui.description_edit.setMinimumSize(QSize(0, 300))
    desc_layout.addWidget(ui.description_edit)
    desc_layout.setStretch(1, 1)
    section.add_layout(desc_layout)

    tag_layout = QVBoxLayout()
    ui.tags_label = QLabel(section)
    ui.tags_label.setObjectName("tagsLabel")
    tag_layout.addWidget(ui.tags_label)

    ui.tags_edit = QLineEdit(section)
    ui.tags_edit.setObjectName("tagsEdit")
    tag_layout.addWidget(ui.tags_edit)
    section.add_layout(tag_layout)

    return section
