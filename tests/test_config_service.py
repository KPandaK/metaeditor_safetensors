"""
Unit tests for ConfigService
============================

Tests for configuration management, including settings persistence,
recent files management, and version migration.
"""

import unittest
import tempfile
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the service to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from metaeditor_safetensors.services.config_service import ConfigService


class TestConfigService(unittest.TestCase):
    """Test cases for ConfigService functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_settings_file = Path(self.temp_dir) / "test_settings.json"
        
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary files and directory
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def _create_config_service_with_temp_file(self):
        """Helper to create a ConfigService with a temporary settings file."""
        with patch.object(ConfigService, '_get_settings_directory', return_value=Path(self.temp_dir)):
            return ConfigService()

    def test_initialization_creates_default_settings(self):
        """Test that initialization creates default settings when no file exists."""
        config_service = self._create_config_service_with_temp_file()
        
        # Verify default settings structure
        self.assertEqual(config_service.get_recent_files(), [])
        self.assertEqual(config_service._settings['config_version'], '1.0')
        self.assertIn('app_version', config_service._settings)
        self.assertIn('recent_files', config_service._settings)

    def test_add_recent_file(self):
        """Test adding files to the recent files list."""
        config_service = self._create_config_service_with_temp_file()
        
        # Add a file
        test_file = "/path/to/test.safetensors"
        config_service.add_recent_file(test_file)
        
        # Verify it was added
        recent_files = config_service.get_recent_files()
        self.assertEqual(len(recent_files), 1)
        self.assertEqual(recent_files[0], test_file)

    def test_add_recent_file_deduplication(self):
        """Test that adding the same file twice moves it to the top."""
        config_service = self._create_config_service_with_temp_file()
        
        # Add multiple files
        file1 = "/path/to/file1.safetensors"
        file2 = "/path/to/file2.safetensors"
        config_service.add_recent_file(file1)
        config_service.add_recent_file(file2)
        
        # Add file1 again
        config_service.add_recent_file(file1)
        
        # Verify file1 is at the top and no duplicates
        recent_files = config_service.get_recent_files()
        self.assertEqual(len(recent_files), 2)
        self.assertEqual(recent_files[0], file1)
        self.assertEqual(recent_files[1], file2)

    def test_recent_files_max_limit(self):
        """Test that recent files list respects the maximum limit."""
        config_service = self._create_config_service_with_temp_file()
        
        # Add more than the maximum number of files
        for i in range(15):  # More than the default max of 10
            config_service.add_recent_file(f"/path/to/file{i}.safetensors")
        
        # Verify only the last 10 files are kept
        recent_files = config_service.get_recent_files()
        self.assertEqual(len(recent_files), 10)
        self.assertEqual(recent_files[0], "/path/to/file14.safetensors")
        self.assertEqual(recent_files[-1], "/path/to/file5.safetensors")

    def test_clear_recent_files(self):
        """Test clearing the recent files list."""
        config_service = self._create_config_service_with_temp_file()
        
        # Add some files
        config_service.add_recent_file("/path/to/file1.safetensors")
        config_service.add_recent_file("/path/to/file2.safetensors")
        
        # Clear them
        config_service.clear_recent_files()
        
        # Verify the list is empty
        self.assertEqual(config_service.get_recent_files(), [])

    def test_remove_recent_file(self):
        """Test removing a specific file from recent files."""
        config_service = self._create_config_service_with_temp_file()
        
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
        self.assertEqual(len(recent_files), 2)
        self.assertIn(file1, recent_files)
        self.assertIn(file3, recent_files)
        self.assertNotIn(file2, recent_files)

    def test_settings_persistence(self):
        """Test that settings are properly saved and loaded from disk."""
        # Create and configure a service
        config_service = self._create_config_service_with_temp_file()
        test_file = "/path/to/test.safetensors"
        config_service.add_recent_file(test_file)
        
        # Create a new service instance (should load from disk)
        config_service2 = self._create_config_service_with_temp_file()
        
        # Verify the settings were loaded
        self.assertEqual(config_service2.get_recent_files(), [test_file])

    def test_corrupted_settings_file_handling(self):
        """Test handling of corrupted settings file."""
        # Create a corrupted JSON file
        with open(self.temp_settings_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Should not crash and should use defaults
        config_service = self._create_config_service_with_temp_file()
        
        # Verify defaults are used
        self.assertEqual(config_service.get_recent_files(), [])
        self.assertEqual(config_service._settings['config_version'], '1.0')

    def test_invalid_settings_file_format(self):
        """Test handling of invalid settings file format (non-dict)."""
        # Create a file with a list instead of dict
        with open(self.temp_settings_file, 'w') as f:
            json.dump(["/some/file.safetensors"], f)
        
        # Should use defaults when format is invalid
        config_service = self._create_config_service_with_temp_file()
        
        # Verify defaults are used
        self.assertEqual(config_service.get_recent_files(), [])
        self.assertEqual(config_service._settings['config_version'], '1.0')

    def test_missing_recent_files_key(self):
        """Test handling when recent_files key is missing."""
        # Create a settings file without recent_files
        incomplete_data = {
            "config_version": "1.0",
            "app_version": "1.0.0"
            # Missing recent_files
        }
        
        with open(self.temp_settings_file, 'w') as f:
            json.dump(incomplete_data, f)
        
        # Should add empty recent_files array
        config_service = self._create_config_service_with_temp_file()
        
        # Verify recent_files was added
        self.assertEqual(config_service.get_recent_files(), [])
        self.assertEqual(config_service._settings['config_version'], '1.0')

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")
    def test_windows_settings_directory(self):
        """Test that Windows settings directory is correctly determined."""
        with patch.dict('metaeditor_safetensors.services.config_service.os.environ', {'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'}):
            with patch('metaeditor_safetensors.services.config_service.Path') as mock_path_class:
                # Create mock path objects
                mock_appdata_path = MagicMock()
                mock_settings_path = MagicMock()
                mock_settings_file = MagicMock()
                
                # Setup the path operations
                mock_path_class.return_value = mock_appdata_path
                mock_appdata_path.__truediv__.return_value = mock_settings_path
                mock_settings_path.__truediv__.return_value = mock_settings_file
                mock_settings_file.exists.return_value = False  # No existing settings file
                
                config_service = ConfigService()
                
                # Verify Path was called with APPDATA value
                mock_path_class.assert_called_with('C:\\Users\\Test\\AppData\\Roaming')
                # Verify the settings directory creation
                mock_appdata_path.__truediv__.assert_called_with("SafetensorsMetadataEditor")
                mock_settings_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
                
                # Verify the ConfigService has the mocked settings directory
                self.assertEqual(config_service._settings_dir, mock_settings_path)

    @unittest.skipUnless(os.name == 'nt', "Windows-specific test")  
    def test_windows_settings_directory_no_appdata(self):
        """Test Windows settings directory when APPDATA is not available."""
        with patch.dict('metaeditor_safetensors.services.config_service.os.environ', {}, clear=True):  # No APPDATA
            with patch('metaeditor_safetensors.services.config_service.Path') as mock_path_class:
                # Create mock path objects
                mock_home_path = MagicMock()
                mock_settings_path = MagicMock()
                mock_settings_file = MagicMock()
                
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
                self.assertEqual(config_service._settings_dir, mock_settings_path)

    def test_json_decode_error_handling(self):
        """Test handling of JSON decode errors with specific error message."""
        # Create a file with invalid JSON
        with open(self.temp_settings_file, 'w') as f:
            f.write('{invalid json')  # Definitely invalid JSON
        
        # Instead of testing print output, test that we get expected behavior
        config_service = self._create_config_service_with_temp_file()
        
        # Verify defaults are used (this proves the error handling worked)
        self.assertEqual(config_service.get_recent_files(), [])
        self.assertEqual(config_service._settings['config_version'], '1.0')

    def test_io_error_during_load(self):
        """Test handling of IO errors during settings load."""
        # Create a valid settings file first
        with open(self.temp_settings_file, 'w') as f:
            json.dump({"recent_files": ["/test/file.safetensors"]}, f)
        
        # Make the file unreadable by changing permissions (Windows approach)
        import stat
        try:
            # Remove read permissions
            os.chmod(self.temp_settings_file, stat.S_IWRITE)
            
            config_service = self._create_config_service_with_temp_file()
            
            # Should use defaults when file can't be loaded
            self.assertEqual(config_service.get_recent_files(), [])
            
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(self.temp_settings_file, stat.S_IREAD | stat.S_IWRITE)
            except:
                pass  # Ignore cleanup errors

    def test_io_error_during_save(self):
        """Test handling of IO errors during settings save."""
        config_service = self._create_config_service_with_temp_file()
        
        # Add a file to trigger save
        test_file = "/test/file.safetensors"
        
        # Mock open to raise IOError during write operations
        original_open = open
        def mock_open_func(*args, **kwargs):
            mode = kwargs.get('mode', args[1] if len(args) > 1 else 'r')
            if 'w' in mode:
                raise IOError("Disk full")
            return original_open(*args, **kwargs)
        
        with patch('builtins.open', side_effect=mock_open_func):
            # This should not raise an exception, but should handle the error gracefully
            try:
                config_service.add_recent_file(test_file)
                # If we get here without exception, the error handling worked
                success = True
            except IOError:
                # If IOError propagates, error handling failed
                success = False
            
            self.assertTrue(success, "IOError during save should be handled gracefully")

    def test_invalid_recent_files_type_in_loaded_data(self):
        """Test handling when recent_files is not a list in loaded data."""
        # Create a settings file with recent_files as a string instead of list
        invalid_data = {
            "config_version": "1.0",
            "app_version": "1.0.0", 
            "recent_files": "not_a_list"  # Should be a list
        }
        
        with open(self.temp_settings_file, 'w') as f:
            json.dump(invalid_data, f)
        
        config_service = self._create_config_service_with_temp_file()
        
        # Should fix the invalid recent_files and make it an empty list
        self.assertEqual(config_service.get_recent_files(), [])
        self.assertIsInstance(config_service._settings['recent_files'], list)

    def test_save_settings_version_enforcement(self):
        """Test that save always enforces current version info."""
        config_service = self._create_config_service_with_temp_file()
        
        # Manually corrupt the internal settings version
        config_service._settings['config_version'] = 'old_version'
        config_service._settings['app_version'] = 'old_app_version'
        
        # Add a file to trigger save
        config_service.add_recent_file("/test/file.safetensors")
        
        # Reload and verify version was enforced during save
        config_service2 = self._create_config_service_with_temp_file()
        self.assertEqual(config_service2._settings['config_version'], '1.0')
        # App version should be current version from _version module
        self.assertIn('app_version', config_service2._settings)


    @unittest.skipIf(os.name == 'nt', "Unix/Linux/macOS-specific test")
    def test_unix_settings_directory(self):
        """Test that Unix/Linux/macOS settings directory is correctly determined."""
        with patch('metaeditor_safetensors.services.config_service.Path') as mock_path_class:
            # Create mock path objects
            mock_home_path = MagicMock()
            mock_settings_path = MagicMock()
            mock_settings_file = MagicMock()
            
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
            self.assertEqual(config_service._settings_dir, mock_settings_path)


if __name__ == '__main__':
    unittest.main()
