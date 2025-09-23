from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView

# Qt's maximum widget size constant
QWIDGETSIZE_MAX = 16777215


class ImageWidget(QGraphicsView):
    # Signal emitted when the pixmap changes
    pixmapChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create scene and pixmap item
        self._scene = QGraphicsScene(self)
        self._pixmap_item = QGraphicsPixmapItem()

        # Configure the view
        self.setScene(self._scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Hide scrollbars - we want the image to fit in view
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setProperty("hasImage", "false")

        # Add pixmap item to scene
        self._scene.addItem(self._pixmap_item)

        # Store original pixmap for proper scaling
        self._original_pixmap = None

        # Primary dimension: which dimension drives the square sizing
        self._primary_dimension = "width"  # "width" or "height"

        # Cache minimum constraints
        self._min_height = self.minimumHeight()
        self._min_width = self.minimumWidth()

        # Guard against infinite resize loops
        self._updating_size = False

    def setPrimaryDimension(self, dimension):
        if dimension in ["width", "height"]:
            self._primary_dimension = dimension
        else:
            raise ValueError("Dimension must be 'width' or 'height'")

    def setPixmap(self, pixmap):
        self._original_pixmap = pixmap

        if pixmap and not pixmap.isNull():
            self._pixmap_item.setPixmap(pixmap)
            self._pixmap_item.setVisible(True)
            self.setProperty("hasImage", "true")
            # Fit the pixmap in the view while maintaining aspect ratio
            self._fit_in_view()
        else:
            self._pixmap_item.setVisible(False)
            self._original_pixmap = None
            self.setProperty("hasImage", "false")

        self.style().unpolish(self)
        self.style().polish(self)

        self._update_size()

        # Emit signal that pixmap changed
        self.pixmapChanged.emit()

        # Update size hint when pixmap changes
        self.updateGeometry()

    def _calculate_aspect_ratio(self):
        if self._original_pixmap is not None and not self._original_pixmap.isNull():
            pixmap = self._original_pixmap
            image_width = pixmap.width()
            image_height = pixmap.height()

            if image_width > 0:
                return image_height / image_width
            else:
                return 1.0
        else:
            return 1.0

    def _update_size(self):
        # Prevent infinite recursion
        if self._updating_size:
            return

        self._updating_size = True

        try:
            # Get current dimensions
            current_width = self.width()
            current_height = self.height()

            aspect_ratio = self._calculate_aspect_ratio()

            # Apply size constraints based on primary dimension and aspect ratio
            # This lets the widget grow within available space but not force window resizing
            if self._primary_dimension == "width":
                # Width drives the size, set maximum height based on current width
                desired_height = int(current_width * aspect_ratio)
                constrained_height = max(self._min_height, desired_height)
                self.setMaximumHeight(constrained_height)
                # Remove any width constraints
                self.setMaximumWidth(QWIDGETSIZE_MAX)
            elif self._primary_dimension == "height":
                # Height drives the size, set maximum width based on current height
                desired_width = int(current_height / aspect_ratio)
                constrained_width = max(self._min_width, desired_width)
                self.setMaximumWidth(constrained_width)
                # Remove any height constraints
                self.setMaximumHeight(QWIDGETSIZE_MAX)

        finally:
            self._updating_size = False

    def sizeHint(self):
        aspect_ratio = self._calculate_aspect_ratio()

        # Get current widget dimensions (or use reasonable defaults)
        current_width = self.width()
        current_height = self.height()

        if self._primary_dimension == "width":
            # Width-driven: calculate ideal height
            ideal_height = int(current_width * aspect_ratio)
            constrained_height = max(self._min_height, ideal_height)
            return QSize(current_width, constrained_height)
        elif self._primary_dimension == "height":
            # Height-driven: calculate ideal width
            ideal_width = int(current_height / aspect_ratio)
            constrained_width = max(self._min_width, ideal_width)
            return QSize(constrained_width, current_height)

        # Fallback (shouldn't happen)
        return QSize(self._min_width, self._min_height)

    def getCurrentSize(self):
        return {"width": self.width(), "height": self.height()}

    def pixmap(self):
        return self._original_pixmap

    def _fit_in_view(self):
        if self._original_pixmap and not self._original_pixmap.isNull():
            # Get the pixmap rect in scene coordinates
            pixmap_rect = self._pixmap_item.boundingRect()

            # Set scene rect to match pixmap rect for proper centering
            self._scene.setSceneRect(pixmap_rect)

            # Fit the pixmap in view with aspect ratio preserved
            self.fitInView(pixmap_rect, Qt.AspectRatioMode.KeepAspectRatio)

            # Force center alignment
            self.centerOn(pixmap_rect.center())

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Re-fit the image when the widget is resized (only if we have a pixmap)
        if self.hasPixmap():
            self._fit_in_view()

        # Update size for current state (empty or image)
        self._update_size()

    def hasPixmap(self):
        return self._original_pixmap is not None and not self._original_pixmap.isNull()
