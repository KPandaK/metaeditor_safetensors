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
        assert theme_service._system_theme_thread is not None
        mock_thread.start.assert_called_once()

    def test_system_theme_callbacks(self, mocker, themes_dir):
        """Test system theme callback registration and notifications."""
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

        # Test callback registration
        callback_called = []

        def test_callback(theme):
            callback_called.append(theme)

        theme_service.add_system_theme_changed_callback(test_callback)

        # Test callback notification
        theme_service._notify_system_theme_changed("dark")
        assert len(callback_called) == 1
        assert callback_called[0] == "dark"

        # Test callback removal
        theme_service.remove_system_theme_changed_callback(test_callback)
        theme_service._notify_system_theme_changed("light")
        assert len(callback_called) == 1  # Should not have been called again

    def test_on_system_theme_changed_fires_callbacks(self, mocker, themes_dir):
        """Test system theme change handling fires callbacks."""
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

        # Add callback to track system theme changes
        callback_called = []

        def test_callback(theme):
            callback_called.append(theme)

        theme_service.add_system_theme_changed_callback(test_callback)

        # Simulate system theme change
        theme_service._on_system_theme_changed("Dark")

        # Should have called the callback
        assert len(callback_called) == 1
        assert callback_called[0] == "Dark"

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
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        theme_service = ThemeService()

        # Track observer calls
        observer_calls = []

        def test_observer(theme):
            observer_calls.append(theme)

        # Register observer
        theme_service.add_theme_changed_observer(test_observer)

        # Apply a theme - should trigger observer
        success = theme_service.apply_theme("dark")
        assert success, "Theme application should succeed"
        assert len(observer_calls) == 1
        assert observer_calls[0].config.theme_id == "dark"

        # Remove observer and test no more calls
        theme_service.remove_theme_changed_observer(test_observer)

        # Apply another theme - should not trigger removed observer
        theme_service.apply_theme("light")
        assert len(observer_calls) == 1, (
            "Observer calls should not increase after removal"
        )


def test_theme_service_no_package_root(mocker):
    """Test ThemeService when package root cannot be determined."""
    # Mock get_package_root to raise an exception
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        side_effect=Exception("Cannot determine package root"),
    )

    # Should not crash during initialization
    theme_service = ThemeService()

    # Should have no themes available
    assert len(theme_service._available_themes) == 0
    assert not theme_service.has_theme("dark")
    assert not theme_service.has_theme("light")


def test_theme_service_nonexistent_themes_directory(mocker, temp_dir):
    """Test ThemeService when themes directory doesn't exist."""
    # Point to non-existent themes directory
    nonexistent_root = temp_dir / "nonexistent"
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=nonexistent_root,
    )

    theme_service = ThemeService()

    # Should have no themes available
    assert len(theme_service._available_themes) == 0
    assert not theme_service.has_theme("dark")


def test_theme_loading_error_handling(mocker, temp_dir):
    """Test that theme loading errors are handled gracefully."""
    # Create valid theme directory structure
    package_root = temp_dir / "metaeditor_safetensors"
    themes_dir = package_root / "themes"
    themes_dir.mkdir(parents=True)

    # Create theme directory that will cause loading error
    error_theme_dir = themes_dir / "error_theme"
    error_theme_dir.mkdir()
    (error_theme_dir / "error.yaml").write_text(
        """
theme_id: "error_theme"
name: "Error Theme"
category: "dark"
""",
        encoding="utf-8",
    )

    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=package_root,
    )

    # Mock Theme.from_directory to raise an exception
    mocker.patch(
        "metaeditor_safetensors.models.theme.Theme.from_directory",
        side_effect=Exception("Theme loading error"),
    )

    theme_service = ThemeService()

    # Should handle the error and have no themes loaded
    assert len(theme_service._available_themes) == 0


def test_apply_theme_with_empty_available_themes(mocker, temp_dir):
    """Test applying theme when no themes are available."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=temp_dir / "empty",
    )

    theme_service = ThemeService()

    # Try to apply any theme - should fail
    assert not theme_service.apply_theme("dark")
    assert not theme_service.apply_theme("light")
    assert not theme_service.apply_theme("system")
    assert not theme_service.apply_theme("nonexistent")


def test_system_theme_resolution_no_matching_category(mocker, themes_dir):
    """Test system theme resolution when no theme matches detected category."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    # Mock system theme detection to return a category not matching our test themes
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.darkdetect.theme",
        return_value="Dark",
    )

    theme_service = ThemeService()

    # Mock the theme categories to not match the detected "dark" category
    # by patching the actual theme configs at runtime
    for theme_id, theme in theme_service._available_themes.items():
        # Use mocker to patch the category property
        mocker.patch.object(theme.config, "category", "other")

    # Should use fallback theme (first available) when no category matches
    result = theme_service._resolve_system_theme()
    assert result in theme_service._available_themes.keys()


