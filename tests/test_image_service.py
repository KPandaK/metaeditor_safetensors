"""
Tests for the ImageService module.

This module tests the image conversion functionality of the ImageService,
including conversion to JPEG format and data URI generation.
"""

import base64
import os
import shutil

# Add the project root to the path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from metaeditor_safetensors.services.image_service import ImageService


class TestImageService(unittest.TestCase):
    """Test cases for ImageService functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for Qt functionality."""
        # Check if QApplication already exists
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures."""
        self.service = ImageService()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_image(self, filename: str, format: str = 'PNG', size: tuple = (100, 100)) -> str:
        """
        Create a test image file for testing.

        Args:
            filename: Name of the file to create
            format: Image format (PNG, JPEG, etc.)
            size: Image size as (width, height)

        Returns:
            Full path to the created test image
        """
        # Create a simple test image
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.red)  # Fill with red color

        # Add some content to make it a valid image
        painter = QPainter(pixmap)
        painter.setPen(Qt.blue)
        painter.drawRect(10, 10, size[0]-20, size[1]-20)
        painter.end()

        filepath = os.path.join(self.temp_dir, filename)
        pixmap.save(filepath, format)
        return filepath

    def test_image_to_data_uri_png_input(self):
        """Test converting a PNG file to JPEG data URI."""
        # Create a test PNG file
        png_file = self.create_test_image('test.png', 'PNG')

        # Convert to data URI
        data_uri = self.service.image_to_data_uri(png_file)

        # Verify the result
        self.assertTrue(data_uri.startswith('data:image/jpeg;base64,'))
        self.assertIn('base64,', data_uri)

        # Verify the base64 part is valid
        base64_part = data_uri.split('base64,')[1]
        try:
            decoded = base64.b64decode(base64_part)
            self.assertGreater(len(decoded), 0)
        except Exception as e:
            self.fail(f"Failed to decode base64 data: {e}")

    def test_image_to_data_uri_bmp_input(self):
        """Test converting a BMP file to JPEG data URI."""
        # Create a test BMP file
        bmp_file = self.create_test_image('test.bmp', 'BMP')

        # Convert to data URI
        data_uri = self.service.image_to_data_uri(bmp_file)

        # Verify always outputs JPEG format
        self.assertTrue(data_uri.startswith('data:image/jpeg;base64,'))

    def test_image_to_data_uri_already_jpeg(self):
        """Test converting a JPEG file (should still output JPEG)."""
        # Create a test JPEG file
        jpeg_file = self.create_test_image('test.jpg', 'JPEG')

        # Convert to data URI
        data_uri = self.service.image_to_data_uri(jpeg_file)

        # Verify outputs JPEG format
        self.assertTrue(data_uri.startswith('data:image/jpeg;base64,'))

    def test_image_to_data_uri_nonexistent_file(self):
        """Test error handling for non-existent files."""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.png')

        with self.assertRaises(ValueError):
            self.service.image_to_data_uri(nonexistent_file)

    def test_image_to_data_uri_invalid_file(self):
        """Test error handling for invalid image files."""
        # Create a text file with image extension
        invalid_file = os.path.join(self.temp_dir, 'invalid.png')
        with open(invalid_file, 'w') as f:
            f.write('This is not an image file')

        with self.assertRaises(ValueError):
            self.service.image_to_data_uri(invalid_file)

    def test_data_uri_to_pixmap_valid(self):
        """Test converting a valid data URI to QPixmap."""
        # First create a data URI from a test image
        png_file = self.create_test_image('test.png', 'PNG')
        data_uri = self.service.image_to_data_uri(png_file)

        # Convert back to pixmap
        pixmap = self.service.data_uri_to_pixmap(data_uri)

        # Verify the result
        self.assertIsNotNone(pixmap)
        self.assertFalse(pixmap.isNull())
        self.assertGreater(pixmap.width(), 0)
        self.assertGreater(pixmap.height(), 0)

    def test_data_uri_to_pixmap_invalid(self):
        """Test data_uri_to_pixmap with invalid input."""
        # Test with invalid data URI
        invalid_uri = "data:image/jpeg;base64,invalid_base64_data"
        pixmap = self.service.data_uri_to_pixmap(invalid_uri)
        self.assertIsNone(pixmap)

    def test_data_uri_to_pixmap_empty(self):
        """Test data_uri_to_pixmap with empty input."""
        # Test with empty string
        pixmap = self.service.data_uri_to_pixmap("")
        self.assertIsNone(pixmap)

        # Test with None
        pixmap = self.service.data_uri_to_pixmap(None)
        self.assertIsNone(pixmap)

    def test_data_uri_to_pixmap_malformed(self):
        """Test data_uri_to_pixmap with malformed data URI."""
        # Test without base64 marker
        malformed_uri = "data:image/jpeg;notbase64"
        pixmap = self.service.data_uri_to_pixmap(malformed_uri)
        self.assertIsNone(pixmap)

    def test_round_trip_conversion(self):
        """Test full round-trip: image file -> data URI -> pixmap."""
        # Create a test image
        original_file = self.create_test_image('original.png', 'PNG', (50, 75))

        # Convert to data URI
        data_uri = self.service.image_to_data_uri(original_file)

        # Convert back to pixmap
        pixmap = self.service.data_uri_to_pixmap(data_uri)

        # Verify the pixmap is valid and has reasonable dimensions
        self.assertIsNotNone(pixmap)
        self.assertFalse(pixmap.isNull())
        # Note: Dimensions might be slightly different due to JPEG compression
        self.assertGreater(pixmap.width(), 0)
        self.assertGreater(pixmap.height(), 0)

    def test_jpeg_compression_quality(self):
        """Test that JPEG compression is applied with reasonable quality."""
        # Create a larger test image for better compression testing
        large_file = self.create_test_image('large.png', 'PNG', (400, 300))

        # Convert to data URI
        data_uri = self.service.image_to_data_uri(large_file)

        # Decode the base64 to check size
        base64_part = data_uri.split('base64,')[1]
        jpeg_bytes = base64.b64decode(base64_part)

        # Verify we have a reasonable file size (not too large, not too small)
        self.assertGreater(len(jpeg_bytes), 1000)  # At least 1KB
        self.assertLess(len(jpeg_bytes), 100000)   # Less than 100KB for a simple test image

    @patch('metaeditor_safetensors.services.image_service.QPixmap')
    def test_pixmap_save_failure(self, mock_qpixmap_class):
        """Test error handling when QPixmap.save() fails."""
        # Create a mock pixmap that fails to save
        mock_pixmap = MagicMock()
        mock_pixmap.isNull.return_value = False
        mock_pixmap.save.return_value = False  # Simulate save failure
        mock_qpixmap_class.return_value = mock_pixmap

        # Create a test file (content doesn't matter since we're mocking)
        test_file = os.path.join(self.temp_dir, 'test.png')
        with open(test_file, 'wb') as f:
            f.write(b'fake image data')

        # Test that conversion raises an appropriate error
        with self.assertRaises(ValueError) as context:
            self.service.image_to_data_uri(test_file)

        self.assertIn("Failed to convert image to JPEG format", str(context.exception))


if __name__ == '__main__':
    unittest.main()
