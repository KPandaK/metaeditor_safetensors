"""
Aspect Ratio Image Widget
=========================

A custom widget for displaying images with proper aspect ratio scaling
using Qt's Graphics View Framework.
"""

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView


class ImageWidget(QGraphicsView):
    """
    A widget that displays images with proper aspect ratio scaling.

    Uses QGraphicsView + QGraphicsPixmapItem for optimal image display
    with automatic scaling that maintains aspect ratio.

    This widget can be used in Qt Designer by promoting a QGraphicsView
    to this class.
    """

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
        """Public method to set primary dimension."""
        if dimension in ["width", "height"]:
            self._primary_dimension = dimension
        else:
            raise ValueError("Dimension must be 'width' or 'height'")

    def setPixmap(self, pixmap):
        """
        Set the pixmap to display.

        Args:
            pixmap (QPixmap or None): The pixmap to display
        """
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

    def _update_size(self):
        """Update widget size based on primary dimension."""
        # Prevent infinite recursion
        if self._updating_size:
            return
        
        self._updating_size = True
        
        try:
            # Get current dimensions
            current_width = self.width()
            current_height = self.height()

            aspect_ratio = 1.0
            image_width = 0
            image_height = 0
            
            if self.hasPixmap():
                # Image state: maintain aspect ratio
                pixmap = self._original_pixmap
                image_width = pixmap.width()
                image_height = pixmap.height()

            # Calculate aspect ratio, avoid division by zero
            if image_width > 0:
                aspect_ratio = image_height / image_width
            else:
                aspect_ratio = 1.0

            # Instead of setFixedHeight/Width, use maximum size constraints
            # This lets the widget grow within available space but not force window resizing
            if self._primary_dimension == "width":
                # Width drives the size, set maximum height based on current width
                desired_height = int(current_width * aspect_ratio)
                constrained_height = max(self._min_height, desired_height)
                self.setMaximumHeight(constrained_height)
                # Remove any width constraints
                self.setMaximumWidth(16777215)  # Qt's QWIDGETSIZE_MAX
            elif self._primary_dimension == "height":
                # Height drives the size, set maximum width based on current height  
                desired_width = int(current_height / aspect_ratio)
                constrained_width = max(self._min_width, desired_width)
                self.setMaximumWidth(constrained_width)
                # Remove any height constraints
                self.setMaximumHeight(16777215)  # Qt's QWIDGETSIZE_MAX
                
        finally:
            self._updating_size = False

    def sizeHint(self):
        """
        Provide size hint based on primary dimension and current state.

        Returns:
            QSize: Preferred size for the widget
        """
        if not self.hasPixmap():
            # Empty state: return square size based on minimum constraints
            return QSize(self._min_width, self._min_height)

        # Image state: calculate size based on primary dimension
        pixmap = self._original_pixmap
        image_width = pixmap.width()
        image_height = pixmap.height()

        if image_width <= 0:
            return QSize(self._min_width, self._min_height)

        # Calculate aspect ratio
        aspect_ratio = image_height / image_width

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
        """Get current widget dimensions for debugging."""
        return {"width": self.width(), "height": self.height()}

    def pixmap(self):
        """
        Get the current pixmap.

        Returns:
            QPixmap: The current pixmap or None
        """
        return self._original_pixmap

    def _fit_in_view(self):
        """Fit the pixmap in the view while maintaining aspect ratio and centering."""
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
        """Handle resize events by refitting the image and updating size."""
        super().resizeEvent(event)
        
        # Re-fit the image when the widget is resized
        self._fit_in_view()
        # Update size for current state (empty or image)
        self._update_size()

    def hasPixmap(self):
        """
        Check if the widget has a pixmap

        Returns:
            bool: True if a pixmap exists, False otherwise
        """
        return self._original_pixmap is not None and not self._original_pixmap.isNull()
