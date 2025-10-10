from typing import Union

from pyqttooltip.enums import TooltipPlacement
from PySide6.QtCore import QMargins, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QToolButton

from ..models.modelspec import ComplianceLevel
from ..services.modelspec_service import ComplianceResult
from .pinnable_tooltip import PinnableTooltip


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
    def __init__(self, parent=None):
        super().__init__(parent)

        self._icon_size = QSize(20, 20)

        # Set object name for QSS styling
        self.setObjectName("StatusWidget")

        # Configure QToolButton properties
        self.setAutoRaise(True)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setIconSize(self._icon_size)

        # Remove any default margins that might affect centering
        self.setContentsMargins(0, 0, 0, 0)

        # Configure custom tooltip
        self._tooltip = PinnableTooltip(self)
        self._tooltip.setWidget(self)
        self._tooltip.setPlacement(TooltipPlacement.TOP)

        self._tooltip.setBackgroundColor(QColor("#252526"))
        self._tooltip.setBorderEnabled(True)
        self._tooltip.setBorderColor(QColor("#454545"))
        self._tooltip.setTextColor(QColor("#f5f5f5"))
        self._tooltip.setMargins(QMargins(16, 12, 16, 12))
        self._tooltip.setMaximumWidth(420)
        self._tooltip.setDropShadowStrength(6.0)

        # Set initial state
        self._compliance_result = None
        self._update_display()

        # Connect click signal
        self.clicked.connect(self._tooltip.handle_click)

    def on_compliance_changed(self, result: ComplianceResult):
        self._compliance_result = result
        self._update_display()

    def _update_display(self):
        if self._compliance_result is None:
            # Set unknown state - use neutral color
            icon_color = QColor("#cccccc")
            icon_pixmap = svg_to_pixmap(
                ":/assets/circle-empty.svg",
                self._icon_size.width(),
                self._icon_size.height(),
                icon_color,
            )
            self.setIcon(QIcon(icon_pixmap))
            self.setText(" Status: Unknown")
            self._tooltip.setText(
                "<b>ModelSpec Compliance</b><br>No file loaded! Open a .safetensors file to check ModelSpec compliance."
            )
            self._tooltip.force_hide()
            self._tooltip_pinned = False
            return

        result = self._compliance_result
        level = result.level

        # Set icon, text, and color based on compliance level
        if level == ComplianceLevel.COMPLIANT:
            icon_color = QColor("#89d185")  # Success green
            icon_pixmap = svg_to_pixmap(
                ":/assets/circle-check.svg",
                self._icon_size.width(),
                self._icon_size.height(),
                icon_color,
            )
            self.setText(" Status: Compliant")
            self._current_status = "compliant"
        elif level == ComplianceLevel.PARTIAL:
            icon_color = QColor("#ffcc02")  # Warning yellow
            icon_pixmap = svg_to_pixmap(
                ":/assets/triangle-warning.svg",
                self._icon_size.width(),
                self._icon_size.height(),
                icon_color,
            )
            self.setText(" Status: Partially Compliant")
            self._current_status = "partial"
        elif level == ComplianceLevel.UNKNOWN:
            icon_color = QColor("#cccccc")
            icon_pixmap = svg_to_pixmap(
                ":/assets/circle-empty.svg",
                self._icon_size.width(),
                self._icon_size.height(),
                icon_color,
            )
            self.setText(" Status: Model Type Needed")
            self._current_status = "unknown"
        else:  # NON_COMPLIANT
            icon_color = QColor("#f14c4c")  # Error red
            icon_pixmap = svg_to_pixmap(
                ":/assets/circle-error.svg",
                self._icon_size.width(),
                self._icon_size.height(),
                icon_color,
            )
            self.setText(" Status: Not Compliant")
            self._current_status = "non-compliant"

        # Set the QIcon
        self.setIcon(QIcon(icon_pixmap))

        tooltip_content = self._create_tooltip(result)
        self._tooltip.setText(tooltip_content)

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
