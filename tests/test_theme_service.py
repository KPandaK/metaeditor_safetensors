import logging
import tempfile
from pathlib import Path

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

        # Connect to callback and track calls
        observer_calls = []
        theme_service.add_theme_changed_callback(
            lambda theme_id: observer_calls.append(theme_id)
        )

        # Apply theme and check callback call
        result = theme_service.apply_theme("dark")
        assert result, "Dark theme application should succeed"
        assert len(observer_calls) == 1
        assert observer_calls[0] == "dark"

        # Apply system theme and check callback call
        observer_calls.clear()
        result = theme_service.apply_theme("system")
        assert result, "System theme application should succeed"
        assert len(observer_calls) == 1
        assert observer_calls[0] == "system"  # Should get the original preference

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

        def test_observer(theme_id):
            observer_calls.append(theme_id)

        # Register observer
        theme_service.add_theme_changed_callback(test_observer)

        # Apply a theme - should trigger observer
        success = theme_service.apply_theme("dark")
        assert success, "Theme application should succeed"
        assert len(observer_calls) == 1
        assert observer_calls[0] == "dark"

        # Remove observer and test no more calls
        theme_service.remove_theme_changed_callback(test_observer)

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
    def failing_observer(theme_id):
        raise ValueError("Observer error")

    theme_service.add_theme_changed_callback(failing_observer)

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

    def dummy_observer(theme_id):
        pass

    # Should not crash when removing non-existent observer
    theme_service.remove_theme_changed_callback(dummy_observer)


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


