from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from ...widgets.image_widget import ImageWidget
from ..layout_utils import create_size_policy


def build_thumbnail_section(ui, parent) -> QVBoxLayout:
    layout = QVBoxLayout()
    layout.setObjectName("thumbnailLayout")

    ui.thumbnail_group = QGroupBox()
    ui.thumbnail_group.setObjectName("thumbnailGroup")
    create_size_policy(
        ui.thumbnail_group,
        QSizePolicy.Policy.Preferred,
        QSizePolicy.Policy.Preferred,
    )

    group_layout = QVBoxLayout(ui.thumbnail_group)
    group_layout.setSpacing(6)

    ui.thumbnail_display = ImageWidget(parent)
    ui.thumbnail_display.setObjectName("thumbnailDisplay")
    ui.thumbnail_display.setPrimaryDimension("width")
    create_size_policy(
        ui.thumbnail_display,
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
        vertical_stretch=1,
    )
    group_layout.addWidget(ui.thumbnail_display)

    buttons_layout = QHBoxLayout()
    buttons_layout.setContentsMargins(0, 0, 0, 10)
    buttons_layout.setObjectName("thumbnailButtonsLayout")

    ui.set_thumbnail_btn = QPushButton(ui.thumbnail_group)
    ui.set_thumbnail_btn.setObjectName("setThumbnailBtn")
    ui.set_thumbnail_btn.setMaximumSize(QSize(16777215, 24))
    buttons_layout.addWidget(ui.set_thumbnail_btn)

    ui.view_thumbnail_btn = QPushButton(ui.thumbnail_group)
    ui.view_thumbnail_btn.setObjectName("viewThumbnailBtn")
    ui.view_thumbnail_btn.setMaximumSize(QSize(16777215, 24))
    buttons_layout.addWidget(ui.view_thumbnail_btn)

    ui.clear_thumbnail_btn = QPushButton(ui.thumbnail_group)
    ui.clear_thumbnail_btn.setObjectName("clearThumbnailBtn")
    ui.clear_thumbnail_btn.setMaximumSize(QSize(16777215, 24))
    buttons_layout.addWidget(ui.clear_thumbnail_btn)

    group_layout.addLayout(buttons_layout)
    group_layout.setStretch(0, 1)

    layout.addWidget(ui.thumbnail_group)
    layout.addItem(
        QSpacerItem(
            20,
            10,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )
    )

    return layout
