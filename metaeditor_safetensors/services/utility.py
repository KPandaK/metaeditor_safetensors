import base64
from enum import Enum
from importlib import resources
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImageWriter, QPixmap


class ModelType(Enum):
    UNKNOWN = "Unknown"
    IMAGE_GENERATION = "Image Generation"
    TEXT_PREDICTION = "Text Prediction"


def get_project_root(start_path: Optional[Path] = None) -> Path:
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    # Search upward for project markers
    markers = ["pyproject.toml", ".git", "justfile"]
    for path in [start_path] + list(start_path.parents):
        for marker in markers:
            if (path / marker).exists():
                return path

    # Fallback to current directory if no markers found
    return start_path


def get_package_root(package_name: str = "metaeditor_safetensors") -> Path:
    try:
        package_files = resources.files(package_name)
        return Path(str(package_files))

    except Exception:
        # Fallback: find in project structure
        project_root = get_project_root()
        return project_root / package_name


def filepath_to_data_uri(filepath: str) -> str:
    try:
        # Load the image
        pixmap = QPixmap(filepath)
        if pixmap.isNull():
            raise ValueError(f"Unsupported or corrupted image file: {filepath}")

        image = pixmap.toImage()

        # Prepare buffer
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)

        # Configure WEBP writer
        writer = QImageWriter(buffer, b"webp")
        writer.setQuality(100)
        writer.setCompression(100)

        if not writer.write(image):
            raise ValueError(f"Failed to write WebP: {writer.errorString()}")

        # Encode as base64
        webp_bytes = buffer.data().data()
        encoded_string = base64.b64encode(webp_bytes).decode("utf-8")
        buffer.close()

        return f"data:image/webp;base64,{encoded_string}"

    except Exception as e:
        raise ValueError(f"Failed to convert image to WebP: {e}")


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
