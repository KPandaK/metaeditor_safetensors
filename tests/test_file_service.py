"""
Unit tests for File Service
============================

Tests for file and path utilities including project root detection
and package root resolution.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from metaeditor_safetensors.services.file_service import get_package_root, get_project_root


class TestFileService(unittest.TestCase):
    """Test cases for file service functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = None

    def tearDown(self):
        """Clean up after each test method."""
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            shutil.rmtree(self.temp_dir)

    def _create_temp_structure(self, files_and_dirs):
        """Helper to create temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        temp_path = Path(self.temp_dir)
        
        for item in files_and_dirs:
            if item.endswith('/'):
                # Directory
                (temp_path / item.rstrip('/')).mkdir(parents=True, exist_ok=True)
            else:
                # File
                file_path = temp_path / item
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()
        
        return temp_path

    def test_get_project_root_with_pyproject_toml(self):
        """Test get_project_root finds project root with pyproject.toml marker."""
        # Create temporary structure with pyproject.toml
        root_path = self._create_temp_structure([
            'pyproject.toml',
            'src/',
            'src/subdir/',
            'src/subdir/file.py'
        ])
        
        # Test from subdirectory
        start_path = root_path / 'src' / 'subdir'
        result = get_project_root(start_path)
        
        # Should find the root with pyproject.toml
        self.assertEqual(result, root_path)

    def test_get_project_root_with_git_marker(self):
        """Test get_project_root finds project root with .git marker."""
        # Create temporary structure with .git
        root_path = self._create_temp_structure([
            '.git/',
            'src/',
            'src/subdir/',
            'src/subdir/file.py'
        ])
        
        # Test from subdirectory
        start_path = root_path / 'src' / 'subdir'
        result = get_project_root(start_path)
        
        # Should find the root with .git
        self.assertEqual(result, root_path)

    def test_get_project_root_with_justfile_marker(self):
        """Test get_project_root finds project root with justfile marker."""
        # Create temporary structure with justfile
        root_path = self._create_temp_structure([
            'justfile',
            'src/',
            'src/subdir/',
            'src/subdir/file.py'
        ])
        
        # Test from subdirectory
        start_path = root_path / 'src' / 'subdir'
        result = get_project_root(start_path)
        
        # Should find the root with justfile
        self.assertEqual(result, root_path)

    def test_get_project_root_no_markers_found(self):
        """Test get_project_root fallback when no markers are found."""
        # Create temporary structure without any markers
        root_path = self._create_temp_structure([
            'src/',
            'src/subdir/',
            'src/subdir/file.py'
        ])
        
        # Test from subdirectory
        start_path = root_path / 'src' / 'subdir'
        result = get_project_root(start_path)
        
        # Should return the start path as fallback
        self.assertEqual(result, start_path)

    def test_get_project_root_multiple_markers(self):
        """Test get_project_root with multiple markers (finds first one)."""
        # Create temporary structure with multiple markers
        root_path = self._create_temp_structure([
            'pyproject.toml',
            '.git/',
            'justfile',
            'src/',
            'src/subdir/',
            'src/subdir/file.py'
        ])
        
        # Test from subdirectory
        start_path = root_path / 'src' / 'subdir'
        result = get_project_root(start_path)
        
        # Should find the root (order in markers list determines which is found first)
        self.assertEqual(result, root_path)

    def test_get_project_root_default_cwd(self):
        """Test get_project_root uses current working directory when start_path is None."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path('/test/current/dir')
            
            with patch.object(Path, 'exists') as mock_exists:
                # Mock no markers found
                mock_exists.return_value = False
                
                result = get_project_root(None)
                
                # Should use cwd as fallback when no markers found
                self.assertEqual(result, Path('/test/current/dir'))
                mock_cwd.assert_called_once()

    def test_get_project_root_nested_markers(self):
        """Test get_project_root finds the closest marker going up the tree."""
        # Create structure with nested markers
        root_path = self._create_temp_structure([
            'pyproject.toml',
            'src/',
            'src/nested/',
            'src/nested/.git/',
            'src/nested/subdir/',
            'src/nested/subdir/file.py'
        ])
        
        # Test from deepest subdirectory
        start_path = root_path / 'src' / 'nested' / 'subdir'
        result = get_project_root(start_path)
        
        # Should find the closest .git directory first (in src/nested/)
        expected_path = root_path / 'src' / 'nested'
        self.assertEqual(result, expected_path)

    def test_get_package_root_success(self):
        """Test get_package_root with successful importlib.resources call."""
        with patch('metaeditor_safetensors.services.file_service.resources.files') as mock_files:
            # Mock successful package resolution
            mock_package_files = MagicMock()
            mock_files.return_value = mock_package_files
            
            # Mock the string conversion to return a valid path string
            expected_path = '/path/to/package'
            mock_package_files.__str__ = MagicMock(return_value=expected_path)
            
            result = get_package_root('test_package')
            
            # Should return the converted path
            self.assertEqual(result, Path(expected_path))
            mock_files.assert_called_once_with('test_package')

    def test_get_package_root_exception_fallback(self):
        """Test get_package_root fallback when importlib.resources fails."""
        with patch('metaeditor_safetensors.services.file_service.resources.files') as mock_files:
            # Mock exception during package resolution
            mock_files.side_effect = Exception("Package not found")
            
            with patch('metaeditor_safetensors.services.file_service.get_project_root') as mock_get_project_root:
                mock_project_root = Path('/project/root')
                mock_get_project_root.return_value = mock_project_root
                
                result = get_package_root('test_package')
                
                # Should fallback to project_root / package_name
                expected_path = mock_project_root / 'test_package'
                self.assertEqual(result, expected_path)
                mock_get_project_root.assert_called_once()

    def test_get_package_root_default_package_name(self):
        """Test get_package_root with default package name."""
        with patch('metaeditor_safetensors.services.file_service.resources.files') as mock_files:
            # Mock successful package resolution
            mock_package_files = MagicMock()
            mock_files.return_value = mock_package_files
            
            # Mock the string conversion to return a valid path string
            expected_path = '/path/to/metaeditor_safetensors'
            mock_package_files.__str__ = MagicMock(return_value=expected_path)
            
            result = get_package_root()  # Use default package name
            
            # Should use default package name
            self.assertEqual(result, Path(expected_path))
            mock_files.assert_called_once_with('metaeditor_safetensors')

    def test_get_package_root_importerror_fallback(self):
        """Test get_package_root fallback when importlib raises ImportError."""
        with patch('metaeditor_safetensors.services.file_service.resources.files') as mock_files:
            # Mock ImportError during package resolution
            mock_files.side_effect = ImportError("No module named 'test_package'")
            
            with patch('metaeditor_safetensors.services.file_service.get_project_root') as mock_get_project_root:
                mock_project_root = Path('/project/root')
                mock_get_project_root.return_value = mock_project_root
                
                result = get_package_root('test_package')
                
                # Should fallback to project_root / package_name
                expected_path = mock_project_root / 'test_package'
                self.assertEqual(result, expected_path)
                mock_get_project_root.assert_called_once()

    def test_get_package_root_modulenotfounderror_fallback(self):
        """Test get_package_root fallback when importlib raises ModuleNotFoundError."""
        with patch('metaeditor_safetensors.services.file_service.resources.files') as mock_files:
            # Mock ModuleNotFoundError during package resolution
            mock_files.side_effect = ModuleNotFoundError("No module named 'test_package'")
            
            with patch('metaeditor_safetensors.services.file_service.get_project_root') as mock_get_project_root:
                mock_project_root = Path('/project/root')
                mock_get_project_root.return_value = mock_project_root
                
                result = get_package_root('test_package')
                
                # Should fallback to project_root / package_name
                expected_path = mock_project_root / 'test_package'
                self.assertEqual(result, expected_path)
                mock_get_project_root.assert_called_once()


if __name__ == "__main__":
    unittest.main()