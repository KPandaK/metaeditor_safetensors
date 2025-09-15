import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from metaeditor_safetensors.services.theme_service import ThemeService, SystemThemeMonitor


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

    def test_apply_theme_internal_error(self, mocker, themes_dir):
        """Test _apply_theme_internal handles QSS loading errors gracefully."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        theme_service = ThemeService()
        theme = theme_service._available_themes.get("dark")
        if theme:
            # Mock the internal method to raise an exception during theme application
            mocker.patch.object(
                theme_service,
                "_notify_theme_changed",
                side_effect=Exception("Notification error"),
            )
            result = theme_service._apply_theme_internal(theme)
            assert result is False

    def test_on_theme_file_changed_reapplies_theme(self, mocker, themes_dir):
        """Test _on_theme_file_changed triggers theme re-application."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        theme_service = ThemeService()

        # Apply a theme first so we have a current theme
        theme_service.apply_theme("dark")
        theme = theme_service._current_theme

        # Patch _apply_theme_internal to track calls
        apply_theme_mock = mocker.patch.object(theme_service, "_apply_theme_internal")
        theme_service._on_theme_file_changed("dummy.qss")
        apply_theme_mock.assert_called_once_with(theme)

    def test_is_valid_theme_directory_edge_cases(self, mocker, temp_dir):
        """Test is_valid_theme_directory with non-directory and missing YAML."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )
        theme_service = ThemeService()
        # Non-existent path
        assert not theme_service.is_valid_theme_directory(temp_dir / "not_a_dir")
        # File instead of directory
        file_path = temp_dir / "file.txt"
        file_path.write_text("not a dir")
        assert not theme_service.is_valid_theme_directory(file_path)
        # Directory with no YAML
        no_yaml_dir = temp_dir / "no_yaml"
        no_yaml_dir.mkdir()
        assert not theme_service.is_valid_theme_directory(no_yaml_dir)

    def test_setup_file_watchers_with_and_without_qss(self, mocker, themes_dir):
        """Test _setup_file_watchers with and without QSS files."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        # Enable live reload
        mocker.patch.dict("os.environ", {"DEV_LIVE_STYLING": "true"})
        theme_service = ThemeService()

        # With live reload enabled, file watcher should be created
        assert theme_service._file_watcher is not None
        # But no files should be watched initially since no theme is applied
        assert theme_service._watched_files == []

    def test_theme_service_initialization(self, mocker, themes_dir):
        """Test ThemeService initialization and theme discovery."""
        # Mock the package root to point to our test package structure
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Create theme service
        theme_service = ThemeService()

        # Check that themes were discovered
        assert theme_service.has_theme("dark")
        assert theme_service.has_theme("light")

    def test_theme_validation_during_discovery(self, mocker, themes_dir):
        """Test that only valid theme directories are loaded."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Create an invalid theme directory (no YAML)
        invalid_theme_dir = themes_dir / "invalid"
        invalid_theme_dir.mkdir()
        (invalid_theme_dir / "style.qss").write_text(
            "/* Invalid theme */", encoding="utf-8"
        )

        # Create theme service
        theme_service = ThemeService()

        # Check that invalid theme was not loaded
        assert not theme_service.has_theme("invalid")
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

    def test_auto_theme_resolution(self, mocker, themes_dir):
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
        theme_service = ThemeService()

        resolved_theme_id = theme_service._resolve_system_theme()
        assert resolved_theme_id == "dark"

        # Test resolution to light theme - clear cache first
        mock_darkdetect.return_value = "Light"
        resolved_theme_id = theme_service._resolve_system_theme()
        assert resolved_theme_id == "light"

    def test_theme_application(self, mocker, themes_dir):
        """Test applying themes to the application."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
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

    def test_system_theme_application(self, mocker, themes_dir):
        """Test applying system theme resolves to correct system theme."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="Dark",
        )

        theme_service = ThemeService()

        # Apply system theme (should resolve to dark)
        success = theme_service.apply_theme("system")
        assert success

        current_theme = theme_service.get_current_theme()
        assert current_theme is not None
        if current_theme:
            assert current_theme.config.name == "Dark Theme"

    def test_invalid_theme_application(self, mocker, temp_dir):
        """Test applying non-existent theme returns False."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )

        theme_service = ThemeService()

        # Try to apply non-existent theme
        success = theme_service.apply_theme("nonexistent")
        assert not success

    def test_theme_changed_signal(self, mocker, themes_dir):
        """Test that theme_changed observer is called when theme is applied."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        # Mock darkdetect to return "dark" so system theme resolution works predictably
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="dark",
        )

        theme_service = ThemeService()

        # Verify themes are loaded before testing signals
        assert theme_service.has_theme("dark"), "Dark theme should be available"
        assert theme_service.has_theme("light"), "Light theme should be available"

        # Connect to observer and track calls
        observer_calls = []
        theme_service.add_theme_changed_observer(
            lambda theme: observer_calls.append(theme)
        )

        # Apply theme and check observer call
        result = theme_service.apply_theme("dark")
        assert result, "Dark theme application should succeed"
        assert len(observer_calls) == 1
        assert observer_calls[0].config.theme_id == "dark"

        # Apply system theme and check observer call
        observer_calls.clear()
        result = theme_service.apply_theme("system")
        assert result, "System theme application should succeed"
        assert len(observer_calls) == 1
        assert observer_calls[0].config.name == "Dark Theme"  # Should resolve to dark

    def test_has_theme_method(self, mocker, themes_dir):
        """Test has_theme method for checking theme availability."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        theme_service = ThemeService()

        # Test existing themes
        assert theme_service.has_theme("dark")
        assert theme_service.has_theme("light")

        # Test non-existent theme
        assert not theme_service.has_theme("nonexistent")

    def test_system_theme_detection_error_handling(self, mocker, temp_dir):
        """Test system theme detection error handling."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )
        mock_darkdetect = mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme"
        )

        theme_service = ThemeService()

        # Test exception during detection
        mock_darkdetect.side_effect = Exception("System error")
        result = theme_service._detect_system_theme()
        assert result.value == "light"

    def test_system_theme_detection_unexpected_value(self, mocker, temp_dir):
        """Test system theme detection with unexpected return value."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )
        mock_darkdetect = mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme"
        )

        theme_service = ThemeService()

        # Test unexpected return value
        mock_darkdetect.return_value = "Purple"  # Unexpected value
        result = theme_service._detect_system_theme()
        assert result.value == "light"  # Should fallback to light

    def test_system_theme_resolution_no_themes(self, mocker, temp_dir):
        """Test system theme resolution when no themes are available."""
        # Point to empty directory
        empty_themes_dir = temp_dir / "empty" / "metaeditor_safetensors"
        empty_themes_dir.mkdir(parents=True)
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=empty_themes_dir,
        )
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="Dark",
        )

        theme_service = ThemeService()

        # Should raise IndexError when no themes are available to select a fallback
        with pytest.raises(IndexError):
            theme_service._resolve_system_theme()

    def test_package_root_exception_handling(self, mocker):
        """Test initialization when get_package_root raises exception."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            side_effect=Exception("Cannot determine package root"),
        )

        # Should not crash during initialization
        theme_service = ThemeService()

        # Should have no themes available
        assert not theme_service.has_theme("dark")
        assert not theme_service.has_theme("light")

    def test_apply_theme_exception_handling(self, mocker, temp_dir):
        """Test apply_theme method exception handling."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )

        theme_service = ThemeService()

        # Mock theme to raise exception during QSS loading
        if "dark" in theme_service._available_themes:
            mocker.patch.object(
                theme_service._available_themes["dark"],
                "get_qss",
                side_effect=Exception("QSS loading failed"),
            )

            result = theme_service.apply_theme("dark")
            assert not result

    def test_system_theme_application_empty_result(self, mocker, temp_dir):
        """Test system theme application when resolution returns empty string."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )

        theme_service = ThemeService()

        # Mock _resolve_system_theme to return empty string
        mocker.patch.object(theme_service, "_resolve_system_theme", return_value="")
        result = theme_service.apply_theme("system")
        assert not result

    def test_get_current_theme_initially_none(self, mocker, temp_dir):
        """Test get_current_theme returns None initially."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )

        theme_service = ThemeService()

        # Should be None initially
        assert theme_service.get_current_theme() is None

    def test_live_reload_disabled_by_default(self, mocker, temp_dir):
        """Test that live reload is disabled by default."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=temp_dir / "metaeditor_safetensors",
        )

        # Ensure environment variable is not set
        mocker.patch.dict("os.environ", {}, clear=True)
        theme_service = ThemeService()

        # Should not have file watcher when live reload is disabled
        assert theme_service._file_watcher is None
        assert theme_service._watched_files == []

    def test_live_reload_enabled(self, mocker, themes_dir):
        """Test that live reload can be enabled via environment variable."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        # Enable live reload via environment variable
        mocker.patch.dict("os.environ", {"DEV_LIVE_STYLING": "true"})
        theme_service = ThemeService()

        # Always check that live reload is enabled
        assert theme_service._enable_live_reload is True

        # File watcher should be created when live reload is enabled
        assert theme_service._file_watcher is not None


