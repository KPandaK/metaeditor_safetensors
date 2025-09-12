"""
Unit tests for ConfigService
============================

Tests for configuration management, including settings persistence,
recent files management, and version migration.
"""

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from metaeditor_safetensors.services.config_service import ConfigService


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up temporary files and directory
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def config_service_factory(mocker, temp_dir):
    """Factory to create ConfigService instances with mocked settings directory."""

    def _create_config_service():
        mocker.patch.object(
            ConfigService, "_get_settings_directory", return_value=Path(temp_dir)
        )
        return ConfigService()

    return _create_config_service


@pytest.fixture(autouse=True)
def suppress_logging():
    """Suppress debug/info logging during tests for cleaner output."""
    logging.getLogger().setLevel(logging.ERROR)


class TestConfigService:
    """Test cases for ConfigService functionality."""

    def test_initialization_creates_default_settings(self, config_service_factory):
        """Test that initialization creates default settings when no file exists."""
        config_service = config_service_factory()
        # Verify default settings structure
        assert config_service.get_recent_files() == []
        assert config_service._settings["config_version"] == "1.0"
        assert "app_version" in config_service._settings
        assert "recent_files" in config_service._settings

    def test_add_recent_file(self, config_service_factory):
        """Test adding files to the recent files list."""
        config_service = config_service_factory()
        # Add a file
        test_file = "/path/to/test.safetensors"
        config_service.add_recent_file(test_file)

        # Verify it was added
        recent_files = config_service.get_recent_files()
        assert len(recent_files) == 1
        assert recent_files[0] == test_file

    def test_add_recent_file_deduplication(self, config_service_factory):
        """Test that adding the same file twice moves it to the top."""
        config_service = config_service_factory()
        # Add multiple files
        file1 = "/path/to/file1.safetensors"
        file2 = "/path/to/file2.safetensors"
        config_service.add_recent_file(file1)
        config_service.add_recent_file(file2)

        # Add file1 again
        config_service.add_recent_file(file1)

        # Verify file1 is at the top and no duplicates
        recent_files = config_service.get_recent_files()
        assert len(recent_files) == 2
        assert recent_files[0] == file1
        assert recent_files[1] == file2

    def test_recent_files_max_limit(self, config_service_factory):
        """Test that recent files list respects the maximum limit."""
        config_service = config_service_factory()
        # Add more than the maximum number of files
        for i in range(15):  # More than the default max of 10
            config_service.add_recent_file(f"/path/to/file{i}.safetensors")

        # Verify only the last 10 files are kept
        recent_files = config_service.get_recent_files()
        assert len(recent_files) == 10
        assert recent_files[0] == "/path/to/file14.safetensors"
        assert recent_files[-1] == "/path/to/file5.safetensors"

    def test_clear_recent_files(self, config_service_factory):
        """Test clearing the recent files list."""
        config_service = config_service_factory()
        # Add some files
        config_service.add_recent_file("/path/to/file1.safetensors")
        config_service.add_recent_file("/path/to/file2.safetensors")

        # Clear them
        config_service.clear_recent_files()

        # Verify the list is empty
        assert config_service.get_recent_files() == []

    def test_remove_recent_file(self, config_service_factory):
        """Test removing a specific file from recent files."""
        config_service = config_service_factory()
        # Add files
        file1 = "/path/to/file1.safetensors"
        file2 = "/path/to/file2.safetensors"
        file3 = "/path/to/file3.safetensors"
        config_service.add_recent_file(file1)
        config_service.add_recent_file(file2)
        config_service.add_recent_file(file3)

        # Remove middle file
        config_service.remove_recent_file(file2)

        # Verify it was removed
        recent_files = config_service.get_recent_files()
        assert len(recent_files) == 2
        assert file1 in recent_files
        assert file3 in recent_files
        assert file2 not in recent_files

    def test_settings_persistence(self, mocker, temp_dir):
        """Test that settings are properly saved and loaded from disk."""
        # Create and configure a service
        mocker.patch.object(
            ConfigService, "_get_settings_directory", return_value=Path(temp_dir)
        )
        config_service = ConfigService()
        test_file = "/path/to/test.safetensors"
        config_service.add_recent_file(test_file)

        # Create a new service instance (should load from disk)
        config_service2 = ConfigService()

        # Verify the settings were loaded
        assert config_service2.get_recent_files() == [test_file]

    def test_corrupted_settings_file_handling(self, config_service_factory, temp_dir):
        """Test handling of corrupted settings file."""
        temp_settings_file = Path(temp_dir) / "test_settings.json"
        # Create a corrupted JSON file
        with open(temp_settings_file, "w") as f:
            f.write("{ invalid json }")

        # Should not crash and should use defaults
        config_service = config_service_factory()

        # Verify defaults are used
        assert config_service.get_recent_files() == []
        assert config_service._settings["config_version"] == "1.0"

    def test_invalid_settings_file_format(self, config_service_factory, temp_dir):
        """Test handling of invalid settings file format (non-dict)."""
        temp_settings_file = Path(temp_dir) / "test_settings.json"
        # Create a file with a list instead of dict
        with open(temp_settings_file, "w") as f:
            json.dump(["/some/file.safetensors"], f)

        # Should use defaults when format is invalid
        config_service = config_service_factory()

        # Verify defaults are used
        assert config_service.get_recent_files() == []
        assert config_service._settings["config_version"] == "1.0"

    def test_missing_recent_files_key(self, config_service_factory, temp_dir):
        """Test handling when recent_files key is missing."""
        temp_settings_file = Path(temp_dir) / "test_settings.json"
        # Create a settings file without recent_files
        incomplete_data = {
            "config_version": "1.0",
            "app_version": "1.0.0",
            # Missing recent_files
        }

        with open(temp_settings_file, "w") as f:
            json.dump(incomplete_data, f)

        # Should add empty recent_files array
        config_service = config_service_factory()

        # Verify recent_files was added
        assert config_service.get_recent_files() == []
        assert config_service._settings["config_version"] == "1.0"

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_windows_settings_directory(self, mocker):
        """Test that Windows settings directory is correctly determined."""
        mocker.patch.dict(
            "metaeditor_safetensors.services.config_service.os.environ",
            {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"},
            clear=True,
        )
        mock_path_class = mocker.patch(
            "metaeditor_safetensors.services.config_service.Path"
        )
        # Create mock path objects
        mock_appdata_path = mocker.MagicMock()
        mock_settings_path = mocker.MagicMock()
        mock_settings_file = mocker.MagicMock()

        # Setup the path operations
        mock_path_class.return_value = mock_appdata_path
        mock_appdata_path.__truediv__.return_value = mock_settings_path
        mock_settings_path.__truediv__.return_value = mock_settings_file
        mock_settings_file.exists.return_value = False  # No existing settings file

        config_service = ConfigService()

        # Verify Path was called with APPDATA value
        mock_path_class.assert_called_with("C:\\Users\\Test\\AppData\\Roaming")
        # Verify the settings directory creation
        mock_appdata_path.__truediv__.assert_called_with("SafetensorsMetadataEditor")
        mock_settings_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify the ConfigService has the mocked settings directory
        assert config_service._settings_dir == mock_settings_path

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_windows_settings_directory_no_appdata(self, mocker):
        """Test Windows settings directory when APPDATA is not available."""
        mocker.patch.dict(
            "metaeditor_safetensors.services.config_service.os.environ", {}, clear=True
        )  # No APPDATA
        mock_path_class = mocker.patch(
            "metaeditor_safetensors.services.config_service.Path"
        )
        # Create mock path objects
        mock_home_path = mocker.MagicMock()
        mock_settings_path = mocker.MagicMock()
        mock_settings_file = mocker.MagicMock()

        # Setup the path operations
        mock_path_class.home.return_value = mock_home_path
        mock_home_path.__truediv__.return_value = mock_settings_path
        mock_settings_path.__truediv__.return_value = mock_settings_file
        mock_settings_file.exists.return_value = False  # No existing settings file

        config_service = ConfigService()

        # Verify Path.home() was called
        mock_path_class.home.assert_called_once()
        # Verify the settings directory creation
        mock_home_path.__truediv__.assert_called_with(".safetensors_metadata_editor")
        mock_settings_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify the ConfigService has the mocked settings directory
        assert config_service._settings_dir == mock_settings_path

    def test_json_decode_error_handling(self, config_service_factory, temp_dir):
        """Test handling of JSON decode errors with specific error message."""
        temp_settings_file = Path(temp_dir) / "test_settings.json"
        # Create a file with invalid JSON
        with open(temp_settings_file, "w") as f:
            f.write("{invalid json")  # Definitely invalid JSON

        # Instead of testing print output, test that we get expected behavior
        config_service = config_service_factory()

        # Verify defaults are used (this proves the error handling worked)
        assert config_service.get_recent_files() == []
        assert config_service._settings["config_version"] == "1.0"

    def test_io_error_during_load(self, mocker, temp_dir):
        """Test handling of IO errors during settings load."""
        temp_settings_file = Path(temp_dir) / "test_settings.json"
        # Create a valid settings file first
        with open(temp_settings_file, "w") as f:
            json.dump({"recent_files": ["/test/file.safetensors"]}, f)

        # Make the file unreadable by changing permissions (Windows approach)
        import stat

        try:
            # Remove read permissions
            os.chmod(temp_settings_file, stat.S_IWRITE)

            mocker.patch.object(
                ConfigService, "_get_settings_directory", return_value=Path(temp_dir)
            )
            config_service = ConfigService()

            # Should use defaults when file can't be loaded
            assert config_service.get_recent_files() == []

        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(temp_settings_file, stat.S_IREAD | stat.S_IWRITE)
            except OSError:
                pass  # Ignore file permission restoration errors during cleanup

    def test_io_error_during_save(self, mocker, temp_dir):
        """Test handling of IO errors during settings save."""
        mocker.patch.object(
            ConfigService, "_get_settings_directory", return_value=Path(temp_dir)
        )
        config_service = ConfigService()

        # Add a file to trigger save
        test_file = "/test/file.safetensors"

        # Mock open to raise IOError during write operations
        mock_open = mocker.patch("builtins.open")
        mock_open.side_effect = IOError("Disk full")

        # This should not raise an exception, but should handle the error gracefully
        try:
            config_service.add_recent_file(test_file)
            # If we get here without exception, the error handling worked
            success = True
        except IOError:
            # If IOError propagates, error handling failed
            success = False

        assert success, "IOError during save should be handled gracefully"

    def test_invalid_recent_files_type_in_loaded_data(self, mocker, temp_dir):
        """Test handling when recent_files is not a list in loaded data."""
        temp_settings_file = Path(temp_dir) / "test_settings.json"
        # Create a settings file with recent_files as a string instead of list
        invalid_data = {
            "config_version": "1.0",
            "app_version": "1.0.0",
            "recent_files": "not_a_list",  # Should be a list
        }

        with open(temp_settings_file, "w") as f:
            json.dump(invalid_data, f)

        mocker.patch.object(
            ConfigService, "_get_settings_directory", return_value=Path(temp_dir)
        )
        config_service = ConfigService()

        # Should fix the invalid recent_files and make it an empty list
        assert config_service.get_recent_files() == []
        assert isinstance(config_service._settings["recent_files"], list)

    def test_save_settings_version_enforcement(self, mocker, temp_dir):
        """Test that save always enforces current version info."""
        mocker.patch.object(
            ConfigService, "_get_settings_directory", return_value=Path(temp_dir)
        )
        config_service = ConfigService()

        # Manually corrupt the internal settings version
        config_service._settings["config_version"] = "old_version"
        config_service._settings["app_version"] = "old_app_version"

        # Add a file to trigger save
        config_service.add_recent_file("/test/file.safetensors")

        # Reload and verify version was enforced during save
        mocker.patch.object(
            ConfigService, "_get_settings_directory", return_value=Path(temp_dir)
        )
        config_service2 = ConfigService()
        assert config_service2._settings["config_version"] == "1.0"
        # App version should be current version from _version module
        assert "app_version" in config_service2._settings

    @pytest.mark.skipif(os.name == "nt", reason="Unix/Linux/macOS-specific test")
    def test_unix_settings_directory(self, mocker):
        """Test that Unix/Linux/macOS settings directory is correctly determined."""
        mock_path_class = mocker.patch(
            "metaeditor_safetensors.services.config_service.Path"
        )
        # Create mock path objects
        mock_home_path = mocker.MagicMock()
        mock_settings_path = mocker.MagicMock()
        mock_settings_file = mocker.MagicMock()

        # Setup the path operations
        mock_path_class.home.return_value = mock_home_path
        mock_home_path.__truediv__.return_value = mock_settings_path
        mock_settings_path.__truediv__.return_value = mock_settings_file
        mock_settings_file.exists.return_value = False  # No existing settings file

        config_service = ConfigService()

        # Verify Path.home() was called
        mock_path_class.home.assert_called_once()
        # Verify the settings directory creation
        mock_home_path.__truediv__.assert_called_with(".safetensors_metadata_editor")
        mock_settings_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify the ConfigService has the mocked settings directory
        assert config_service._settings_dir == mock_settings_path
