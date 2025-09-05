"""
Unit tests for StylesheetService
================================

Tests for stylesheet management, including resource loading,
file-based loading, and live-reload functionality.
"""

import logging
import os
import shutil

# Import the service to test
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from PySide6.QtCore import QFile, QIODevice

# Import Qt classes for testing
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from metaeditor_safetensors.services.stylesheet_service import StylesheetService


class TestStylesheetService(unittest.TestCase):
    """Test cases for StylesheetService functionality."""

    def setUp(self):
        """Set up test fixtures and suppress logging during tests."""
        # Suppress debug/info logging during tests for cleaner output
        logging.getLogger('metaeditor_safetensors.services.stylesheet_service').setLevel(logging.WARNING)

        # Create a minimal QApplication for testing (if not already created)
        if not QApplication.instance():
            self.app = QApplication([])
            self.created_app = True
        else:
            self.app = QApplication.instance()
            self.created_app = False

        # Create temporary directory and file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_stylesheet = Path(self.temp_dir) / "test_style.qss"

        # Test stylesheet content
        self.test_stylesheet_content = """
QMainWindow {
    background-color: #f0f0f0;
}

QPushButton {
    background-color: #4CAF50;
    border: none;
    color: white;
    padding: 8px 16px;
    text-align: center;
    font-size: 14px;
}
"""

        # Write test stylesheet to file
        with open(self.temp_stylesheet, 'w', encoding='utf-8') as f:
            f.write(self.test_stylesheet_content)

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary files and directory
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

        # Reset application stylesheet
        self.app.setStyleSheet("")

        # Clean up QApplication if we created it
        if self.created_app:
            self.app.quit()

    @patch.dict('os.environ', {}, clear=True)
    def test_initialization_default_mode(self):
        """Test initialization with default settings (production mode)."""
        service = StylesheetService(
            self.app,
            ":/assets/style.qss",
            str(self.temp_stylesheet)
        )

        # Should not enable live reload by default
        self.assertFalse(service._enable_live_reload)
        self.assertEqual(service._resource_path, ":/assets/style.qss")
        self.assertEqual(service._filesystem_path, str(self.temp_stylesheet))

    @patch.dict('os.environ', {'DEV_LIVE_STYLING': 'true'})
    def test_initialization_dev_mode(self):
        """Test initialization with development mode enabled."""
        service = StylesheetService(
            self.app,
            ":/assets/style.qss",
            str(self.temp_stylesheet)
        )

        # Should enable live reload in dev mode
        self.assertTrue(service._enable_live_reload)

    @patch.dict('os.environ', {'DEV_LIVE_STYLING': 'false'})
    def test_initialization_dev_mode_disabled(self):
        """Test initialization with development mode explicitly disabled."""
        service = StylesheetService(
            self.app,
            ":/assets/style.qss",
            str(self.temp_stylesheet)
        )

        # Should not enable live reload when explicitly disabled
        self.assertFalse(service._enable_live_reload)

    def test_apply_from_file_success(self):
        """Test successfully loading stylesheet from filesystem."""
        service = StylesheetService(
            self.app,
            ":/assets/style.qss",
            str(self.temp_stylesheet)
        )

        # Apply from file
        service._apply_from_file()

        # Verify stylesheet was applied
        applied_stylesheet = self.app.styleSheet()
        self.assertEqual(applied_stylesheet.strip(), self.test_stylesheet_content.strip())

    def test_apply_from_file_not_found(self):
        """Test fallback behavior when stylesheet file is not found."""
        non_existent_file = str(Path(self.temp_dir) / "non_existent.qss")

        with patch.object(StylesheetService, '_apply_from_resources') as mock_apply_resources:
            service = StylesheetService(
                self.app,
                ":/assets/style.qss",
                non_existent_file
            )

            # Apply from non-existent file should fallback to resources
            service._apply_from_file()

            # Verify fallback was called
            mock_apply_resources.assert_called_once()

    def test_apply_from_file_no_filesystem_path(self):
        """Test fallback behavior when no filesystem path is provided."""
        with patch.object(StylesheetService, '_apply_from_resources') as mock_apply_resources:
            service = StylesheetService(
                self.app,
                ":/assets/style.qss",
                None  # No filesystem path
            )

            # Apply from file should fallback to resources
            service._apply_from_file()

            # Verify fallback was called
            mock_apply_resources.assert_called_once()

    @patch('metaeditor_safetensors.services.stylesheet_service.QFile')
    def test_apply_from_resources_success(self, mock_qfile_class):
        """Test successfully loading stylesheet from Qt resources."""
        # Mock QFile behavior
        mock_qfile = MagicMock()
        mock_qfile_class.return_value = mock_qfile
        mock_qfile.open.return_value = True
        mock_qfile.readAll.return_value.data.return_value.decode.return_value = self.test_stylesheet_content

        service = StylesheetService(
            self.app,
            ":/assets/style.qss"
        )

        # Apply from resources
        service._apply_from_resources()

        # Verify QFile was used correctly
        mock_qfile_class.assert_called_once_with(":/assets/style.qss")
        mock_qfile.open.assert_called_once_with(QIODevice.ReadOnly | QIODevice.Text)
        mock_qfile.close.assert_called_once()

        # Verify stylesheet was applied
        applied_stylesheet = self.app.styleSheet()
        self.assertEqual(applied_stylesheet, self.test_stylesheet_content)

    @patch('metaeditor_safetensors.services.stylesheet_service.QFile')
    def test_apply_from_resources_failure(self, mock_qfile_class):
        """Test handling of resource loading failure."""
        # Mock QFile failure
        mock_qfile = MagicMock()
        mock_qfile_class.return_value = mock_qfile
        mock_qfile.open.return_value = False  # Simulate failure

        service = StylesheetService(
            self.app,
            ":/assets/style.qss"
        )

        # Apply from resources (should not crash)
        service._apply_from_resources()

        # Verify QFile was attempted
        mock_qfile_class.assert_called_once_with(":/assets/style.qss")
        mock_qfile.open.assert_called_once_with(QIODevice.ReadOnly | QIODevice.Text)

        # close() should not be called on failure
        mock_qfile.close.assert_not_called()

    @patch.dict('os.environ', {'DEV_LIVE_STYLING': 'true'})
    @patch('metaeditor_safetensors.services.stylesheet_service.QFileSystemWatcher')
    def test_setup_file_watcher_success(self, mock_watcher_class):
        """Test setting up file watcher for live reload."""
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        service = StylesheetService(
            self.app,
            ":/assets/style.qss",
            str(self.temp_stylesheet)
        )

        # Setup file watcher
        service._setup_file_watcher()

        # Verify watcher was created and configured
        mock_watcher_class.assert_called_once_with([str(self.temp_stylesheet)])
        mock_watcher.fileChanged.connect.assert_called_once_with(service._on_file_changed)

    @patch.dict('os.environ', {'DEV_LIVE_STYLING': 'true'})
    def test_setup_file_watcher_no_file(self):
        """Test file watcher setup when file doesn't exist."""
        non_existent_file = str(Path(self.temp_dir) / "non_existent.qss")

        service = StylesheetService(
            self.app,
            ":/assets/style.qss",
            non_existent_file
        )

        # Setup file watcher (should not crash)
        service._setup_file_watcher()

        # Verify no watcher was created
        self.assertIsNone(service._watcher)

    @patch.dict('os.environ', {'DEV_LIVE_STYLING': 'true'})
    def test_apply_stylesheet_dev_mode(self):
        """Test apply_stylesheet in development mode."""
        with patch.object(StylesheetService, '_apply_from_file') as mock_apply_file, \
             patch.object(StylesheetService, '_setup_file_watcher') as mock_setup_watcher:

            service = StylesheetService(
                self.app,
                ":/assets/style.qss",
                str(self.temp_stylesheet)
            )

            # Apply stylesheet
            service.apply_stylesheet()

            # Verify development mode methods were called
            mock_apply_file.assert_called_once()
            mock_setup_watcher.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_apply_stylesheet_production_mode(self):
        """Test apply_stylesheet in production mode."""
        with patch.object(StylesheetService, '_apply_from_resources') as mock_apply_resources:

            service = StylesheetService(
                self.app,
                ":/assets/style.qss",
                str(self.temp_stylesheet)
            )

            # Apply stylesheet
            service.apply_stylesheet()

            # Verify production mode method was called
            mock_apply_resources.assert_called_once()

    def test_on_file_changed(self):
        """Test file change handler for live reload."""
        with patch.object(StylesheetService, '_apply_from_file') as mock_apply_file:

            service = StylesheetService(
                self.app,
                ":/assets/style.qss",
                str(self.temp_stylesheet)
            )

            # Simulate file change
            service._on_file_changed()

            # Verify stylesheet was reloaded
            mock_apply_file.assert_called_once()

    @patch.dict('os.environ', {'DEV_LIVE_STYLING': 'true'})
    def test_full_dev_workflow(self):
        """Test complete development workflow with file watching."""
        service = StylesheetService(
            self.app,
            ":/assets/style.qss",
            str(self.temp_stylesheet)
        )

        # Apply initial stylesheet
        service.apply_stylesheet()

        # Verify initial content was loaded
        self.assertIn("background-color: #f0f0f0", self.app.styleSheet())

        # Modify the stylesheet file
        modified_content = "QMainWindow { background-color: #ff0000; }"
        with open(self.temp_stylesheet, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        # Simulate file change event
        service._on_file_changed()

        # Verify new content was loaded
        self.assertEqual(self.app.styleSheet(), modified_content)


if __name__ == '__main__':
    unittest.main()
