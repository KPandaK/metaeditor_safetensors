from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QLabel, QLineEdit, QTextEdit, QVBoxLayout, QWidget
from superqt.collapsible import QCollapsible


def build_usage_section(ui, parent) -> QCollapsible:
    section = QCollapsible(parent)
    section.layout().setSpacing(0)

    content_widget = QWidget(section)
    content_layout = QVBoxLayout(content_widget)

    usage_hint_layout = QVBoxLayout()
    ui.usage_hint_label = QLabel(content_widget)
    ui.usage_hint_label.setObjectName("usageHintLabel")
    usage_hint_layout.addWidget(ui.usage_hint_label)

    ui.usage_hint_edit = QTextEdit(content_widget)
    ui.usage_hint_edit.setObjectName("usageHintEdit")
    ui.usage_hint_edit.setMaximumSize(QSize(16777215, 100))
    usage_hint_layout.addWidget(ui.usage_hint_edit)
    content_layout.addLayout(usage_hint_layout)

    license_layout = QVBoxLayout()
    ui.license_label = QLabel(content_widget)
    ui.license_label.setObjectName("licenseLabel")
    license_layout.addWidget(ui.license_label)

    ui.license_edit = QLineEdit(content_widget)
    ui.license_edit.setObjectName("licenseEdit")
    license_layout.addWidget(ui.license_edit)
    content_layout.addLayout(license_layout)

    section.setContent(content_widget)

    return section
