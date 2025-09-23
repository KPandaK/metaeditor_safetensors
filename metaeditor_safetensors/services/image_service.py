import base64

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QPixmap


class ImageService:
    @staticmethod
    def filepath_to_data_uri(filepath: str) -> str:
        try:
            # Load the image using QPixmap (supports many formats)
            pixmap = QPixmap(filepath)
            if pixmap.isNull():
                raise ValueError(f"Unsupported or corrupted image file: {filepath}")

            # Convert to PNG format in memory using Qt's QBuffer
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            # Save as PNG
            if not pixmap.save(buffer, "PNG"):
                raise ValueError("Failed to convert image to PNG format")

            png_bytes = buffer.data().data()  # Get the raw bytes
            buffer.close()

            # Encode as base64
            encoded_string = base64.b64encode(png_bytes).decode("utf-8")

            return f"data:image/png;base64,{encoded_string}"

        except IOError as e:
            raise IOError(f"Failed to read image file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to convert image to PNG: {e}")

    @staticmethod
    def data_uri_to_pixmap(data_uri: str) -> QPixmap | None:
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

    @staticmethod
    def pixmap_to_data_uri(pixmap: QPixmap) -> str:
        if pixmap.isNull():
            return ""

        # Convert pixmap to PNG bytes
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not pixmap.save(buffer, "PNG"):
            return ""

        png_bytes = buffer.data().data()
        buffer.close()

        # Encode as base64 data URI
        encoded_string = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{encoded_string}"
