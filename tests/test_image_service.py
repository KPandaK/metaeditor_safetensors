"""
Tests for the ImageService module.

This module tests the image conversion functionality of the ImageService,
including conversion to JPEG format and data URI generation.
"""

import base64
import os
import shutil
import tempfile

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from metaeditor_safetensors.services.image_service import ImageService


@pytest.fixture(scope="class")
def qapp():
    """Set up QApplication for Qt functionality."""
    # Check if QApplication already exists
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app


@pytest.fixture
def image_service():
    """Set up ImageService instance."""
    return ImageService()


@pytest.fixture
def temp_dir():
    """Set up test fixtures."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up temporary files
    shutil.rmtree(temp_dir, ignore_errors=True)


def create_test_image(
    temp_dir: str, filename: str, format: str = "PNG", size: tuple = (100, 100)
) -> str:
    """
    Create a test image file for testing.

    Args:
        temp_dir: Temporary directory path
        filename: Name of the file to create
        format: Image format (PNG, JPEG, etc.)
        size: Image size as (width, height)

    Returns:
        Full path to the created test image
    """
    # Create a simple test image
    pixmap = QPixmap(size[0], size[1])
    pixmap.fill(Qt.GlobalColor.red)

    # Add some content to make it a valid image
    painter = QPainter(pixmap)
    painter.setPen(Qt.GlobalColor.blue)
    painter.drawRect(10, 10, size[0] - 20, size[1] - 20)
    painter.end()

    filepath = os.path.join(temp_dir, filename)
    pixmap.save(filepath, format)
    return filepath


class TestImageService:
    """Test cases for ImageService functionality."""

    def test_image_to_data_uri_png_input(self, qapp, image_service, temp_dir):
        """Test converting a PNG file to JPEG data URI."""
        # Create a test PNG file
        png_file = create_test_image(temp_dir, "test.png", "PNG")

        # Convert to data URI
        data_uri = image_service.image_to_data_uri(png_file)

        # Verify the result
        assert data_uri.startswith("data:image/jpeg;base64,")
        assert "base64," in data_uri

        # Verify the base64 part is valid
        base64_part = data_uri.split("base64,")[1]
        try:
            decoded = base64.b64decode(base64_part)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Failed to decode base64 data: {e}")

    def test_image_to_data_uri_bmp_input(self, qapp, image_service, temp_dir):
        """Test converting a BMP file to JPEG data URI."""
        # Create a test BMP file
        bmp_file = create_test_image(temp_dir, "test.bmp", "BMP")

        # Convert to data URI
        data_uri = image_service.image_to_data_uri(bmp_file)

        # Verify always outputs JPEG format
        assert data_uri.startswith("data:image/jpeg;base64,")

    def test_image_to_data_uri_already_jpeg(self, qapp, image_service, temp_dir):
        """Test converting a JPEG file (should still output JPEG)."""
        # Create a test JPEG file
        jpeg_file = create_test_image(temp_dir, "test.jpg", "JPEG")

        # Convert to data URI
        data_uri = image_service.image_to_data_uri(jpeg_file)

        # Verify outputs JPEG format
        assert data_uri.startswith("data:image/jpeg;base64,")

    def test_image_to_data_uri_nonexistent_file(self, image_service, temp_dir):
        """Test error handling for non-existent files."""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.png")

        with pytest.raises(ValueError):
            image_service.image_to_data_uri(nonexistent_file)

    def test_image_to_data_uri_invalid_file(self, image_service, temp_dir):
        """Test error handling for invalid image files."""
        # Create a text file with image extension
        invalid_file = os.path.join(temp_dir, "invalid.png")
        with open(invalid_file, "w") as f:
            f.write("This is not an image file")

        with pytest.raises(ValueError):
            image_service.image_to_data_uri(invalid_file)

    def test_data_uri_to_pixmap_valid(self, qapp, image_service, temp_dir):
        """Test converting a valid data URI to QPixmap."""
        # First create a data URI from a test image
        png_file = create_test_image(temp_dir, "test.png", "PNG")
        data_uri = image_service.image_to_data_uri(png_file)

        # Convert back to pixmap
        pixmap = image_service.data_uri_to_pixmap(data_uri)

        # Verify the result
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0

    def test_data_uri_to_pixmap_invalid(self, image_service):
        """Test data_uri_to_pixmap with invalid input."""
        # Test with invalid data URI
        invalid_uri = "data:image/jpeg;base64,invalid_base64_data"
        pixmap = image_service.data_uri_to_pixmap(invalid_uri)
        assert pixmap is None

    def test_data_uri_to_pixmap_empty(self, image_service):
        """Test data_uri_to_pixmap with empty input."""
        # Test with empty string
        pixmap = image_service.data_uri_to_pixmap("")
        assert pixmap is None

        # Test with None
        pixmap = image_service.data_uri_to_pixmap(None)
        assert pixmap is None

    def test_data_uri_to_pixmap_malformed(self, image_service):
        """Test data_uri_to_pixmap with malformed data URI."""
        # Test without base64 marker
        malformed_uri = "data:image/jpeg;notbase64"
        pixmap = image_service.data_uri_to_pixmap(malformed_uri)
        assert pixmap is None

    def test_round_trip_conversion(self, qapp, image_service, temp_dir):
        """Test full round-trip: image file -> data URI -> pixmap."""
        # Create a test image
        original_file = create_test_image(temp_dir, "original.png", "PNG", (50, 75))

        # Convert to data URI
        data_uri = image_service.image_to_data_uri(original_file)

        # Convert back to pixmap
        pixmap = image_service.data_uri_to_pixmap(data_uri)

        # Verify the pixmap is valid and has reasonable dimensions
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0

    def test_jpeg_compression_quality(self, qapp, image_service, temp_dir):
        """Test that JPEG compression is applied with reasonable quality."""
        # Create a larger test image for better compression testing
        large_file = create_test_image(temp_dir, "large.png", "PNG", (400, 300))

        # Convert to data URI
        data_uri = image_service.image_to_data_uri(large_file)

        # Decode the base64 to check size
        base64_part = data_uri.split("base64,")[1]
        jpeg_bytes = base64.b64decode(base64_part)

        # Verify we have a reasonable file size (not too large, not too small)
        assert len(jpeg_bytes) > 1000
        assert len(jpeg_bytes) < 100000  # Less than 100KB for a simple test image

    def test_pixmap_save_failure(self, mocker, image_service, temp_dir):
        """Test error handling when QPixmap.save() fails."""
        # Create a mock pixmap that fails to save
        mock_pixmap = mocker.MagicMock()
        mock_pixmap.isNull.return_value = False
        mock_pixmap.save.return_value = False  # Simulate save failure
        mocker.patch(
            "metaeditor_safetensors.services.image_service.QPixmap",
            return_value=mock_pixmap,
        )

        # Create a test file (content doesn't matter since we're mocking)
        test_file = os.path.join(temp_dir, "test.png")
        with open(test_file, "wb") as f:
            f.write(b"fake image data")

        # Test that conversion raises an appropriate error
        with pytest.raises(ValueError) as exc_info:
            image_service.image_to_data_uri(test_file)

        assert "Failed to convert image to JPEG format" in str(exc_info.value)
