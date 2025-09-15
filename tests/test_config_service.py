import json
import os
import tempfile
from pathlib import Path

import pytest

from metaeditor_safetensors.services.config_service import ConfigService


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        temp_path = Path(tmp.name)
    yield temp_path
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_config_service_creation_with_defaults(temp_config_file):
    """Test that ConfigService creates with default settings."""
    config_service = ConfigService(temp_config_file)

    # Test default values
    assert config_service.get_recent_files() == []
    assert config_service.get_theme_preference() == "system"
    assert config_service.get_window_size() == (1100, 800)


def test_recent_files_management(temp_config_file):
    """Test recent files add/remove functionality."""
    config_service = ConfigService(temp_config_file)

    # Add files
    config_service.add_recent_file("/path/to/file1.safetensors")
    config_service.add_recent_file("/path/to/file2.safetensors")

    recent_files = config_service.get_recent_files()
    assert len(recent_files) == 2
    assert "/path/to/file2.safetensors" == recent_files[0]  # Most recent first
    assert "/path/to/file1.safetensors" == recent_files[1]

    # Remove a file
    config_service.remove_recent_file("/path/to/file1.safetensors")
    recent_files = config_service.get_recent_files()
    assert len(recent_files) == 1
    assert "/path/to/file2.safetensors" == recent_files[0]

    # Clear all
    config_service.clear_recent_files()
    assert config_service.get_recent_files() == []


def test_theme_preference_management(temp_config_file):
    """Test theme preference setting and getting."""
    config_service = ConfigService(temp_config_file)

    # Test setting different themes
    config_service.set_theme_preference("light")
    assert config_service.get_theme_preference() == "light"

    config_service.set_theme_preference("dark")
    assert config_service.get_theme_preference() == "dark"

    config_service.set_theme_preference("system")
    assert config_service.get_theme_preference() == "system"


def test_window_size_management(temp_config_file):
    """Test window size setting and getting."""
    config_service = ConfigService(temp_config_file)

    # Test setting custom window size
    config_service.set_window_size(1200, 900)
    width, height = config_service.get_window_size()
    assert width == 1200
    assert height == 900


def test_persistence_across_instances(temp_config_file):
    """Test that settings persist across ConfigService instances."""
    # Create first instance and set some values
    config1 = ConfigService(temp_config_file)
    config1.add_recent_file("/test/file.safetensors")
    config1.set_theme_preference("dark")
    config1.set_window_size(1300, 1000)

    # Create second instance and verify values persist
    config2 = ConfigService(temp_config_file)
    assert config2.get_recent_files() == ["/test/file.safetensors"]
    assert config2.get_theme_preference() == "dark"
    assert config2.get_window_size() == (1300, 1000)


def test_max_recent_files_limit(temp_config_file):
    """Test that recent files list respects the maximum limit."""
    config_service = ConfigService(temp_config_file)

    # Add more than the max limit (10)
    for i in range(15):
        config_service.add_recent_file(f"/test/file{i}.safetensors")

    recent_files = config_service.get_recent_files()
    assert len(recent_files) == 10  # Should be limited to MAX_RECENT_FILES
    assert recent_files[0] == "/test/file14.safetensors"  # Most recent first
    assert recent_files[-1] == "/test/file5.safetensors"  # Oldest kept


def test_recent_files_observer_pattern(temp_config_file):
    """Test that observers are notified when recent files change."""
    config_service = ConfigService(temp_config_file)

    # Track observer calls
    observer_calls = []

    def test_observer(files_list):
        observer_calls.append(files_list.copy())

    # Register observer
    config_service.add_recent_files_observer(test_observer)

    # Add a file - should trigger observer
    config_service.add_recent_file("/test/file1.safetensors")
    assert len(observer_calls) == 1
    assert observer_calls[0] == ["/test/file1.safetensors"]

    # Add another file - should trigger observer again
    config_service.add_recent_file("/test/file2.safetensors")
    assert len(observer_calls) == 2
    assert observer_calls[1] == ["/test/file2.safetensors", "/test/file1.safetensors"]

    # Remove a file - should trigger observer
    config_service.remove_recent_file("/test/file1.safetensors")
    assert len(observer_calls) == 3
    assert observer_calls[2] == ["/test/file2.safetensors"]

    # Clear files - should trigger observer
    config_service.clear_recent_files()
    assert len(observer_calls) == 4
    assert observer_calls[3] == []

    # Remove observer and test no more calls
    config_service.remove_recent_files_observer(test_observer)
    config_service.add_recent_file("/test/file3.safetensors")
    assert len(observer_calls) == 4  # Should not increase


