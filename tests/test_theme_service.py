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

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_system_theme_detection_caching(self, mock_darkdetect, mock_get_package_root):
        """Test system theme detection caching functionality."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        
        theme_service = ThemeService(self.__class__.app)  # type: ignore
        
        # First call should call darkdetect
        mock_darkdetect.return_value = "Dark"
        result1 = theme_service._detect_system_theme(use_cache=True)
        self.assertEqual(result1, SystemTheme.DARK)
        
        # Second call should use cache and not call darkdetect again
        mock_darkdetect.return_value = "Light"  # Change value but should not be used
        result2 = theme_service._detect_system_theme(use_cache=True)
        self.assertEqual(result2, SystemTheme.DARK)  # Should still be dark from cache
        
        # Call with use_cache=False should call darkdetect again
        result3 = theme_service._detect_system_theme(use_cache=False)
        self.assertEqual(result3, SystemTheme.LIGHT)  # Should be light now

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_system_theme_detection_error_handling(self, mock_darkdetect, mock_get_package_root):
        """Test system theme detection error handling."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        
        theme_service = ThemeService(self.__class__.app)  # type: ignore
        
        # Test exception during detection
        mock_darkdetect.side_effect = Exception("System error")
        result = theme_service._detect_system_theme(use_cache=False)
        self.assertEqual(result, SystemTheme.UNKNOWN)

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_system_theme_detection_unexpected_value(self, mock_darkdetect, mock_get_package_root):
        """Test system theme detection with unexpected return value."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        
        theme_service = ThemeService(self.__class__.app)  # type: ignore
        
        # Test unexpected return value
        mock_darkdetect.return_value = "Purple"  # Unexpected value
        result = theme_service._detect_system_theme(use_cache=False)
        self.assertEqual(result, SystemTheme.UNKNOWN)

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_auto_theme_resolution_no_themes(self, mock_darkdetect, mock_get_package_root):
        """Test auto theme resolution when no themes are available."""
        # Point to empty directory
        empty_themes_dir = self.temp_dir / "empty" / "metaeditor_safetensors"
        empty_themes_dir.mkdir(parents=True)
        mock_get_package_root.return_value = empty_themes_dir
        
        mock_darkdetect.return_value = "Dark"
        theme_service = ThemeService(self.__class__.app)  # type: ignore
        
        # Should return empty string when no themes available
        result = theme_service._resolve_auto_theme()
        self.assertEqual(result, "")

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_themes_directory_not_found(self, mock_get_package_root):
        """Test initialization when themes directory doesn't exist."""
        # Point to non-existent directory
        mock_get_package_root.return_value = self.temp_dir / "nonexistent"
        
        theme_service = ThemeService(self.__class__.app)  # type: ignore
        
        # Should not crash and should have no themes except auto
        self.assertTrue(theme_service.has_theme("auto"))
        self.assertFalse(theme_service.has_theme("dark"))
        self.assertFalse(theme_service.has_theme("light"))

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_package_root_exception_handling(self, mock_get_package_root):
        """Test initialization when get_package_root raises exception."""
        mock_get_package_root.side_effect = Exception("Cannot determine package root")
        
        # Should not crash during initialization
        theme_service = ThemeService(self.__class__.app)  # type: ignore
        
        # Should still support auto theme (even if no actual themes available)
        self.assertTrue(theme_service.has_theme("auto"))

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_apply_theme_exception_handling(self, mock_get_package_root):
        """Test apply_theme method exception handling."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        
        theme_service = ThemeService(self.__class__.app)  # type: ignore
        
        # Mock theme to raise exception during QSS loading
        with patch.object(theme_service._available_themes['dark'], 'get_qss') as mock_get_qss:
            mock_get_qss.side_effect = Exception("QSS loading failed")
            
            result = theme_service.apply_theme("dark")
            self.assertFalse(result)

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_auto_theme_resolution_empty_result(self, mock_darkdetect, mock_get_package_root):
        """Test auto theme application when resolution returns empty string."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        
        theme_service = ThemeService(self.__class__.app)  # type: ignore
        
        # Mock _resolve_auto_theme to return empty string
        with patch.object(theme_service, '_resolve_auto_theme', return_value=""):
            result = theme_service.apply_theme("auto")
            self.assertFalse(result)

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_get_current_theme_initially_none(self, mock_get_package_root):
        """Test get_current_theme returns None initially."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        
        theme_service = ThemeService(self.__class__.app)  # type: ignore
        
        # Should be None initially
        self.assertIsNone(theme_service.get_current_theme())

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_live_reload_disabled_by_default(self, mock_get_package_root):
        """Test that live reload is disabled by default."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        
        # Ensure environment variable is not set
        with patch.dict('os.environ', {}, clear=True):
            theme_service = ThemeService(self.__class__.app)  # type: ignore
            
            # Should not have file watcher when live reload is disabled
            self.assertIsNone(theme_service._file_watcher)
            self.assertEqual(theme_service._watched_files, [])

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    def test_live_reload_enabled(self, mock_get_package_root):
        """Test that live reload can be enabled via environment variable."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        
        # Enable live reload via environment variable
        with patch.dict('os.environ', {'DEV_LIVE_STYLING': 'true'}):
            theme_service = ThemeService(self.__class__.app)  # type: ignore
            
            # Should have file watcher when live reload is enabled
            self.assertIsNotNone(theme_service._file_watcher)


if __name__ == "__main__":
    unittest.main()
