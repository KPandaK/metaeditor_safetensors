"""
Image Service
=============

This module provides a service class for handling image-related operations,
such as converting image files to data URIs and vice-versa. This keeps
image-specific logic decoupled from other parts of the application.
"""

import base64
import os
from PySide6.QtGui import QPixmap

class ImageService:
    """
    Provides methods for image conversions.
    """

    def image_to_data_uri(self, filepath: str) -> str:
        """
        Convert an image file to a data URI string for embedding in metadata.
        
        Args:
            filepath: Path to the image file
            
        Returns:
            Data URI string (e.g., "data:image/png;base64,...")
            
        Raises:
            IOError: If the file cannot be read
            ValueError: If the file format is not supported
        """
        mime_map = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg', 
            '.png': 'png',
            '.bmp': 'bmp',
            '.gif': 'gif'
        }
        
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in mime_map:
            raise ValueError(f"Unsupported image format: {ext}")
        
        try:
            with open(filepath, "rb") as f:
                image_bytes = f.read()
            
            encoded_string = base64.b64encode(image_bytes).decode('utf-8')
            img_type = mime_map[ext]
            
            return f"data:image/{img_type};base64,{encoded_string}"
            
        except IOError as e:
            raise IOError(f"Failed to read image file: {e}")

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
