from __future__ import annotations

from PySide6.QtWidgets import QSizePolicy, QWidget


def create_size_policy(
    widget: QWidget,
    horizontal_policy: QSizePolicy.Policy,
    vertical_policy: QSizePolicy.Policy,
    horizontal_stretch: int = 0,
    vertical_stretch: int = 0,
) -> None:
    size_policy = QSizePolicy(horizontal_policy, vertical_policy)
    size_policy.setHorizontalStretch(horizontal_stretch)
    size_policy.setVerticalStretch(vertical_stretch)
    size_policy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
    widget.setSizePolicy(size_policy)