class TestThemeServiceObserverPattern:
    def test_theme_service_observer_pattern(self, mocker, themes_dir):
        """Test that observers are notified when theme changes."""
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
        assert (
            len(observer_calls) == 1
        ), "Observer calls should not increase after removal"


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


def test_theme_service_string_representations(themes_dir, mocker):
    """Test string representations work correctly."""
    mocker.patch(
        "metaeditor_safetensors.services.theme_service.get_package_root",
        return_value=themes_dir.parent,
    )

    theme_service = ThemeService()

    # Apply a theme
    theme_service.apply_theme("dark")
    current_theme = theme_service.get_current_theme()

    if current_theme:
        # Should be able to convert theme to string without error
        theme_str = str(current_theme)
        assert isinstance(theme_str, str)
        assert len(theme_str) > 0


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


class TestSystemThemeMonitor:
    """Test cases for SystemThemeMonitor functionality."""

    def test_system_theme_monitor_creation(self):
        """Test SystemThemeMonitor can be created without error."""
        monitor = SystemThemeMonitor()
        assert monitor is not None
        assert not monitor._monitoring
        assert monitor._monitor_thread is None

    def test_start_monitoring(self, mocker):
        """Test starting system theme monitoring."""
        monitor = SystemThemeMonitor()
        
        # Mock threading.Thread to prevent actual thread creation
        mock_thread = Mock()
        mocker.patch("threading.Thread", return_value=mock_thread)
        
        monitor.start_monitoring()
        
        assert monitor._monitoring is True
        assert monitor._monitor_thread is mock_thread
        mock_thread.start.assert_called_once()

    def test_start_monitoring_already_monitoring(self, mocker):
        """Test starting monitoring when already monitoring does nothing."""
        monitor = SystemThemeMonitor()
        
        # Mock threading.Thread to prevent actual thread creation
        mock_thread = Mock()
        mocker.patch("threading.Thread", return_value=mock_thread)
        
        # Start monitoring first time
        monitor.start_monitoring()
        mock_thread.start.assert_called_once()
        
        # Reset mock and try to start again
        mock_thread.reset_mock()
        monitor.start_monitoring()
        
        # Should not create new thread or start again
        mock_thread.start.assert_not_called()

    def test_stop_monitoring(self, mocker):
        """Test stopping system theme monitoring."""
        monitor = SystemThemeMonitor()
        
        # Mock threading.Thread
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        mocker.patch("threading.Thread", return_value=mock_thread)
        
        # Start monitoring
        monitor.start_monitoring()
        assert monitor._monitoring is True
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        assert monitor._monitoring is False
        assert monitor._monitor_thread is None
        mock_thread.join.assert_called_once_with(timeout=1.0)

    def test_stop_monitoring_not_monitoring(self):
        """Test stopping monitoring when not monitoring does nothing."""
        monitor = SystemThemeMonitor()
        
        # Should not raise error
        monitor.stop_monitoring()
        
        assert not monitor._monitoring
        assert monitor._monitor_thread is None

    def test_monitor_system_theme_callback(self, mocker):
        """Test that monitor_system_theme calls darkdetect.listener with callback."""
        monitor = SystemThemeMonitor()
        
        # Mock darkdetect.listener
        mock_listener = mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        )
        
        monitor._monitoring = True
        
        # Call the monitoring method directly
        monitor._monitor_system_theme()
        
        # Should have called darkdetect.listener with a callback
        mock_listener.assert_called_once()
        callback = mock_listener.call_args[0][0]
        assert callable(callback)

    def test_monitor_system_theme_signal_emission(self, mocker):
        """Test that theme changes emit signals."""
        monitor = SystemThemeMonitor()
        
        # Track signal emissions
        signal_emissions = []
        monitor.theme_changed.connect(lambda theme: signal_emissions.append(theme))
        
        # Mock darkdetect.listener to call callback immediately
        def mock_listener(callback):
            if monitor._monitoring:
                callback("Dark")
        
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener",
            side_effect=mock_listener
        )
        
        monitor._monitoring = True
        monitor._monitor_system_theme()
        
        # Should have emitted signal
        assert len(signal_emissions) == 1
        assert signal_emissions[0] == "Dark"

    def test_monitor_system_theme_exception_handling(self, mocker):
        """Test monitor_system_theme handles exceptions gracefully."""
        monitor = SystemThemeMonitor()
        
        # Mock darkdetect.listener to raise exception
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener",
            side_effect=Exception("Listener error")
        )
        
        monitor._monitoring = True
        
        # Should not raise exception
        try:
            monitor._monitor_system_theme()
        except Exception:
            pytest.fail("_monitor_system_theme should handle exceptions gracefully")


