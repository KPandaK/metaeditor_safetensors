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
    QWidget,
)
from superqt.collapsible import QCollapsible

from ..layout_utils import create_size_policy


def build_general_section(ui, parent) -> QCollapsible:
    section = QCollapsible(parent)

    layout = section.layout()
    if layout is not None:
        layout.setSpacing(0)

    content_widget = QWidget(section)
    content_layout = QVBoxLayout(content_widget)

    title_type_layout = QHBoxLayout()

    title_layout = QVBoxLayout()
    ui.title_label = QLabel(content_widget)
    ui.title_label.setObjectName("titleLabel")
    title_layout.addWidget(ui.title_label)

    ui.title_edit = QLineEdit(content_widget)
    ui.title_edit.setObjectName("titleEdit")
    title_layout.addWidget(ui.title_edit)
    title_type_layout.addLayout(title_layout)

    type_layout = QVBoxLayout()
    ui.type_label = QLabel(content_widget)
    ui.type_label.setObjectName("typeLabel")
    type_layout.addWidget(ui.type_label)

    ui.type_select = QComboBox(content_widget)
    ui.type_select.setObjectName("typeSelect")
    type_layout.addWidget(ui.type_select)
    title_type_layout.addLayout(type_layout)

    content_layout.addLayout(title_type_layout)

    desc_layout = QVBoxLayout()
    desc_layout.setSpacing(6)
    ui.description_label = QLabel(content_widget)
    ui.description_label.setObjectName("descriptionLabel")
    desc_layout.addWidget(ui.description_label)

    ui.description_edit = QTextEdit(content_widget)
    ui.description_edit.setObjectName("descriptionEdit")
    create_size_policy(
        ui.description_edit,
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    ui.description_edit.setMinimumSize(QSize(0, 300))
    desc_layout.addWidget(ui.description_edit)
    desc_layout.setStretch(1, 1)
    content_layout.addLayout(desc_layout)

    tag_layout = QVBoxLayout()
    ui.tags_label = QLabel(content_widget)
    ui.tags_label.setObjectName("tagsLabel")
    tag_layout.addWidget(ui.tags_label)

    ui.tags_edit = QLineEdit(content_widget)
    ui.tags_edit.setObjectName("tagsEdit")
    tag_layout.addWidget(ui.tags_edit)
    content_layout.addLayout(tag_layout)

    arch_impl_layout = QHBoxLayout()

    arch_layout = QVBoxLayout()
    ui.arch_label = QLabel(content_widget)
    ui.arch_label.setObjectName("architectureLabel")
    arch_layout.addWidget(ui.arch_label)

    ui.arch_edit = QLineEdit(content_widget)
    ui.arch_edit.setObjectName("architectureEdit")
    arch_layout.addWidget(ui.arch_edit)
    arch_impl_layout.addLayout(arch_layout)

    impl_layout = QVBoxLayout()
    ui.impl_label = QLabel(content_widget)
    ui.impl_label.setObjectName("implementationLabel")
    impl_layout.addWidget(ui.impl_label)

    ui.impl_edit = QLineEdit(content_widget)
    ui.impl_edit.setObjectName("implementationEdit")
    impl_layout.addWidget(ui.impl_edit)
    arch_impl_layout.addLayout(impl_layout)

    content_layout.addLayout(arch_impl_layout)

    section.setContent(content_widget)

    return section
