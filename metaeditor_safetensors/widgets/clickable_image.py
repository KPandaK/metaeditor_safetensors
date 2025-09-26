import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

logger = logging.getLogger(__name__)


class ClickableImage(QLabel):
    """Clickable label used for image-style links in the UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setScaledContents(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    # Retain logging hook for compatibility if future code sets pixmaps directly
    def setPixmap(self, pixmap):  # type: ignore[override]
        logger.debug("ClickableImage setPixmap called - image styling is theme-driven")
        super().setPixmap(pixmap)