class TestThemeServiceSystemMonitoring:
    """Test cases for ThemeService system theme monitoring functionality."""

    def test_theme_service_with_config_service(self, mocker, themes_dir):
        """Test ThemeService initialization with config service."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        # Mock config service
        mock_config = Mock()
        mock_config.get_theme_preference.return_value = "system"
        
        # Should not raise error with config service
        theme_service = ThemeService(mock_config)
        assert theme_service._config_service is mock_config

    def test_setup_system_theme_monitoring_system_preference(self, mocker, themes_dir):
        """Test system monitoring is started when preference is 'system'."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        # Mock config service with system preference
        mock_config = Mock()
        mock_config.get_theme_preference.return_value = "system"
        
        # Mock the start monitoring method
        start_mock = Mock()
        mocker.patch.object(ThemeService, "_start_system_theme_monitoring", start_mock)
        
        theme_service = ThemeService(mock_config)
        
        # Should have attempted to start monitoring
        start_mock.assert_called_once()

    def test_setup_system_theme_monitoring_non_system_preference(self, mocker, themes_dir):
        """Test system monitoring is not started when preference is not 'system'."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        # Mock config service with non-system preference
        mock_config = Mock()
        mock_config.get_theme_preference.return_value = "dark"
        
        # Mock the start monitoring method
        start_mock = Mock()
        mocker.patch.object(ThemeService, "_start_system_theme_monitoring", start_mock)
        
        theme_service = ThemeService(mock_config)
        
        # Should not have started monitoring
        start_mock.assert_not_called()

    def test_start_system_theme_monitoring(self, mocker, themes_dir):
        """Test starting system theme monitoring."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        theme_service = ThemeService()
        
        # Mock SystemThemeMonitor
        mock_monitor = Mock()
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.SystemThemeMonitor",
            return_value=mock_monitor
        )
        
        theme_service._start_system_theme_monitoring()
        
        assert theme_service._is_monitoring_system_theme is True
        assert theme_service._system_theme_monitor is mock_monitor
        mock_monitor.theme_changed.connect.assert_called_once()
        mock_monitor.start_monitoring.assert_called_once()

    def test_start_system_theme_monitoring_already_monitoring(self, mocker, themes_dir):
        """Test starting monitoring when already monitoring does nothing."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        theme_service = ThemeService()
        theme_service._is_monitoring_system_theme = True
        
        # Mock SystemThemeMonitor
        mock_monitor = Mock()
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.SystemThemeMonitor",
            return_value=mock_monitor
        )
        
        theme_service._start_system_theme_monitoring()
        
        # Should not have created new monitor
        mock_monitor.assert_not_called()

    def test_stop_system_theme_monitoring(self, mocker, themes_dir):
        """Test stopping system theme monitoring."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        theme_service = ThemeService()
        
        # Set up monitoring state
        mock_monitor = Mock()
        theme_service._system_theme_monitor = mock_monitor
        theme_service._is_monitoring_system_theme = True
        
        theme_service._stop_system_theme_monitoring()
        
        assert theme_service._is_monitoring_system_theme is False
        assert theme_service._system_theme_monitor is None
        mock_monitor.stop_monitoring.assert_called_once()

    def test_stop_system_theme_monitoring_not_monitoring(self, mocker, themes_dir):
        """Test stopping monitoring when not monitoring does nothing."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        theme_service = ThemeService()
        
        # Should not raise error
        theme_service._stop_system_theme_monitoring()
        
        assert not theme_service._is_monitoring_system_theme

    def test_on_system_theme_changed_with_system_preference(self, mocker, themes_dir):
        """Test system theme change handling when preference is 'system'."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        # Mock config service
        mock_config = Mock()
        mock_config.get_theme_preference.return_value = "system"
        
        theme_service = ThemeService(mock_config)
        
        # Mock apply_theme
        apply_mock = Mock(return_value=True)
        mocker.patch.object(theme_service, "apply_theme", apply_mock)
        
        # Simulate system theme change
        theme_service._on_system_theme_changed("Dark")
        
        # Should have applied system theme
        apply_mock.assert_called_once_with("system")

    def test_on_system_theme_changed_with_non_system_preference(self, mocker, themes_dir):
        """Test system theme change handling when preference is not 'system'."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        # Mock config service with non-system preference
        mock_config = Mock()
        mock_config.get_theme_preference.return_value = "dark"
        
        theme_service = ThemeService(mock_config)
        
        # Mock methods
        apply_mock = Mock()
        stop_mock = Mock()
        mocker.patch.object(theme_service, "apply_theme", apply_mock)
        mocker.patch.object(theme_service, "_stop_system_theme_monitoring", stop_mock)
        
        # Simulate system theme change
        theme_service._on_system_theme_changed("Dark")
        
        # Should not have applied theme but should stop monitoring
        apply_mock.assert_not_called()
        stop_mock.assert_called_once()

    def test_update_system_monitoring_for_preference_system(self, mocker, themes_dir):
        """Test updating monitoring when preference changes to 'system'."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        theme_service = ThemeService()
        
        # Mock start monitoring
        start_mock = Mock()
        mocker.patch.object(theme_service, "_start_system_theme_monitoring", start_mock)
        
        theme_service.update_system_monitoring_for_preference("system")
        
        start_mock.assert_called_once()

    def test_update_system_monitoring_for_preference_non_system(self, mocker, themes_dir):
        """Test updating monitoring when preference changes away from 'system'."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        theme_service = ThemeService()
        theme_service._is_monitoring_system_theme = True
        
        # Mock stop monitoring
        stop_mock = Mock()
        mocker.patch.object(theme_service, "_stop_system_theme_monitoring", stop_mock)
        
        theme_service.update_system_monitoring_for_preference("dark")
        
        stop_mock.assert_called_once()

    def test_shutdown_stops_monitoring(self, mocker, themes_dir):
        """Test shutdown stops system monitoring."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
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
        
        theme_service = ThemeService()
        
        # Mock methods to raise exceptions
        mocker.patch.object(
            theme_service, 
            "_start_system_theme_monitoring", 
            side_effect=Exception("Start error")
        )
        mocker.patch.object(
            theme_service, 
            "_stop_system_theme_monitoring", 
            side_effect=Exception("Stop error")
        )
        
        # Should not raise exceptions
        try:
            theme_service.update_system_monitoring_for_preference("system")
            theme_service.update_system_monitoring_for_preference("dark") 
            theme_service.shutdown()
        except Exception:
            pytest.fail("Exception handling should prevent exceptions from propagating")

    def test_system_theme_monitoring_without_config_service(self, mocker, themes_dir):
        """Test theme service works without config service."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        
        # Should not raise error without config service
        theme_service = ThemeService(None)
        assert theme_service._config_service is None
        assert not theme_service._is_monitoring_system_theme
