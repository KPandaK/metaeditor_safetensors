"""
Unit tests for Theme Service System Monitoring
==============================================

Tests for system theme change monitoring functionality including
thread management, signal handling, and cleanup.
"""

import logging
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from PySide6.QtWidgets import QApplication

from metaeditor_safetensors.services.theme_service import (  # type: ignore
    SystemTheme,
    ThemeService,
)


class TestThemeMonitoring(unittest.TestCase):
    """Test cases for Theme Service system monitoring functionality."""

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
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_monitoring_activation_with_auto_theme(self, mock_darkdetect, mock_get_package_root):
        """Test that system theme monitoring starts when auto theme is applied."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        mock_darkdetect.return_value = "dark"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Initially, monitoring should not be active
        self.assertFalse(theme_service.is_monitoring_system_theme())
        self.assertEqual(theme_service.get_current_theme_preference(), None)

        # Apply auto theme - monitoring should start
        with patch("metaeditor_safetensors.services.theme_service.darkdetect.listener") as mock_listener:
            # Make the listener mock block indefinitely to simulate real behavior
            mock_listener.side_effect = lambda callback: threading.Event().wait()
            
            result = theme_service.apply_theme("auto")
            self.assertTrue(result)
            
            # Give the thread a moment to start and set the monitoring flag
            time.sleep(0.1)
            
            self.assertTrue(theme_service.is_monitoring_system_theme())
            self.assertEqual(theme_service.get_current_theme_preference(), "auto")

        theme_service.cleanup()

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_monitoring_deactivation_with_specific_theme(self, mock_darkdetect, mock_get_package_root):
        """Test that system theme monitoring stops when specific theme is applied."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        mock_darkdetect.return_value = "dark"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Apply auto theme first to start monitoring
        with patch("metaeditor_safetensors.services.theme_service.darkdetect.listener") as mock_listener:
            # Make the listener mock block indefinitely to simulate real behavior
            mock_listener.side_effect = lambda callback: threading.Event().wait()
            
            theme_service.apply_theme("auto")
            time.sleep(0.1)
            self.assertTrue(theme_service.is_monitoring_system_theme())

        # Apply specific theme - monitoring should stop
        result = theme_service.apply_theme("dark")
        self.assertTrue(result)
        self.assertFalse(theme_service.is_monitoring_system_theme())
        self.assertEqual(theme_service.get_current_theme_preference(), "dark")

        theme_service.cleanup()

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_system_theme_changed_signal_emission(self, mock_darkdetect, mock_get_package_root):
        """Test that system_theme_changed signal is emitted correctly."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        mock_darkdetect.return_value = "dark"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Set up signal capture
        signal_received = []
        theme_service.system_theme_changed.connect(
            lambda theme_name: signal_received.append(theme_name)
        )

        # Simulate system theme change callback directly
        theme_service.system_theme_changed.emit("Light")
        
        # Process any pending Qt events
        self.__class__.app.processEvents()

        # Check that signal was received
        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0], "Light")

        theme_service.cleanup()

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_system_theme_change_with_auto_theme_active(self, mock_darkdetect, mock_get_package_root):
        """Test theme reapplication when system theme changes with auto theme active."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        
        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Mock apply_theme to track calls
        original_apply = theme_service.apply_theme
        theme_service.apply_theme = MagicMock(side_effect=original_apply)

        # Start with dark system theme
        mock_darkdetect.return_value = "dark"
        
        with patch("metaeditor_safetensors.services.theme_service.darkdetect.listener"):
            # Apply auto theme
            result = theme_service.apply_theme("auto")
            self.assertTrue(result)
            self.assertEqual(theme_service.get_current_theme_preference(), "auto")

            # Simulate system theme change to light
            mock_darkdetect.return_value = "light"
            theme_service._on_system_theme_changed("Light")

            # apply_theme should have been called again with "auto"
            expected_calls = [call("auto"), call("auto")]
            theme_service.apply_theme.assert_has_calls(expected_calls)

        theme_service.cleanup()

    @patch("metaeditor_safetensors.services.theme_service.get_package_root") 
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_system_theme_change_ignored_when_not_auto(self, mock_darkdetect, mock_get_package_root):
        """Test that system theme changes are ignored when not using auto theme."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        mock_darkdetect.return_value = "dark"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Apply specific theme (not auto)
        result = theme_service.apply_theme("dark")
        self.assertTrue(result)
        self.assertEqual(theme_service.get_current_theme_preference(), "dark")

        # Mock apply_theme to track calls
        original_apply = theme_service.apply_theme
        theme_service.apply_theme = MagicMock(side_effect=original_apply)

        # Simulate system theme change
        theme_service._on_system_theme_changed("Light")

        # apply_theme should not have been called since we're not using auto theme
        theme_service.apply_theme.assert_not_called()

        theme_service.cleanup()

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_cleanup_stops_monitoring(self, mock_darkdetect, mock_get_package_root):
        """Test that cleanup properly stops theme monitoring."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        mock_darkdetect.return_value = "dark"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Start monitoring
        with patch("metaeditor_safetensors.services.theme_service.darkdetect.listener") as mock_listener:
            # Make the listener mock block indefinitely to simulate real behavior
            mock_listener.side_effect = lambda callback: threading.Event().wait()
            
            theme_service.apply_theme("auto")
            time.sleep(0.1)
            self.assertTrue(theme_service.is_monitoring_system_theme())

        # Cleanup should stop monitoring
        theme_service.cleanup()
        self.assertFalse(theme_service.is_monitoring_system_theme())

    @patch("metaeditor_safetensors.services.theme_service.get_package_root")
    @patch("metaeditor_safetensors.services.theme_service.darkdetect.theme")
    def test_monitoring_thread_safety(self, mock_darkdetect, mock_get_package_root):
        """Test thread safety of monitoring activation/deactivation."""
        mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
        mock_darkdetect.return_value = "dark"

        theme_service = ThemeService(self.__class__.app)  # type: ignore

        # Test multiple rapid start/stop cycles
        with patch("metaeditor_safetensors.services.theme_service.darkdetect.listener") as mock_listener:
            # Make the listener mock block indefinitely to simulate real behavior
            mock_listener.side_effect = lambda callback: threading.Event().wait()
            
            for i in range(5):
                theme_service.apply_theme("auto")
                time.sleep(0.01)  # Very brief pause
                theme_service.apply_theme("dark")
                time.sleep(0.01)

        # Should end up with monitoring stopped
        self.assertFalse(theme_service.is_monitoring_system_theme())
        
        theme_service.cleanup()

    def test_getter_methods(self):
        """Test new getter methods for theme preference and monitoring state."""
        with patch("metaeditor_safetensors.services.theme_service.get_package_root") as mock_get_package_root:
            mock_get_package_root.return_value = self.temp_dir / "metaeditor_safetensors"
            
            theme_service = ThemeService(self.__class__.app)  # type: ignore

            # Initially no preference set
            self.assertIsNone(theme_service.get_current_theme_preference())
            self.assertFalse(theme_service.is_monitoring_system_theme())

            theme_service.cleanup()


if __name__ == "__main__":
    unittest.main()