def test_theme_preference_validation(temp_config_file):
    """Test that theme preference accepts various string values."""
    config_service = ConfigService(temp_config_file)

    # Test that any string is accepted (validation happens at theme service level)
    config_service.set_theme_preference("custom-theme-id")
    assert config_service.get_theme_preference() == "custom-theme-id"

    # Test empty string
    config_service.set_theme_preference("")
    assert config_service.get_theme_preference() == ""


def test_recent_files_duplicate_handling(temp_config_file):
    """Test that adding duplicate files moves them to the front."""
    config_service = ConfigService(temp_config_file)

    # Add initial files
    config_service.add_recent_file("/test/file1.safetensors")
    config_service.add_recent_file("/test/file2.safetensors")
    config_service.add_recent_file("/test/file3.safetensors")

    assert config_service.get_recent_files() == [
        "/test/file3.safetensors",
        "/test/file2.safetensors",
        "/test/file1.safetensors",
    ]

    # Add file1 again - should move to front and not duplicate
    config_service.add_recent_file("/test/file1.safetensors")

    recent_files = config_service.get_recent_files()
    assert len(recent_files) == 3  # Should not increase
    assert recent_files[0] == "/test/file1.safetensors"  # Should be at front
    assert recent_files == [
        "/test/file1.safetensors",
        "/test/file3.safetensors",
        "/test/file2.safetensors",
    ]


def test_pydantic_validation_in_persistence(temp_config_file):
    """Test that Pydantic validation works when loading from file."""
    # Create invalid JSON data
    invalid_data = {
        "config_version": "1.0",
        "recent_files": "not-a-list",  # Should be a list
        "theme": "system",
        "window": {
            "width": "not-a-number",  # Should be an integer
            "height": 800,
        },
    }

    # Write invalid data to file
    with open(temp_config_file, "w") as f:
        json.dump(invalid_data, f)

    # ConfigService should handle validation error and use defaults
    config_service = ConfigService(temp_config_file)

    # Should get default values due to validation failure
    assert config_service.get_recent_files() == []
    assert config_service.get_theme_preference() == "system"
    assert config_service.get_window_size() == (1100, 800)


def test_config_service_default_path_windows(mocker):
    """Test default config path creation on Windows."""
    # Mock Windows environment
    mocker.patch("os.name", "nt")
    mocker.patch.dict("os.environ", {"APPDATA": "C:\\Users\\test\\AppData\\Roaming"})
    mock_mkdir = mocker.patch("pathlib.Path.mkdir")

    config_service = ConfigService()

    expected_path = (
        Path("C:\\Users\\test\\AppData\\Roaming")
        / "metaeditor_safetensors"
        / "settings.json"
    )
    assert config_service.config_path == expected_path
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


@pytest.mark.skipif(os.name == "nt", reason="Unix path test not supported on Windows")
def test_config_service_default_path_unix_with_xdg(mocker):
    """Test default config path creation on Unix with XDG_CONFIG_HOME."""
    # Mock Unix environment with XDG_CONFIG_HOME
    mocker.patch("os.name", "posix")
    mocker.patch.dict("os.environ", {"XDG_CONFIG_HOME": "/home/test/.config"})
    mock_mkdir = mocker.patch("pathlib.Path.mkdir")

    config_service = ConfigService()
    expected_path = (
        Path("/home/test/.config") / "metaeditor_safetensors" / "settings.json"
    )
    assert config_service.config_path == expected_path
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_file_io_error_during_save(mocker, temp_config_file):
    """Test handling of IOError during save operations."""
    config_service = ConfigService(temp_config_file)

    # Mock file write to raise IOError
    mock_open_func = mocker.mock_open()
    mock_open_func.side_effect = IOError("Permission denied")
    mocker.patch("builtins.open", mock_open_func)

    # Should not crash when save fails
    config_service.set_theme_preference("dark")
    config_service.add_recent_file("/test/file.safetensors")
    config_service.set_window_size(1200, 900)


def test_type_error_during_save(mocker, temp_config_file):
    """Test handling of TypeError during save operations."""
    config_service = ConfigService(temp_config_file)

    # Mock settings to have an object that can't be serialized
    mock_settings = mocker.patch.object(config_service, "settings")
    mock_settings.model_dump_json.side_effect = TypeError(
        "Object is not JSON serializable"
    )

    # Should not crash when save fails due to serialization error
    config_service._save()


