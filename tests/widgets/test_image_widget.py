from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, QUrl

from metaeditor_safetensors.widgets.image_widget import ImageWidget


@pytest.fixture
def image_widget(qtbot):
    widget = ImageWidget()
    qtbot.addWidget(widget)
    return widget


def test_extract_image_path_returns_supported_file(image_widget, tmp_path):
    file_path = tmp_path / "thumb.png"
    file_path.write_text("content")

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(file_path))])

    result = image_widget._extract_image_path(mime)
    assert Path(result) == file_path


def test_extract_image_path_ignores_non_image(image_widget, tmp_path):
    file_path = tmp_path / "document.txt"
    file_path.write_text("content")

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(file_path))])

    assert image_widget._extract_image_path(mime) is None


def test_extract_image_path_requires_local_file(image_widget):
    mime = QMimeData()
    mime.setUrls([QUrl("https://example.com/image.png")])

    assert image_widget._extract_image_path(mime) is None