def test_system_theme_resolution_empty_themes_list(mocker, temp_dir):
    """Test system theme resolution when no themes are available."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=temp_dir / "empty",
    )

    theme_service = ThemeService()

    # Should raise IndexError when trying to get fallback from empty list
    with pytest.raises(IndexError):
        theme_service._resolve_system_theme()


def test_apply_theme_exception_in_apply_internal(mocker, themes_dir):
    """Test apply_theme when _apply_theme_internal raises exception."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    theme_service = ThemeService()

    # Mock _apply_theme_internal to raise exception
    mocker.patch.object(
        theme_service,
        "_apply_theme_internal",
        side_effect=Exception("Internal apply error"),
    )

    # Should return False and not crash
    result = theme_service.apply_theme("dark")
    assert result is False


def test_file_watcher_update_no_current_theme(mocker, themes_dir):
    """Test file watcher update when no current theme is set."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    # Enable live reload
    mocker.patch.dict("os.environ", {"DEV_LIVE_STYLING": "true"})

    theme_service = ThemeService()

    # Should have file watcher but no watched files
    assert theme_service._file_watcher is not None
    assert theme_service._watched_files == []

    # Call update with no current theme
    theme_service._update_file_watchers()

    # Should still have no watched files
    assert theme_service._watched_files == []


def test_on_theme_file_changed_no_current_theme(mocker, themes_dir):
    """Test theme file change callback when no current theme is set."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    theme_service = ThemeService()

    # Should not crash when called with no current theme
    theme_service._on_theme_file_changed("dummy.qss")


def test_observer_callback_exception_handling(mocker, themes_dir):
    """Test that observer callback exceptions don't crash the service."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    theme_service = ThemeService()

    # Add observer that raises exception
    def failing_observer(theme):
        raise ValueError("Observer error")

    theme_service.add_theme_changed_observer(failing_observer)

    # Should not crash when applying theme
    result = theme_service.apply_theme("dark")
    assert result is True  # Theme application should still succeed


def test_remove_nonexistent_observer(mocker, themes_dir):
    """Test removing an observer that wasn't added."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    theme_service = ThemeService()

    def dummy_observer(theme):
        pass

    # Should not crash when removing non-existent observer
    theme_service.remove_theme_changed_observer(dummy_observer)


def test_darkdetect_unexpected_return_value(mocker, themes_dir):
    """Test handling of unexpected darkdetect return values."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    # Mock darkdetect to return unexpected value
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.darkdetect.theme",
        return_value="Purple",  # Unexpected value
    )

    theme_service = ThemeService()

    # Should fallback to LIGHT theme
    detected_theme = theme_service._detect_system_theme()
    assert detected_theme.value == "light"


def test_apply_default_theme(mocker, themes_dir):
    """Test applying the default theme."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    # Mock system theme detection
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.darkdetect.theme",
        return_value="Dark",
    )

    theme_service = ThemeService()

    # Should apply system theme by default
    result = theme_service.apply_default_theme()
    assert result is True
    assert theme_service.get_current_theme() is not None


def test_file_watcher_remove_paths_error(mocker, themes_dir):
    """Test file watcher gracefully handles removePaths errors."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    # Enable live reload
    mocker.patch.dict("os.environ", {"DEV_LIVE_STYLING": "true"})

    theme_service = ThemeService()

    # Apply a theme to get some watched files
    theme_service.apply_theme("dark")

    # Mock removePaths to raise exception
    if theme_service._file_watcher:
        mocker.patch.object(
            theme_service._file_watcher,
            "removePaths",
            side_effect=Exception("Remove paths error"),
        )

        # Should not crash when updating file watchers
        try:
            theme_service._update_file_watchers()
        except Exception:
            pytest.fail(
                "_update_file_watchers should handle removePaths errors gracefully"
            )


def test_theme_service_live_reload_env_var_variations(mocker, temp_dir):
    """Test different environment variable values for live reload."""
    package_root = temp_dir / "metaeditor_safetensors"
    package_root.mkdir(parents=True)

    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=package_root,
    )

    # Test "TRUE" (uppercase)
    mocker.patch.dict("os.environ", {"DEV_LIVE_STYLING": "TRUE"})
    theme_service1 = ThemeService()
    assert theme_service1._enable_live_reload is True

    # Test "True" (mixed case)
    mocker.patch.dict("os.environ", {"DEV_LIVE_STYLING": "True"})
    theme_service2 = ThemeService()
    assert theme_service2._enable_live_reload is True

    # Test "false"
    mocker.patch.dict("os.environ", {"DEV_LIVE_STYLING": "false"})
    theme_service3 = ThemeService()
    assert theme_service3._enable_live_reload is False

    # Test empty string
    mocker.patch.dict("os.environ", {"DEV_LIVE_STYLING": ""})
    theme_service4 = ThemeService()
    assert theme_service4._enable_live_reload is False
