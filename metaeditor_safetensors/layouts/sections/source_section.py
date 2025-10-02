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
    QWidget,
)
from superqt.collapsible import QCollapsible

from ..layout_utils import create_size_policy


def build_source_section(ui, parent) -> QCollapsible:
    section = QCollapsible(parent)

    layout = section.layout()
    if layout is not None:
        layout.setSpacing(0)

    content_widget = QWidget(section)
    content_layout = QVBoxLayout(content_widget)

    author_date_layout = QHBoxLayout()

    author_layout = QVBoxLayout()
    ui.author_label = QLabel(content_widget)
    ui.author_label.setObjectName("authorLabel")
    author_layout.addWidget(ui.author_label)

    ui.author_edit = QLineEdit(content_widget)
    ui.author_edit.setObjectName("authorEdit")
    create_size_policy(
        ui.author_edit,
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Fixed,
    )
    author_layout.addWidget(ui.author_edit)
    author_date_layout.addLayout(author_layout)

    date_layout = QVBoxLayout()
    ui.date_label = QLabel(content_widget)
    ui.date_label.setObjectName("dateLabel")
    date_layout.addWidget(ui.date_label)

    ui.date_time_edit = QDateTimeEdit(content_widget)
    ui.date_time_edit.setObjectName("dateTimeEdit")
    ui.date_time_edit.setMinimumSize(QSize(140, 22))
    ui.date_time_edit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    ui.date_time_edit.setCalendarPopup(True)
    date_layout.addWidget(ui.date_time_edit)
    author_date_layout.addLayout(date_layout)

    content_layout.addLayout(author_date_layout)

    merged_layout = QVBoxLayout()
    ui.merged_from_label = QLabel(content_widget)
    ui.merged_from_label.setObjectName("mergedFromLabel")
    merged_layout.addWidget(ui.merged_from_label)

    ui.merged_from_edit = QLineEdit(content_widget)
    ui.merged_from_edit.setObjectName("mergedFromEdit")
    merged_layout.addWidget(ui.merged_from_edit)
    content_layout.addLayout(merged_layout)

    section.setContent(content_widget)

    return section
