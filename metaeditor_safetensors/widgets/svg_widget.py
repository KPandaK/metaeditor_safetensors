from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QSizePolicy, QWidget


class SvgWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._svg_renderer = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def loadSvg(self, path: str):
        self._svg_renderer = QSvgRenderer(path)
        if not self._svg_renderer.isValid():
            self._svg_renderer = None
        self.update()

    def paintEvent(self, event):
        # return self._svg_renderer is not None and self._svg_renderer.isValid()
        if self._svg_renderer is None or not self._svg_renderer.isValid():
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
        if self._svg_renderer is not None and self._svg_renderer.isValid():
            return self._svg_renderer.defaultSize()
        return QSize(100, 100)