class TestSystemThemeMonitoring:
    """Test cases for system theme monitoring functionality."""

    def test_monitoring_activation_with_system_theme(self, mocker, themes_dir):
        """Test that system theme monitoring starts when system theme is applied."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="dark",
        )

        theme_service = ThemeService()

        # Initially, monitoring should not be active
        assert not theme_service.is_monitoring_system_theme()
        assert theme_service.get_current_theme_preference() is None

        # Apply system theme - monitoring should start
        with mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        ) as mock_listener:
            # Make the listener mock block indefinitely to simulate real behavior
            import threading

            mock_listener.side_effect = lambda callback: threading.Event().wait()

            result = theme_service.apply_theme("system")
            assert result is True

            # Give the thread a moment to start and set the monitoring flag
            import time

            time.sleep(0.1)

            assert theme_service.is_monitoring_system_theme()
            assert theme_service.get_current_theme_preference() == "system"

        theme_service.cleanup()

    def test_monitoring_deactivation_with_specific_theme(self, mocker, themes_dir):
        """Test that system theme monitoring stops when specific theme is applied."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="dark",
        )

        theme_service = ThemeService()

        # Apply system theme first to start monitoring
        with mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        ) as mock_listener:
            # Make the listener mock block indefinitely to simulate real behavior
            import threading

            mock_listener.side_effect = lambda callback: threading.Event().wait()

            theme_service.apply_theme("system")
            import time

            time.sleep(0.1)
            assert theme_service.is_monitoring_system_theme()

        # Apply specific theme - monitoring should stop
        result = theme_service.apply_theme("dark")
        assert result is True
        assert not theme_service.is_monitoring_system_theme()
        assert theme_service.get_current_theme_preference() == "dark"

        theme_service.cleanup()

    def test_system_theme_changed_callback_emission(self, mocker, themes_dir):
        """Test that system_theme_changed callback is called correctly."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="dark",
        )

        theme_service = ThemeService()

        # Set up callback capture
        callback_received = []
        theme_service.add_system_theme_changed_callback(
            lambda theme_name: callback_received.append(theme_name)
        )

        # Simulate system theme change callback directly
        theme_service._notify_system_theme_changed("Light")

        # Check that callback was received
        assert len(callback_received) == 1
        assert callback_received[0] == "Light"

        theme_service.cleanup()

    def test_system_theme_change_with_system_theme_active(self, mocker, themes_dir):
        """Test theme reapplication when system theme changes with system theme active."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        theme_service = ThemeService()

        # Mock apply_theme to track calls
        original_apply = theme_service.apply_theme
        theme_service.apply_theme = mocker.MagicMock(side_effect=original_apply)

        # Start with dark system theme
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="dark",
        )

        with mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        ):
            # Apply system theme
            result = theme_service.apply_theme("system")
            assert result is True
            assert theme_service.get_current_theme_preference() == "system"

            # Simulate system theme change to light
            mocker.patch(
                "metaeditor_safetensors.services.theme_service.darkdetect.theme",
                return_value="light",
            )
            theme_service._on_system_theme_changed("Light")

            # apply_theme should have been called again with "system"
            from unittest.mock import call

            expected_calls = [call("system"), call("system")]
            theme_service.apply_theme.assert_has_calls(expected_calls)

        theme_service.cleanup()

    def test_system_theme_change_ignored_when_not_system(self, mocker, themes_dir):
        """Test that system theme changes are ignored when not using system theme."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="dark",
        )

        theme_service = ThemeService()

        # Apply specific theme (not system)
        result = theme_service.apply_theme("dark")
        assert result is True
        assert theme_service.get_current_theme_preference() == "dark"

        # Mock apply_theme to track calls
        original_apply = theme_service.apply_theme
        theme_service.apply_theme = mocker.MagicMock(side_effect=original_apply)

        # Simulate system theme change
        theme_service._on_system_theme_changed("Light")

        # apply_theme should not have been called since we're not using system theme
        theme_service.apply_theme.assert_not_called()

        theme_service.cleanup()

    def test_cleanup_stops_monitoring(self, mocker, themes_dir):
        """Test that cleanup properly stops theme monitoring."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="dark",
        )

        theme_service = ThemeService()

        # Start monitoring
        with mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        ) as mock_listener:
            # Make the listener mock block indefinitely to simulate real behavior
            import threading

            mock_listener.side_effect = lambda callback: threading.Event().wait()

            theme_service.apply_theme("system")
            import time

            time.sleep(0.1)
            assert theme_service.is_monitoring_system_theme()

        # Cleanup should stop monitoring
        theme_service.cleanup()
        assert not theme_service.is_monitoring_system_theme()

    def test_monitoring_thread_safety(self, mocker, themes_dir):
        """Test thread safety of monitoring activation/deactivation."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.theme",
            return_value="dark",
        )

        theme_service = ThemeService()

        # Test multiple rapid start/stop cycles
        with mocker.patch(
            "metaeditor_safetensors.services.theme_service.darkdetect.listener"
        ) as mock_listener:
            # Make the listener mock block indefinitely to simulate real behavior
            import threading

            mock_listener.side_effect = lambda callback: threading.Event().wait()

            for i in range(5):
                theme_service.apply_theme("system")
                import time

                time.sleep(0.01)  # Very brief pause
                theme_service.apply_theme("dark")
                time.sleep(0.01)

        # Should end up with monitoring stopped
        assert not theme_service.is_monitoring_system_theme()

        theme_service.cleanup()

    def test_getter_methods(self, mocker, themes_dir):
        """Test new getter methods for theme preference and monitoring state."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        theme_service = ThemeService()

        # Initially no preference set
        assert theme_service.get_current_theme_preference() is None
        assert not theme_service.is_monitoring_system_theme()

        theme_service.cleanup()

    def test_callback_management(self, mocker, themes_dir):
        """Test callback management for system theme changes."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        theme_service = ThemeService()

        # Test adding and removing callbacks
        callback_calls = []

        def test_callback(theme_name):
            callback_calls.append(theme_name)

        # Add callback
        theme_service.add_system_theme_changed_callback(test_callback)

        # Trigger callback
        theme_service._notify_system_theme_changed("Dark")
        assert len(callback_calls) == 1
        assert callback_calls[0] == "Dark"

        # Remove callback
        theme_service.remove_system_theme_changed_callback(test_callback)

        # Trigger again - should not be called
        theme_service._notify_system_theme_changed("Light")
        assert len(callback_calls) == 1  # Should not increase

        theme_service.cleanup()

    def test_callback_exception_handling(self, mocker, themes_dir):
        """Test that callback exceptions don't crash the service."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        theme_service = ThemeService()

        # Add callback that raises exception
        def failing_callback(theme_name):
            raise ValueError("Callback error")

        theme_service.add_system_theme_changed_callback(failing_callback)

        # Should not crash when notifying callbacks
        try:
            theme_service._notify_system_theme_changed("Dark")
        except Exception:
            pytest.fail("Callback exceptions should be handled gracefully")

        theme_service.cleanup()

    def test_has_theme_with_system(self, mocker, themes_dir):
        """Test has_theme method includes 'system' theme."""
        mocker.patch(
            "metaeditor_safetensors.services.theme_service.get_package_root",
            return_value=themes_dir.parent,
        )

        theme_service = ThemeService()

        # Test existing themes
        assert theme_service.has_theme("dark")
        assert theme_service.has_theme("light")
        assert theme_service.has_theme("system")  # Should include system

        # Test non-existent theme
        assert not theme_service.has_theme("nonexistent")

        theme_service.cleanup()