def test_corrupted_json_file_loading(temp_config_file):
    """Test handling of corrupted JSON file during loading."""
    # Write invalid JSON to file
    with open(temp_config_file, "w") as f:
        f.write("{ invalid json content }")

    # Should load defaults without crashing
    config_service = ConfigService(temp_config_file)
    assert config_service.get_recent_files() == []
    assert config_service.get_theme_preference() == "system"
    assert config_service.get_window_size() == (1100, 800)


def test_empty_json_file_loading(temp_config_file):
    """Test handling of empty JSON file during loading."""
    # Write empty content to file
    with open(temp_config_file, "w") as f:
        f.write("")

    # Should load defaults without crashing
    config_service = ConfigService(temp_config_file)
    assert config_service.get_recent_files() == []
    assert config_service.get_theme_preference() == "system"
    assert config_service.get_window_size() == (1100, 800)


def test_observer_error_handling(temp_config_file):
    """Test that observer errors don't crash the service."""
    config_service = ConfigService(temp_config_file)

    # Add observer that raises an exception
    def failing_observer(files_list):
        raise ValueError("Observer error")

    config_service.add_recent_files_observer(failing_observer)

    # Should not crash when observer fails
    config_service.add_recent_file("/test/file.safetensors")

    # Verify file was still added
    assert config_service.get_recent_files() == ["/test/file.safetensors"]


def test_remove_nonexistent_recent_file(temp_config_file):
    """Test removing a file that doesn't exist in recent files."""
    config_service = ConfigService(temp_config_file)

    # Add some files
    config_service.add_recent_file("/test/file1.safetensors")
    config_service.add_recent_file("/test/file2.safetensors")

    # Try to remove non-existent file
    config_service.remove_recent_file("/test/nonexistent.safetensors")

    # Should not affect existing files
    assert len(config_service.get_recent_files()) == 2
    assert "/test/file1.safetensors" in config_service.get_recent_files()
    assert "/test/file2.safetensors" in config_service.get_recent_files()


def test_remove_nonexistent_observer(temp_config_file):
    """Test removing an observer that wasn't added."""
    config_service = ConfigService(temp_config_file)

    def dummy_observer(files_list):
        pass

    # Should not crash when trying to remove non-existent observer
    config_service.remove_recent_files_observer(dummy_observer)

    # Add and remove actual observer
    config_service.add_recent_files_observer(dummy_observer)
    config_service.remove_recent_files_observer(dummy_observer)

    # Try to remove again - should not crash
    config_service.remove_recent_files_observer(dummy_observer)


def test_clear_recent_files_empty_list(temp_config_file):
    """Test clearing recent files when list is already empty."""
    config_service = ConfigService(temp_config_file)

    # List should be empty by default
    assert config_service.get_recent_files() == []

    # Clearing empty list should work fine
    config_service.clear_recent_files()
    assert config_service.get_recent_files() == []


def test_file_encoding_handling(temp_config_file):
    """Test that file encoding is handled correctly."""
    config_service = ConfigService(temp_config_file)

    # Add file with unicode characters
    unicode_path = "/test/файл с русскими символами.safetensors"
    config_service.add_recent_file(unicode_path)

    # Create new instance to test loading
    config_service2 = ConfigService(temp_config_file)
    assert unicode_path in config_service2.get_recent_files()


def test_theme_preference_edge_cases(temp_config_file):
    """Test theme preference with edge case values."""
    config_service = ConfigService(temp_config_file)

    # Test with None-like string
    config_service.set_theme_preference("none")
    assert config_service.get_theme_preference() == "none"

    # Test with numeric string
    config_service.set_theme_preference("123")
    assert config_service.get_theme_preference() == "123"

    # Test with special characters
    config_service.set_theme_preference("theme-with-dashes_and_underscores")
    assert config_service.get_theme_preference() == "theme-with-dashes_and_underscores"


def test_window_size_edge_cases(temp_config_file):
    """Test window size with edge case values."""
    config_service = ConfigService(temp_config_file)

    # Test with very small values
    config_service.set_window_size(1, 1)
    assert config_service.get_window_size() == (1, 1)

    # Test with very large values
    config_service.set_window_size(9999, 9999)
    assert config_service.get_window_size() == (9999, 9999)

    # Test with zero values
    config_service.set_window_size(0, 0)
    assert config_service.get_window_size() == (0, 0)
