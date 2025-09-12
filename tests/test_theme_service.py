"""
Unit tests for Theme Service
============================

Tests for theme service functionality including theme management,
system detection, auto resolution, and theme application.
"""

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from metaeditor_safetensors.services.theme_service import (  # type: ignore
    SystemTheme,
    ThemeService,
)


class TestThemeService(unittest.TestCase):
    """Test cases for ThemeService functionality."""

    @classmethod
    def setUpClass(cls):
        """Create a QApplication for all tests."""
        # Ensure QApplication instance exists
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

        # Verify we have a QApplication
        assert cls.app is not None
        assert isinstance(cls.app, QApplication)

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Suppress debug/info logging during tests for cleaner output
        logging.getLogger().setLevel(logging.ERROR)

        # Create temporary directory structure for themes
        self.temp_dir = Path(tempfile.mkdtemp())
        self.themes_dir = self.temp_dir / "metaeditor_safetensors" / "themes"
        self.themes_dir.mkdir(parents=True)

        # Create mock dark theme
        dark_theme_dir = self.themes_dir / "dark"
        dark_theme_dir.mkdir()
        (dark_theme_dir / "dark.yaml").write_text(
            """
name: "Dark Theme"
category: "dark"
qss_order:
  - "base.qss"
""",
            encoding="utf-8",
        )
        (dark_theme_dir / "base.qss").write_text(
            "/* Dark theme styles */", encoding="utf-8"
        )

        # Create mock light theme
        light_theme_dir = self.themes_dir / "light"
        light_theme_dir.mkdir()
        (light_theme_dir / "light.yaml").write_text(
            """
name: "Light Theme"
category: "light"
qss_order:
  - "base.qss"
""",
            encoding="utf-8",
        )
        (light_theme_dir / "base.qss").write_text(
            "/* Light theme styles */", encoding="utf-8"
        )

    def tearDown(self):
        """Clean up after each test."""
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_theme_service_initialization(self, mock_get_package_root):
        """Test ThemeService initialization and theme discovery."""
        # Mock the package root to point to our test package structure
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"

        # Create theme service
        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Check that themes were discovered
        self.assertTrue(theme_service.has_theme("dark"))
        self.assertTrue(theme_service.has_theme("light"))
        self.assertTrue(
            theme_service.has_theme("auto")
        )  # Auto should always be available

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_theme_validation_during_discovery(self, mock_get_package_root):
        """Test that only valid theme directories are loaded."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"

        # Create an invalid theme directory (no YAML)
        invalid_theme_dir = self.themes_dir / "invalid"
        invalid_theme_dir.mkdir()
        (invalid_theme_dir / "style.qss").write_text(
            "/* Invalid theme */", encoding="utf-8"
        )

        # Create theme service
        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Check that invalid theme was not loaded
        self.assertFalse(theme_service.has_theme("invalid"))
        self.assertTrue(theme_service.has_theme("dark"))
        self.assertTrue(theme_service.has_theme("light"))

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_system_theme_detection(self, mock_darkdetect, mock_get_package_root):
        """Test system theme detection functionality."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"

        # Test dark theme detection
        mock_darkdetect.return_value = "Dark"
        theme_service = ThemeService(self.__class__.app)  # type: ignore

        system_theme = theme_service._detect_system_theme(use_cache=False)
        self.assertEqual(system_theme, SystemTheme.DARK)

        # Test light theme detection
        mock_darkdetect.return_value = "Light"
        system_theme = theme_service._detect_system_theme(use_cache=False)
        self.assertEqual(system_theme, SystemTheme.LIGHT)

        # Test unknown theme
        mock_darkdetect.return_value = None
        system_theme = theme_service._detect_system_theme(use_cache=False)
        self.assertEqual(system_theme, SystemTheme.UNKNOWN)

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_auto_theme_resolution(self, mock_darkdetect, mock_get_package_root):
        """Test auto theme resolution based on system detection."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"

        # Test resolution to dark theme
        mock_darkdetect.return_value = "Dark"
        theme_service = ThemeService(self.__class__.app)  # type: ignore

        resolved_theme_id = theme_service._resolve_auto_theme()
        self.assertEqual(resolved_theme_id, "dark")

        # Test resolution to light theme - clear cache first
        mock_darkdetect.return_value = "Light"
        theme_service._cached_system_theme = None  # Clear cache
        resolved_theme_id = theme_service._resolve_auto_theme()
        self.assertEqual(resolved_theme_id, "light")

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_theme_application(self, mock_get_package_root):
        """Test applying themes to the application."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Test applying dark theme
        success = theme_service.apply_theme("dark")
        self.assertTrue(success)

        current_theme = theme_service.get_current_theme()
        self.assertIsNotNone(current_theme)
        if current_theme:
            self.assertEqual(current_theme.name, "Dark Theme")

        # Test applying light theme
        success = theme_service.apply_theme("light")
        self.assertTrue(success)

        current_theme = theme_service.get_current_theme()
        self.assertIsNotNone(current_theme)
        if current_theme:
            self.assertEqual(current_theme.name, "Light Theme")

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_auto_theme_application(self, mock_darkdetect, mock_get_package_root):
        """Test applying auto theme resolves to correct system theme."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        mock_darkdetect.return_value = "Dark"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Apply auto theme (should resolve to dark)
        success = theme_service.apply_theme("auto")
        self.assertTrue(success)

        current_theme = theme_service.get_current_theme()
        self.assertIsNotNone(current_theme)
        if current_theme:
            self.assertEqual(current_theme.name, "Dark Theme")

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_invalid_theme_application(self, mock_get_package_root):
        """Test applying non-existent theme returns False."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Try to apply non-existent theme
        success = theme_service.apply_theme("nonexistent")
        self.assertFalse(success)

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_theme_changed_signal(self, mock_darkdetect, mock_get_package_root):
        """Test that theme_changed signal is emitted when theme is applied."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        # Mock darkdetect to return "dark" so auto theme resolution works predictably
        mock_darkdetect.return_value = "dark"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Verify themes are loaded before testing signals
        self.assertTrue(
            theme_service.has_theme("dark"), "Dark theme should be available"
        )
        self.assertTrue(
            theme_service.has_theme("light"), "Light theme should be available"
        )

        # Connect to signal and track emissions
        signal_received = []
        theme_service.theme_changed.connect(
            lambda theme_id: signal_received.append(theme_id)
        )

        # Apply theme and check signal
        result = theme_service.apply_theme("dark")
        self.assertTrue(result, "Dark theme application should succeed")
        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0], "dark")

        # Apply auto theme and check signal (should emit "auto", not resolved theme)
        signal_received.clear()
        result = theme_service.apply_theme("auto")
        self.assertTrue(result, "Auto theme application should succeed")
        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0], "auto")

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_theme_directory_validation(self, mock_get_package_root):
        """Test is_valid_theme_directory validation method."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Test valid directory (has YAML)
        self.assertTrue(
            theme_service.is_valid_theme_directory(self.themes_dir / "dark")
        )

        # Test invalid directory (no YAML)
        invalid_dir = self.temp_dir / "invalid"
        invalid_dir.mkdir()
        (invalid_dir / "style.qss").write_text("/* styles */", encoding="utf-8")
        self.assertFalse(theme_service.is_valid_theme_directory(invalid_dir))

        # Test non-existent directory
        self.assertFalse(
            theme_service.is_valid_theme_directory(self.temp_dir / "nonexistent")
        )

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_has_theme_method(self, mock_get_package_root):
        """Test has_theme method for checking theme availability."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Test existing themes
        self.assertTrue(theme_service.has_theme("dark"))
        self.assertTrue(theme_service.has_theme("light"))
        self.assertTrue(theme_service.has_theme("auto"))

        # Test non-existent theme
        self.assertFalse(theme_service.has_theme("nonexistent"))


if __name__ == "__main__":
    unittest.main()
