from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDateTimeEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
)

from ...widgets.collapsible_section import CollapsibleSection
from ..layout_utils import create_size_policy


def build_source_section(ui, parent) -> CollapsibleSection:
    section = CollapsibleSection(parent)
    section.setMinimumSize(QSize(0, 0))

    author_date_layout = QHBoxLayout()

    author_layout = QVBoxLayout()
    ui.author_label = QLabel(section)
    ui.author_label.setObjectName("authorLabel")
    author_layout.addWidget(ui.author_label)

    ui.author_edit = QLineEdit(section)
    ui.author_edit.setObjectName("authorEdit")
    create_size_policy(
        ui.author_edit,
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    author_layout.addWidget(ui.author_edit)
    author_date_layout.addLayout(author_layout)

    date_layout = QVBoxLayout()
    ui.date_label = QLabel(section)
    ui.date_label.setObjectName("dateLabel")
    date_layout.addWidget(ui.date_label)

    ui.date_time_edit = QDateTimeEdit(section)
    ui.date_time_edit.setObjectName("dateTimeEdit")
    ui.date_time_edit.setMinimumSize(QSize(140, 22))
    ui.date_time_edit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    ui.date_time_edit.setCalendarPopup(True)
    date_layout.addWidget(ui.date_time_edit)
    author_date_layout.addLayout(date_layout)

    section.add_layout(author_date_layout)

    merged_layout = QVBoxLayout()
    ui.merged_from_label = QLabel(section)
    ui.merged_from_label.setObjectName("mergedFromLabel")
    merged_layout.addWidget(ui.merged_from_label)

    ui.merged_from_edit = QLineEdit(section)
    ui.merged_from_edit.setObjectName("mergedFromEdit")
    merged_layout.addWidget(ui.merged_from_edit)
    section.add_layout(merged_layout)

    return section
