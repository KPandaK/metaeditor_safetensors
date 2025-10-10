from pyqttooltip.tooltip import Tooltip
from pyqttooltip.utils import Utils
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QToolButton


class PinnableTooltip(Tooltip):
    """Tooltip that supports pinning and corrects placement for nested widgets."""

    def __init__(self, owner: QToolButton):
        super().__init__(owner)
        self._owner = owner
        self._tooltip_pinned = False
        self.setShowDelay(0)
        self.setHideDelay(0)

    def pin(self) -> None:
        self.show(delay=False)
        self._tooltip_pinned = True

    def hide(self, delay: bool = False) -> None:  # type: ignore[override]
        if self._tooltip_pinned:
            return
        super().hide(delay=False)

    def force_hide(self) -> None:
        super().hide(delay=False)

    def handle_click(self, checked: bool = False) -> None:
        if self._tooltip_pinned:
            self._tooltip_pinned = False
            self.clearFocus()
            self.hide()
        else:
            self.show(delay=False)
            self.setFocus(Qt.FocusReason.PopupFocusReason)
            self._tooltip_pinned = True

    def _Tooltip__update_ui(self) -> None:  # type: ignore[override]
        super()._Tooltip__update_ui()

        widget = self._Tooltip__widget  # type: ignore[attr-defined]
        if not widget:
            return

        top_level_parent = Utils.get_top_level_parent(widget)
        assumed_global = top_level_parent.mapToGlobal(widget.pos())
        actual_global = widget.mapToGlobal(QPoint(0, 0))
        delta = actual_global - assumed_global

        if delta == QPoint(0, 0):
            return

        self.move(self.pos() + delta)
