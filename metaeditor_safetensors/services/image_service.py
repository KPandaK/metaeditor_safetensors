"""
Image Service
=============

This module provides a service class for handling image-related operations,
such as converting image files to data URIs and vice-versa. This keeps
image-specific logic decoupled from other parts of the application.
"""

import base64

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QPixmap


class ImageService:
    """
    Provides methods for image conversions.
    """

    def image_to_data_uri(self, filepath: str) -> str:
        """
        Convert an image file to a JPEG data URI string for embedding in metadata.
        All input formats are converted to JPEG to comply with modelspec standards.

        Args:
            filepath: Path to the image file

        Returns:
            Data URI string

        Raises:
            IOError: If the file cannot be read
            ValueError: If the file format is not supported by Qt
        """
        try:
            # Load the image using QPixmap (supports many formats)
            pixmap = QPixmap(filepath)
            if pixmap.isNull():
                raise ValueError(f"Unsupported or corrupted image file: {filepath}")

            # Convert to JPEG format in memory using Qt's QBuffer
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            # Save as JPEG with good quality (85 is a good balance of quality/size)
            if not pixmap.save(buffer, "JPEG", quality=85):
                raise ValueError("Failed to convert image to JPEG format")

            jpeg_bytes = buffer.data().data()  # Get the raw bytes
            buffer.close()

            # Encode as base64
            encoded_string = base64.b64encode(jpeg_bytes).decode("utf-8")

            return f"data:image/jpeg;base64,{encoded_string}"

        except IOError as e:
            raise IOError(f"Failed to read image file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to convert image to JPEG: {e}")

    def data_uri_to_pixmap(self, data_uri: str) -> QPixmap | None:
        """
        Convert a data URI string back to a QPixmap.

        Args:
            data_uri: Data URI string (e.g., "data:image/png;base64,...")

        Returns:
            QPixmap object, or None if conversion fails.
        """
        if not data_uri or "base64," not in data_uri:
            return None

        try:
            base64_data = data_uri.split("base64,")[1]
            pixmap_data = base64.b64decode(base64_data)
            pixmap = QPixmap()
            pixmap.loadFromData(pixmap_data)
            return pixmap if not pixmap.isNull() else None
        except Exception:
            return None
