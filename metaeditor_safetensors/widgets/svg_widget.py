"""
SVG Widget
==========

A specialized widget for displaying SVG images with crisp, high-quality rendering
at any scale. Uses QSvgRenderer for perfect vector graphics display.
"""

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QSizePolicy, QWidget


class SvgWidget(QWidget):
    """
    A widget specifically designed for displaying SVG images with crisp rendering.

    This widget uses QSvgRenderer to render SVG files directly from vector data,
    ensuring sharp, high-quality display at any size without pixelation.

    This widget can be used in Qt Designer by promoting a QWidget to this class.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._svg_renderer = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def loadSvg(self, path: str):
        """
        Load an SVG file from the given path.

        Args:
            path (str): Path to the SVG file
        """
        self._svg_renderer = QSvgRenderer(path)
        if not self._svg_renderer.isValid():
            self._svg_renderer = None
        self.update()

    def setSvgData(self, svg_data: bytes):
        """
        Load SVG from raw data bytes.

        Args:
            svg_data (bytes): Raw SVG data
        """
        self._svg_renderer = QSvgRenderer(svg_data)
        if not self._svg_renderer.isValid():
            self._svg_renderer = None
        self.update()

    def hasSvg(self):
        """
        Check if a valid SVG is currently loaded.

        Returns:
            bool: True if a valid SVG is loaded, False otherwise
        """
        return self._svg_renderer is not None and self._svg_renderer.isValid()

    def paintEvent(self, event):
        """
        Handle the paint event to render the SVG with correct aspect ratio.
        """
        if not self.hasSvg():
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        target_rect = self.rect()
        svg_size = self._svg_renderer.defaultSize()

        # Scale SVG to fit widget while preserving aspect ratio
        scaled_size = svg_size.scaled(
            target_rect.size(), Qt.AspectRatioMode.KeepAspectRatio
        )

        # Center the SVG within the widget
        render_rect = QRect(QPoint(0, 0), scaled_size)
        render_rect.moveCenter(target_rect.center())

        # Render the SVG at the calculated size and position
        self._svg_renderer.render(painter, render_rect)

        super().paintEvent(event)

    def sizeHint(self):
        """
        Provide a size hint based on the SVG's default size.

        Returns:
            QSize: The preferred size for this widget
        """
        if self.hasSvg():
            return self._svg_renderer.defaultSize()
        return QSize(100, 100)
