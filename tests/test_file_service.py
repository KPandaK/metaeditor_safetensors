"""
Unit tests for File Service
============================

Tests for file and path utilities including project root detection
and package root resolution.
"""

import tempfile
from pathlib import Path

import pytest

from metaeditor_safetensors.services.file_service import (
    get_package_root,
    get_project_root,
)


@pytest.fixture
def temp_structure_factory():
    """Factory to create temporary directory structures for testing."""
    created_dirs = []

    def _create_temp_structure(files_and_dirs):
        """Create a temporary directory structure with specified files and directories.

        Args:
            files_and_dirs: List where items are either:
                - str ending with '/' for directories
                - str for files

        Returns:
            Path to the root of the created structure
        """
        import shutil

        temp_dir = tempfile.mkdtemp()
        created_dirs.append(temp_dir)
        temp_path = Path(temp_dir)

        for item in files_and_dirs:
            if item.endswith("/"):
                # Directory
                (temp_path / item.rstrip("/")).mkdir(parents=True, exist_ok=True)
            else:
                # File
                file_path = temp_path / item
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()

        return temp_path

    yield _create_temp_structure

    # Cleanup
    import shutil

    for temp_dir in created_dirs:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)


class TestFileService:
    """Test cases for file service functionality."""

    def test_get_project_root_with_pyproject_toml(self, temp_structure_factory):
        """Test get_project_root finds project root with pyproject.toml marker."""
        # Create temporary structure with pyproject.toml
        root_path = temp_structure_factory(
            ["pyproject.toml", "src/", "src/subdir/", "src/subdir/file.py"]
        )

        # Test from subdirectory
        start_path = root_path / "src" / "subdir"
        result = get_project_root(start_path)

        # Should find the root with pyproject.toml
        assert result == root_path

    def test_get_project_root_with_git_marker(self, temp_structure_factory):
        """Test get_project_root finds project root with .git marker."""
        # Create temporary structure with .git
        root_path = temp_structure_factory(
            [".git/", "src/", "src/subdir/", "src/subdir/file.py"]
        )

        # Test from subdirectory
        start_path = root_path / "src" / "subdir"
        result = get_project_root(start_path)

        # Should find the root with .git
        assert result == root_path

    def test_get_project_root_with_justfile_marker(self, temp_structure_factory):
        """Test get_project_root finds project root with justfile marker."""
        # Create temporary structure with justfile
        root_path = temp_structure_factory(
            ["justfile", "src/", "src/subdir/", "src/subdir/file.py"]
        )

        # Test from subdirectory
        start_path = root_path / "src" / "subdir"
        result = get_project_root(start_path)

        # Should find the root with justfile
        assert result == root_path

    def test_get_project_root_no_markers_found(self, temp_structure_factory):
        """Test get_project_root fallback when no markers are found."""
        # Create temporary structure without any markers
        root_path = temp_structure_factory(
            ["src/", "src/subdir/", "src/subdir/file.py"]
        )

        # Test from subdirectory
        start_path = root_path / "src" / "subdir"
        result = get_project_root(start_path)

        # Should return the start path as fallback
        assert result == start_path

    def test_get_project_root_multiple_markers(self, temp_structure_factory):
        """Test get_project_root with multiple markers (finds first one)."""
        # Create temporary structure with multiple markers
        root_path = temp_structure_factory(
            [
                "pyproject.toml",
                ".git/",
                "justfile",
                "src/",
                "src/subdir/",
                "src/subdir/file.py",
            ]
        )

        # Test from subdirectory
        start_path = root_path / "src" / "subdir"
        result = get_project_root(start_path)

        # Should find the root (order in markers list determines which is found first)
        assert result == root_path

    def test_get_project_root_default_cwd(self, mocker):
        """Test get_project_root uses current working directory when start_path is None."""
        mock_cwd = mocker.patch("pathlib.Path.cwd")
        mock_cwd.return_value = Path("/test/current/dir")

        mock_exists = mocker.patch.object(Path, "exists")
        # Mock no markers found
        mock_exists.return_value = False

        result = get_project_root(None)

        # Should use cwd as fallback when no markers found
        assert result == Path("/test/current/dir")
        mock_cwd.assert_called_once()

    def test_get_project_root_nested_markers(self, temp_structure_factory):
        """Test get_project_root finds the closest marker going up the tree."""
        # Create structure with nested markers
        root_path = temp_structure_factory(
            [
                "pyproject.toml",
                "src/",
                "src/nested/",
                "src/nested/.git/",
                "src/nested/subdir/",
                "src/nested/subdir/file.py",
            ]
        )

        # Test from deepest subdirectory
        start_path = root_path / "src" / "nested" / "subdir"
        result = get_project_root(start_path)

        # Should find the closest .git directory first (in src/nested/)
        expected_path = root_path / "src" / "nested"
        assert result == expected_path

    def test_get_package_root_success(self, mocker):
        """Test get_package_root with successful importlib.resources call."""
        mock_files = mocker.patch(
            "metaeditor_safetensors.services.file_service.resources.files"
        )
        # Mock successful package resolution
        mock_package_files = mocker.MagicMock()
        mock_files.return_value = mock_package_files

        # Mock the string conversion to return a valid path string
        expected_path = "/path/to/package"
        mock_package_files.__str__ = mocker.MagicMock(return_value=expected_path)

        result = get_package_root("test_package")

        # Should return the converted path
        assert result == Path(expected_path)
        mock_files.assert_called_once_with("test_package")

    def test_get_package_root_exception_fallback(self, mocker):
        """Test get_package_root fallback when importlib.resources fails."""
        mock_files = mocker.patch(
            "metaeditor_safetensors.services.file_service.resources.files"
        )
        # Mock exception during package resolution
        mock_files.side_effect = Exception("Package not found")

        mock_get_project_root = mocker.patch(
            "metaeditor_safetensors.services.file_service.get_project_root"
        )
        mock_project_root = Path("/project/root")
        mock_get_project_root.return_value = mock_project_root

        result = get_package_root("test_package")

        # Should fallback to project_root / package_name
        expected_path = mock_project_root / "test_package"
        assert result == expected_path
        mock_get_project_root.assert_called_once()

    def test_get_package_root_default_package_name(self, mocker):
        """Test get_package_root with default package name."""
        mock_files = mocker.patch(
            "metaeditor_safetensors.services.file_service.resources.files"
        )
        # Mock successful package resolution
        mock_package_files = mocker.MagicMock()
        mock_files.return_value = mock_package_files

        # Mock the string conversion to return a valid path string
        expected_path = "/path/to/metaeditor_safetensors"
        mock_package_files.__str__ = mocker.MagicMock(return_value=expected_path)

        result = get_package_root()  # Use default package name

        # Should use default package name
        assert result == Path(expected_path)
        mock_files.assert_called_once_with("metaeditor_safetensors")

    def test_get_package_root_importerror_fallback(self, mocker):
        """Test get_package_root fallback when importlib raises ImportError."""
        mock_files = mocker.patch(
            "metaeditor_safetensors.services.file_service.resources.files"
        )
        # Mock ImportError during package resolution
        mock_files.side_effect = ImportError("No module named 'test_package'")

        mock_get_project_root = mocker.patch(
            "metaeditor_safetensors.services.file_service.get_project_root"
        )
        mock_project_root = Path("/project/root")
        mock_get_project_root.return_value = mock_project_root

        result = get_package_root("test_package")

        # Should fallback to project_root / package_name
        expected_path = mock_project_root / "test_package"
        assert result == expected_path
        mock_get_project_root.assert_called_once()

    def test_get_package_root_modulenotfounderror_fallback(self, mocker):
        """Test get_package_root fallback when importlib raises ModuleNotFoundError."""
        mock_files = mocker.patch(
            "metaeditor_safetensors.services.file_service.resources.files"
        )
        # Mock ModuleNotFoundError during package resolution
        mock_files.side_effect = ModuleNotFoundError("No module named 'test_package'")

        mock_get_project_root = mocker.patch(
            "metaeditor_safetensors.services.file_service.get_project_root"
        )
        mock_project_root = Path("/project/root")
        mock_get_project_root.return_value = mock_project_root

        result = get_package_root("test_package")

        # Should fallback to project_root / package_name
        expected_path = mock_project_root / "test_package"
        assert result == expected_path
        mock_get_project_root.assert_called_once()
