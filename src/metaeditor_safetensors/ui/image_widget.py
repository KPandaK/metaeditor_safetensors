"""
Aspect Ratio Image Widget
=========================

A custom widget for displaying images with proper aspect ratio scaling
using Qt's Graphics View Framework.
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPixmap, QPainter


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
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Hide scrollbars - we want the image to fit in view
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Add pixmap item to scene
        self._scene.addItem(self._pixmap_item)
        
        # Store original pixmap for proper scaling
        self._original_pixmap = None
        
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
            # Fit the pixmap in the view while maintaining aspect ratio
            self._fit_in_view()
        else:
            self._pixmap_item.setVisible(False)
            self._original_pixmap = None
        
        # Emit signal that pixmap changed
        self.pixmapChanged.emit()
    
    def pixmap(self):
        """
        Get the current pixmap.
        
        Returns:
            QPixmap: The current pixmap or None
        """
        return self._original_pixmap
    
    def _fit_in_view(self):
        """Fit the pixmap in the view while maintaining aspect ratio."""
        if self._original_pixmap and not self._original_pixmap.isNull():
            # Get the pixmap rect in scene coordinates
            pixmap_rect = self._pixmap_item.boundingRect()
            # Fit the pixmap in view with aspect ratio preserved
            self.fitInView(pixmap_rect, Qt.AspectRatioMode.KeepAspectRatio)
    
    def resizeEvent(self, event):
        """Handle resize events by refitting the image."""
        super().resizeEvent(event)
        # Re-fit the image when the widget is resized
        self._fit_in_view()
    
    def hasPixmap(self):
        """
        Check if a pixmap is currently displayed.
        
        Returns:
            bool: True if a pixmap is displayed, False otherwise
        """
        return self._original_pixmap is not None and not self._original_pixmap.isNull()
