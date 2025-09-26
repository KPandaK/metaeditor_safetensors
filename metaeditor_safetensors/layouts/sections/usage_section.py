from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QLabel, QLineEdit, QTextEdit, QVBoxLayout

from ...widgets.collapsible_section import CollapsibleSection


def build_usage_section(ui, parent) -> CollapsibleSection:
    section = CollapsibleSection(parent)
    section.setMinimumSize(QSize(0, 0))

    usage_hint_layout = QVBoxLayout()
    ui.usage_hint_label = QLabel(section)
    ui.usage_hint_label.setObjectName("usageHintLabel")
    usage_hint_layout.addWidget(ui.usage_hint_label)

    ui.usage_hint_edit = QTextEdit(section)
    ui.usage_hint_edit.setObjectName("usageHintEdit")
    ui.usage_hint_edit.setMaximumSize(QSize(16777215, 100))
    usage_hint_layout.addWidget(ui.usage_hint_edit)
    section.add_layout(usage_hint_layout)

    license_layout = QVBoxLayout()
    ui.license_label = QLabel(section)
    ui.license_label.setObjectName("licenseLabel")
    license_layout.addWidget(ui.license_label)

    ui.license_edit = QLineEdit(section)
    ui.license_edit.setObjectName("licenseEdit")
    license_layout.addWidget(ui.license_edit)
    section.add_layout(license_layout)

    return section
