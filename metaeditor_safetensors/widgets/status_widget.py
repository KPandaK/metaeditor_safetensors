from typing import Union

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QSizePolicy, QToolButton, QToolTip

from ..models.modelspec import ComplianceLevel
from ..services.modelspec_service import ComplianceResult


def svg_to_pixmap(
    svg_path: str, width: int, height: int, color: Union[QColor, str]
) -> QPixmap:
    if not isinstance(color, QColor):
        color = QColor(color)

    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)

    # Apply color overlay
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()

    return pixmap


class StatusWidget(QToolButton):
    # Signal emitted when the widget is clicked
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set object name for QSS styling
        self.setObjectName("StatusWidget")

        # Configure QToolButton properties
        self.setAutoRaise(True)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Tooltip pinning state
        self._tooltip_pinned = False
        self._pinned_tooltip_timer = QTimer()
        self._pinned_tooltip_timer.setSingleShot(True)
        self._pinned_tooltip_timer.timeout.connect(self._hide_pinned_tooltip)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        # Remove any default margins that might affect centering
        self.setContentsMargins(0, 0, 0, 0)

        # Set initial state
        self._compliance_result = None
        self._update_display()

        # Connect click signal
        self.clicked.connect(self._handle_click)

    def on_compliance_changed(self, result: ComplianceResult):
        self._compliance_result = result
        self._update_display()

    def _update_display(self):
        if self._compliance_result is None:
            # Set unknown state - use neutral color
            icon_color = QColor("#cccccc")
            icon_pixmap = svg_to_pixmap(":/assets/circle-empty.svg", 20, 20, icon_color)
            self.setIcon(QIcon(icon_pixmap))
            self.setText(" Status: Unknown")
            self.setToolTip(
                "No file loaded! Open a .safetensors file to check ModelSpec compliance."
            )
            return

        result = self._compliance_result
        level = result.level

        # Set icon, text, and color based on compliance level
        if level == ComplianceLevel.COMPLIANT:
            icon_color = QColor("#89d185")  # Success green
            icon_pixmap = svg_to_pixmap(":/assets/circle-check.svg", 16, 16, icon_color)
            self.setText(" Status: Compliant")
            self._current_status = "compliant"
        elif level == ComplianceLevel.PARTIAL:
            icon_color = QColor("#ffcc02")  # Warning yellow
            icon_pixmap = svg_to_pixmap(
                ":/assets/triangle-warning.svg", 16, 16, icon_color
            )
            self.setText(" Status: Partially Compliant")
            self._current_status = "partial"
        elif level == ComplianceLevel.UNKNOWN:
            icon_color = QColor("#cccccc")
            icon_pixmap = svg_to_pixmap(":/assets/circle-empty.svg", 16, 16, icon_color)
            self.setText(" Status: Model Type Needed")
            self._current_status = "unknown"
        else:  # NON_COMPLIANT
            icon_color = QColor("#f14c4c")  # Error red
            icon_pixmap = svg_to_pixmap(":/assets/circle-error.svg", 16, 16, icon_color)
            self.setText(" Status: Not Compliant")
            self._current_status = "non-compliant"

        # Set the QIcon
        self.setIcon(QIcon(icon_pixmap))

        tooltip_content = self._create_tooltip(result)
        self.setToolTip(tooltip_content)

    def _create_tooltip(self, result: ComplianceResult) -> str:
        # Create clean HTML structure for tooltip
        html_parts = []

        # Main container with consistent width
        html_parts.append(
            '<div style="max-width: 450px; font-size: 13px; line-height: 1.5;">'
        )

        html_parts.append('<div style="margin-bottom: 12px;">')
        html_parts.append(
            '<b style="font-size: 14px; color: #ffffff;">ModelSpec Compliance</b>'
        )
        html_parts.append("<br>")
        html_parts.append(f'<span style="font-weight: 600;">{result.summary}</span>')
        html_parts.append("</div>")

        # Model category if available
        if result.model_category.value != "unknown":
            category_name = result.model_category.value.replace("_", " ").title()
            html_parts.append('<div style="margin-bottom: 10px;">')
            html_parts.append(
                f'<b>Model Type:</b> <span style="color: #f0f0f0;">{category_name}</span>'
            )
            html_parts.append("</div>")

        # Details section with improved formatting
        if result.details:
            html_parts.append('<div style="margin-bottom: 10px;">')
            html_parts.append("<b>Details:</b>")
            for i, detail in enumerate(result.details):
                if detail.startswith("  • "):
                    # Nested bullet points with better indentation
                    html_parts.append(
                        f'<div style="margin-left: 20px; margin-top: 2px;">• {detail[4:]}</div>'
                    )
                else:
                    # Regular detail items
                    prefix = "<br>" if i > 0 else ""
                    html_parts.append(
                        f'{prefix}<div style="margin-top: 4px;">{detail}</div>'
                    )
            html_parts.append("</div>")

        # Subtle footer
        html_parts.append(
            '<div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #454545;">'
        )
        html_parts.append(
            '<span style="color: #999999; font-size: 11px;">💡 Click to pin tooltip</span>'
        )
        html_parts.append("</div>")

        html_parts.append("</div>")
        return "".join(html_parts)

    def _handle_click(self):
        self.setFocus()  # Take focus

        # Pin/unpin tooltip behavior
        if self._tooltip_pinned:
            self._unpin_tooltip()
        else:
            self._pin_tooltip()

    def _pin_tooltip(self):
        self._tooltip_pinned = True
        # Show tooltip at widget position
        if hasattr(self, "toolTip") and self.toolTip():
            QToolTip.showText(
                self.mapToGlobal(self.rect().bottomLeft()), self.toolTip(), self
            )
        # Auto-unpin after 5 seconds
        self._pinned_tooltip_timer.start(5000)

    def _unpin_tooltip(self):
        self._tooltip_pinned = False
        self._pinned_tooltip_timer.stop()
        QToolTip.hideText()

    def _hide_pinned_tooltip(self):
        if self._tooltip_pinned:
            self._unpin_tooltip()

    def focusOutEvent(self, event):
        if self._tooltip_pinned:
            self._unpin_tooltip()
        super().focusOutEvent(event)
