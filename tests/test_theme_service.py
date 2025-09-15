import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from metaeditor_safetensors.services.theme_service import ThemeService


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
    # Create the exact path structure that get_package_root would return
    package_root = temp_dir / "metaeditor_safetensors"
    themes_dir = package_root / "themes"
    themes_dir.mkdir(parents=True)

    # Create mock dark theme
    dark_theme_dir = themes_dir / "dark"
    dark_theme_dir.mkdir()
    (dark_theme_dir / "dark.yaml").write_text(
        """
theme_id: "dark"
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
theme_id: "light"
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

    def test_theme_service_initialization(self, mocker, themes_dir):
        """Test ThemeService initialization and theme discovery."""
        # Mock the package root to point to our test package structure
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Mock threading to prevent actual thread creation
        mocker.patch("threading.Thread")
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        )

        # Create theme service
        theme_service = ThemeService()

        # Check that themes were discovered
        assert theme_service.has_theme("dark")
        assert theme_service.has_theme("light")

    def test_system_theme_detection(self, mocker, temp_dir):
        """Test system theme detection functionality."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )
        mock_darkdetect = mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme"
        )

        # Mock threading to prevent actual thread creation
        mocker.patch("threading.Thread")
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        )

        # Test dark theme detection
        mock_darkdetect.return_value = "Dark"
        theme_service = ThemeService()

        system_theme = theme_service._detect_system_theme()
        assert system_theme.value == "dark"

        # Test light theme detection
        mock_darkdetect.return_value = "Light"
        system_theme = theme_service._detect_system_theme()
        assert system_theme.value == "light"

        # Test unknown theme
        mock_darkdetect.return_value = None
        system_theme = theme_service._detect_system_theme()
        assert system_theme.value == "light"

    def test_theme_application(self, mocker, themes_dir):
        """Test applying themes to the application."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Mock threading to prevent actual thread creation
        mocker.patch("threading.Thread")
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        )

        theme_service = ThemeService()

        # Test applying dark theme
        success = theme_service.apply_theme("dark")
        assert success

        current_theme = theme_service.get_current_theme()
        assert current_theme is not None
        if current_theme:
            assert current_theme.config.name == "Dark Theme"

        # Test applying light theme
        success = theme_service.apply_theme("light")
        assert success

        current_theme = theme_service.get_current_theme()
        assert current_theme is not None
        if current_theme:
            assert current_theme.config.name == "Light Theme"


class TestThemeServiceSystemMonitoring:
    """Test cases for ThemeService system theme monitoring functionality."""

    def test_start_system_theme_monitoring(self, mocker, themes_dir):
        """Test starting system theme monitoring."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Mock threading.Thread to prevent actual thread creation
        mock_thread = Mock()
        mock_darkdetect_listener = Mock()
        mocker.patch("threading.Thread", return_value=mock_thread)
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener",
            mock_darkdetect_listener,
        )

        theme_service = ThemeService()

        # Should have started monitoring by default
        assert theme_service._system_theme_monitoring is True
        mock_thread.start.assert_called_once()

    def test_user_theme_preference_methods(self, mocker, themes_dir):
        """Test user theme preference getter and setter."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Mock threading to prevent actual thread creation
        mocker.patch("threading.Thread")
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        )

        theme_service = ThemeService()

        # Default should be "system"
        assert theme_service.get_user_theme_preference() == "system"

        # Test setting preference
        theme_service.set_user_theme_preference("dark")
        assert theme_service.get_user_theme_preference() == "dark"

    def test_on_system_theme_changed_with_system_preference(self, mocker, themes_dir):
        """Test system theme change handling when preference is 'system'."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Mock threading to prevent actual thread creation
        mocker.patch("threading.Thread")
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        )

        theme_service = ThemeService()

        # Mock apply_theme
        apply_mock = Mock(return_value=True)
        mocker.patch.object(theme_service, "apply_theme", apply_mock)

        # Simulate system theme change
        theme_service._on_system_theme_changed("Dark")

        # Should have applied system theme
        apply_mock.assert_called_once_with("system")

    def test_on_system_theme_changed_with_non_system_preference(
        self, mocker, themes_dir
    ):
        """Test system theme change handling when preference is not 'system'."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Mock threading to prevent actual thread creation
        mocker.patch("threading.Thread")
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        )

        theme_service = ThemeService()
        theme_service.set_user_theme_preference("dark")

        # Mock apply_theme
        apply_mock = Mock()
        mocker.patch.object(theme_service, "apply_theme", apply_mock)

        # Simulate system theme change
        theme_service._on_system_theme_changed("Dark")

        # Should not have applied theme since preference is not "system"
        apply_mock.assert_not_called()

    def test_shutdown_stops_monitoring(self, mocker, themes_dir):
        """Test shutdown stops system monitoring."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Mock threading to prevent actual thread creation
        mocker.patch("threading.Thread")
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        )

        theme_service = ThemeService()

        # Mock stop monitoring
        stop_mock = Mock()
        mocker.patch.object(theme_service, "_stop_system_theme_monitoring", stop_mock)

        theme_service.shutdown()

        stop_mock.assert_called_once()

    def test_exception_handling_in_monitoring_methods(self, mocker, themes_dir):
        """Test exception handling in monitoring methods."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Mock threading to raise exception
        mocker.patch("threading.Thread", side_effect=Exception("Thread error"))
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        )

        # Should not raise exception during initialization
        try:
            theme_service = ThemeService()
            assert (
                not theme_service._system_theme_monitoring
            )  # Should be False due to error
        except Exception:
            pytest.fail("Exception handling should prevent exceptions from propagating")
