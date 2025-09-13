"""
Clickable Image Button Widget
=============================

A simple button widget that can display different dark/light images.
"""

import logging
from enum import Enum
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"


class ClickableImage(QLabel):
    """
    A simple button widget that can display different images.

    This button allows setting multiple images and switching between them
    programmatically. It does not have any automatic theme detection or
    dependencies on external services.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Image paths for different states
        self._light_image_path: Optional[str] = None
        self._dark_image_path: Optional[str] = None

        # Cache for loaded pixmaps
        self._light_pixmap: Optional[QPixmap] = None
        self._dark_pixmap: Optional[QPixmap] = None

        # Current image mode
        self._current_mode: ThemeMode = ThemeMode.LIGHT

        # Initialize appearance
        self._update_button_image()

    def setImages(self, light_image_path: str, dark_image_path: str):
        """
        Set both light and dark images at once.

        Args:
            light_image_path (str): Path to the light image file
            dark_image_path (str): Path to the dark image file
        """
        self._light_image_path = light_image_path
        self._dark_image_path = dark_image_path
        self._light_pixmap = None
        self._dark_pixmap = None

    def setMode(self, mode: ThemeMode):
        """
        Set the current display mode.

        Args:
            mode (ThemeMode): Either ThemeMode.LIGHT or ThemeMode.DARK
        """
        old_mode = self._current_mode
        self._current_mode = mode
        if old_mode != self._current_mode:
            self._update_button_image()

    def _update_button_image(self):
        """Update the button's image based on the current mode."""
        target_image_path = self._get_current_image_path()

        if not target_image_path:
            # No image available, clear the pixmap
            self.setPixmap(QPixmap())
            return

        try:
            # Load and cache the appropriate pixmap
            if self._current_mode == ThemeMode.LIGHT and self._light_pixmap is None:
                if self._light_image_path:
                    self._light_pixmap = QPixmap(self._light_image_path)
            elif self._current_mode == ThemeMode.DARK and self._dark_pixmap is None:
                if self._dark_image_path:
                    self._dark_pixmap = QPixmap(self._dark_image_path)

            # Get the cached pixmap
            pixmap = self._get_current_pixmap()

            if pixmap and not pixmap.isNull():
                # Set the pixmap directly on the QLabel
                self.setPixmap(pixmap)
                logger.debug(f"Updated button image for {self._current_mode} mode")
            else:
                logger.warning(f"Failed to load image: {target_image_path}")
                self.setPixmap(QPixmap())

        except Exception as e:
            logger.error(f"Error updating button image: {e}")
            self.setPixmap(QPixmap())

    def _get_current_image_path(self) -> Optional[str]:
        """
        Get the image path that should be displayed for the current mode.

        Returns:
            str: The path to the appropriate image, or None if not available
        """
        if self._current_mode == ThemeMode.LIGHT:
            return self._light_image_path
        else:
            return self._dark_image_path

    def _get_current_pixmap(self) -> Optional[QPixmap]:
        """
        Get the pixmap that should be displayed for the current mode.

        Returns:
            QPixmap: The appropriate pixmap, or None if not available
        """
        if self._current_mode == ThemeMode.LIGHT:
            return self._light_pixmap
        else:
            return self._dark_pixmap
