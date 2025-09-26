from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Property, QDateTime, QEvent, Qt, Signal
from PySide6.QtGui import (
    QFocusEvent,
    QInputMethodEvent,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QWheelEvent,
)
from PySide6.QtQuick import QQuickItem, QQuickPaintedItem
from PySide6.QtWidgets import QApplication, QDateTimeEdit


class QDateTimeEditBridge(QQuickPaintedItem):
    """Bridge control that embeds a QWidget-based QDateTimeEdit into QML."""

    isoDateTimeChanged = Signal(str)
    editingFinished = Signal()

    def __init__(self, parent: Optional[QQuickItem] = None) -> None:
        super().__init__(parent)

        self._widget = QDateTimeEdit()
        self._widget.setCalendarPopup(True)
        self._widget.dateTimeChanged.connect(self._on_widget_datetime_changed)
        self._widget.editingFinished.connect(self.editingFinished)
        self._widget.installEventFilter(self)

        self.setFlag(QQuickItem.ItemHasContents, True)
        self.setFlag(QQuickItem.ItemAcceptsInputMethod, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.AllButtons)
        self.setAcceptHoverEvents(True)

        self.setImplicitWidth(self._widget.sizeHint().width())
        self.setImplicitHeight(self._widget.sizeHint().height())

    # ------------------------------------------------------------------
    # QWidget <-> QML state synchronisation
    # ------------------------------------------------------------------
    def geometryChanged(self, new_geometry, old_geometry) -> None:  # type: ignore[override]
        super().geometryChanged(new_geometry, old_geometry)
        self._widget.resize(int(new_geometry.width()), int(new_geometry.height()))
        self.update()

    def itemChange(self, change: "QQuickItem.ItemChange", value):  # type: ignore[override]
        if change == QQuickItem.ItemChange.ItemEnabledHasChanged:
            self._widget.setEnabled(self.isEnabled())
            self.update()
        elif change == QQuickItem.ItemChange.ItemActiveFocusHasChanged:
            if self.isActiveFocus():
                focus_event = QFocusEvent(QEvent.Type.FocusIn, Qt.FocusReason.OtherFocusReason)
            else:
                focus_event = QFocusEvent(QEvent.Type.FocusOut, Qt.FocusReason.OtherFocusReason)
            QApplication.sendEvent(self._widget, focus_event)
            self.update()
        return super().itemChange(change, value)

    def eventFilter(self, obj, event):  # type: ignore[override]
        if obj is self._widget and event.type() in {
            QEvent.Type.UpdateRequest,
            QEvent.Type.Paint,
            QEvent.Type.Resize,
            QEvent.Type.StyleChange,
        }:
            self.update()
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------
    def paint(self, painter: QPainter) -> None:  # type: ignore[override]
        self._widget.render(painter)

    # ------------------------------------------------------------------
    # QQuickItem event overrides
    # ------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if not self.isActiveFocus():
            self.forceActiveFocus()
        widget_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            event.position(),
            event.globalPosition(),
            event.button(),
            event.buttons(),
            event.modifiers(),
            event.source(),
        )
        QApplication.sendEvent(self._widget, widget_event)
        self.update()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        widget_event = QMouseEvent(
            QEvent.Type.MouseMove,
            event.position(),
            event.globalPosition(),
            event.button(),
            event.buttons(),
            event.modifiers(),
            event.source(),
        )
        QApplication.sendEvent(self._widget, widget_event)
        self.update()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        widget_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            event.position(),
            event.globalPosition(),
            event.button(),
            event.buttons(),
            event.modifiers(),
            event.source(),
        )
        QApplication.sendEvent(self._widget, widget_event)
        self.update()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        widget_event = QMouseEvent(
            QEvent.Type.MouseButtonDblClick,
            event.position(),
            event.globalPosition(),
            event.button(),
            event.buttons(),
            event.modifiers(),
            event.source(),
        )
        QApplication.sendEvent(self._widget, widget_event)
        self.update()
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:  # type: ignore[override]
        widget_event = QWheelEvent(
            event.position(),
            event.globalPosition(),
            event.pixelDelta(),
            event.angleDelta(),
            event.buttons(),
            event.modifiers(),
            event.phase(),
            event.isInverted(),
            event.source(),
        )
        QApplication.sendEvent(self._widget, widget_event)
        self.update()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        widget_event = QKeyEvent(
            QEvent.Type.KeyPress,
            event.key(),
            event.modifiers(),
            event.text(),
            event.isAutoRepeat(),
            event.count(),
        )
        QApplication.sendEvent(self._widget, widget_event)
        self.update()
        event.accept()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        widget_event = QKeyEvent(
            QEvent.Type.KeyRelease,
            event.key(),
            event.modifiers(),
            event.text(),
            event.isAutoRepeat(),
            event.count(),
        )
        QApplication.sendEvent(self._widget, widget_event)
        self.update()
        event.accept()

    def focusInEvent(self, event: QFocusEvent) -> None:  # type: ignore[override]
        QApplication.sendEvent(self._widget, QFocusEvent(QEvent.Type.FocusIn, event.reason()))
        self.update()
        event.accept()

    def focusOutEvent(self, event: QFocusEvent) -> None:  # type: ignore[override]
        QApplication.sendEvent(self._widget, QFocusEvent(QEvent.Type.FocusOut, event.reason()))
        self.update()
        event.accept()

    def inputMethodEvent(self, event: QInputMethodEvent) -> None:  # type: ignore[override]
        QApplication.sendEvent(self._widget, event)
        self.update()
        event.accept()

    # ------------------------------------------------------------------
    # Exposed API
    # ------------------------------------------------------------------
    def _on_widget_datetime_changed(self, value: QDateTime) -> None:
        self.isoDateTimeChanged.emit(value.toString(Qt.DateFormat.ISODateWithMs))
        self.update()

    def _get_iso_datetime(self) -> str:
        return self._widget.dateTime().toString(Qt.DateFormat.ISODateWithMs)

    def _set_iso_datetime(self, value: str) -> None:
        if not value:
            return

        dt = QDateTime.fromString(value, Qt.DateFormat.ISODateWithMs)
        if not dt.isValid():
            dt = QDateTime.fromString(value, Qt.DateFormat.ISODate)
        if dt.isValid() and dt != self._widget.dateTime():
            self._widget.setDateTime(dt)
            self.update()

    isoDateTime = Property(str, _get_iso_datetime, _set_iso_datetime, notify=isoDateTimeChanged)

    def _get_display_format(self) -> str:
        return self._widget.displayFormat()

    def _set_display_format(self, value: str) -> None:
        if value and value != self._widget.displayFormat():
            self._widget.setDisplayFormat(value)
            self.update()

    displayFormat = Property(str, _get_display_format, _set_display_format)

    def _get_calendar_popup(self) -> bool:
        return self._widget.calendarPopup()

    def _set_calendar_popup(self, enabled: bool) -> None:
        self._widget.setCalendarPopup(bool(enabled))
        self.update()

    calendarPopup = Property(bool, _get_calendar_popup, _set_calendar_popup)

    @property
    def widget(self) -> QDateTimeEdit:
        return self._widget

    def destroy(self) -> None:
        self._widget.deleteLater()
        super().destroy()


__all__ = ["QDateTimeEditBridge"]
