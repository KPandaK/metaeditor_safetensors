"""
Unit tests for Theme Service
============================

Tests for theme service functionality including theme management,
system detection, auto resolution, and theme application.
"""

import logging
import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from metaeditor_safetensors.services.theme_service import (
    SystemTheme,
    ThemeService,
)


@pytest.fixture(scope="class")
def qapp():
    """Create a QApplication for all tests."""
    # Ensure QApplication instance exists
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()

    # Verify we have a QApplication
    assert app is not None
    assert isinstance(app, QApplication)
    yield app


@pytest.fixture
def temp_dir():
    """Set up test fixtures before each test method."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Clean up after each test
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def themes_dir(temp_dir):
    """Create temporary directory structure for themes."""
    themes_dir = temp_dir / "metaeditor_safetensors" / "themes"
    themes_dir.mkdir(parents=True)

    # Create mock dark theme
    dark_theme_dir = themes_dir / "dark"
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
    light_theme_dir = themes_dir / "light"
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

    return themes_dir


@pytest.fixture(autouse=True)
def suppress_logging():
    """Suppress debug/info logging during tests for cleaner output."""
    logging.getLogger().setLevel(logging.ERROR)


class TestThemeService:
    """Test cases for ThemeService functionality."""

    def test_theme_service_initialization(self, mocker, qapp, temp_dir, themes_dir):
        """Test ThemeService initialization and theme discovery."""
        # Mock the package root to point to our test package structure
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )

        # Create theme service
        theme_service = ThemeService(qapp)

        # Check that themes were discovered
        assert theme_service.has_theme("dark")
        assert theme_service.has_theme("light")
        assert theme_service.has_theme("auto")  # Auto should always be available

    def test_theme_validation_during_discovery(
        self, mocker, qapp, temp_dir, themes_dir
    ):
        """Test that only valid theme directories are loaded."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )

        # Create an invalid theme directory (no YAML)
        invalid_theme_dir = themes_dir / "invalid"
        invalid_theme_dir.mkdir()
        (invalid_theme_dir / "style.qss").write_text(
            "/* Invalid theme */", encoding="utf-8"
        )

        # Create theme service
        theme_service = ThemeService(qapp)

        # Check that invalid theme was not loaded
        assert not theme_service.has_theme("invalid")
        assert theme_service.has_theme("dark")
        assert theme_service.has_theme("light")

    def test_system_theme_detection(self, mocker, qapp, temp_dir):
        """Test system theme detection functionality."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )
        mock_darkdetect = mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme"
        )

        # Test dark theme detection
        mock_darkdetect.return_value = "Dark"
        theme_service = ThemeService(qapp)

        system_theme = theme_service._detect_system_theme(use_cache=False)
        assert system_theme == SystemTheme.DARK

        # Test light theme detection
        mock_darkdetect.return_value = "Light"
        system_theme = theme_service._detect_system_theme(use_cache=False)
        assert system_theme == SystemTheme.LIGHT

        # Test unknown theme
        mock_darkdetect.return_value = None
        system_theme = theme_service._detect_system_theme(use_cache=False)
        assert system_theme == SystemTheme.UNKNOWN

    def test_auto_theme_resolution(self, mocker, qapp, themes_dir):
        """Test auto theme resolution based on system detection."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        mock_darkdetect = mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme"
        )

        # Test resolution to dark theme
        mock_darkdetect.return_value = "Dark"
        theme_service = ThemeService(qapp)

        resolved_theme_id = theme_service._resolve_auto_theme()
        assert resolved_theme_id == "dark"

        # Test resolution to light theme - clear cache first
        mock_darkdetect.return_value = "Light"
        theme_service._cached_system_theme = None  # Clear cache
        resolved_theme_id = theme_service._resolve_auto_theme()
        assert resolved_theme_id == "light"

    def test_theme_application(self, mocker, qapp, themes_dir):
        """Test applying themes to the application."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        theme_service = ThemeService(qapp)

        # Test applying dark theme
        success = theme_service.apply_theme("dark")
        assert success

        current_theme = theme_service.get_current_theme()
        assert current_theme is not None
        if current_theme:
            assert current_theme.name == "Dark Theme"

        # Test applying light theme
        success = theme_service.apply_theme("light")
        assert success

        current_theme = theme_service.get_current_theme()
        assert current_theme is not None
        if current_theme:
            assert current_theme.name == "Light Theme"

    def test_auto_theme_application(self, mocker, qapp, themes_dir):
        """Test applying auto theme resolves to correct system theme."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="Dark",
        )

        theme_service = ThemeService(qapp)

        # Apply auto theme (should resolve to dark)
        success = theme_service.apply_theme("auto")
        assert success

        current_theme = theme_service.get_current_theme()
        assert current_theme is not None
        if current_theme:
            assert current_theme.name == "Dark Theme"

    def test_invalid_theme_application(self, mocker, qapp, temp_dir):
        """Test applying non-existent theme returns False."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )

        theme_service = ThemeService(qapp)

        # Try to apply non-existent theme
        success = theme_service.apply_theme("nonexistent")
        assert not success

    def test_theme_changed_signal(self, mocker, qapp, temp_dir, themes_dir):
        """Test that theme_changed signal is emitted when theme is applied."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )
        # Mock darkdetect to return "dark" so auto theme resolution works predictably
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="dark",
        )

        theme_service = ThemeService(qapp)

        # Verify themes are loaded before testing signals
        assert theme_service.has_theme("dark"), "Dark theme should be available"
        assert theme_service.has_theme("light"), "Light theme should be available"

        # Connect to signal and track emissions
        signal_received = []
        theme_service.theme_changed.connect(
            lambda theme_id: signal_received.append(theme_id)
        )

        # Apply theme and check signal
        result = theme_service.apply_theme("dark")
        assert result, "Dark theme application should succeed"
        assert len(signal_received) == 1
        assert signal_received[0] == "dark"

        # Apply auto theme and check signal (should emit "auto", not resolved theme)
        signal_received.clear()
        result = theme_service.apply_theme("auto")
        assert result, "Auto theme application should succeed"
        assert len(signal_received) == 1
        assert signal_received[0] == "auto"

    def test_theme_directory_validation(self, mocker, qapp, temp_dir, themes_dir):
        """Test is_valid_theme_directory validation method."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )

        theme_service = ThemeService(qapp)

        # Test valid directory (has YAML)
        assert theme_service.is_valid_theme_directory(themes_dir / "dark")

        # Test invalid directory (no YAML)
        invalid_dir = temp_dir / "invalid"
        invalid_dir.mkdir()
        (invalid_dir / "style.qss").write_text("/* styles */", encoding="utf-8")
        assert not theme_service.is_valid_theme_directory(invalid_dir)

        # Test non-existent directory
        assert not theme_service.is_valid_theme_directory(temp_dir / "nonexistent")

    def test_has_theme_method(self, mocker, qapp, themes_dir):
        """Test has_theme method for checking theme availability."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        theme_service = ThemeService(qapp)

        # Test existing themes
        assert theme_service.has_theme("dark")
        assert theme_service.has_theme("light")
        assert theme_service.has_theme("auto")

        # Test non-existent theme
        assert not theme_service.has_theme("nonexistent")
