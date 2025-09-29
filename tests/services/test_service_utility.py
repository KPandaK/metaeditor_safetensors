import base64
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap

from metaeditor_safetensors.services.utility import (
    data_uri_to_pixmap,
    filepath_to_data_uri,
    get_package_root,
    get_project_root,
    pixmap_to_data_uri,
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

    for temp_dir in created_dirs:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)


@pytest.fixture
def temp_dir():
    """Set up test fixtures."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up temporary files
    shutil.rmtree(temp_dir, ignore_errors=True)


def create_test_image(
    temp_dir: str, filename: str, image_format: str = "PNG", size: tuple = (100, 100)
) -> str:
    """
    Create a test image file for testing.

    Args:
        temp_dir: Temporary directory path
        filename: Name of the file to create
        image_format: Image format (PNG, JPEG, etc.)
        size: Image size as (width, height)

    Returns:
        Full path to the created test image
    """
    # Create a simple test image
    pixmap = QPixmap(size[0], size[1])
    pixmap.fill(Qt.GlobalColor.red)

    # Add some content to make it a valid image
    painter = QPainter(pixmap)
    painter.setPen(Qt.GlobalColor.blue)
    painter.drawRect(10, 10, size[0] - 20, size[1] - 20)
    painter.end()

    filepath = os.path.join(temp_dir, filename)
    pixmap.save(filepath, image_format)
    return filepath


class TestFileUtilities:
    """Test cases for file utility functionality."""

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
        assert result.resolve() == root_path.resolve()

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
        assert result.resolve() == root_path.resolve()

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
        assert result.resolve() == root_path.resolve()

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
        assert result.resolve() == start_path.resolve()

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
        assert result.resolve() == root_path.resolve()

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
        assert result.resolve() == expected_path.resolve()

    def test_get_package_root_success(self, mocker):
        """Test get_package_root with successful importlib.resources call."""
        mock_files = mocker.patch(
            "metaeditor_safetensors.services.utility.resources.files"
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
            "metaeditor_safetensors.services.utility.resources.files"
        )
        # Mock exception during package resolution
        mock_files.side_effect = Exception("Package not found")

        mock_get_project_root = mocker.patch(
            "metaeditor_safetensors.services.utility.get_project_root"
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
            "metaeditor_safetensors.services.utility.resources.files"
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

    def test_get_package_root_import_error_fallback(self, mocker):
        """Test get_package_root fallback when importlib raises import-related errors."""
        mock_files = mocker.patch(
            "metaeditor_safetensors.services.utility.resources.files"
        )

        mock_get_project_root = mocker.patch(
            "metaeditor_safetensors.services.utility.get_project_root"
        )
        mock_project_root = Path("/project/root")
        mock_get_project_root.return_value = mock_project_root

        # Test ImportError
        mock_files.side_effect = ImportError("No module named 'test_package'")
        result = get_package_root("test_package")
        expected_path = mock_project_root / "test_package"
        assert result == expected_path

        # Test ModuleNotFoundError (subclass of ImportError)
        mock_files.side_effect = ModuleNotFoundError("No module named 'test_package'")
        result = get_package_root("test_package")
        assert result == expected_path

        mock_get_project_root.assert_called()


class TestImageUtilities:
    """Test cases for image utility functionality."""

    def test_image_to_data_uri_png_input(self, qapp, temp_dir):
        """Test converting a PNG file to WEBP data URI."""
        # Create a test PNG file
        png_file = create_test_image(temp_dir, "test.png", "PNG")

        # Convert to data URI
        data_uri = filepath_to_data_uri(png_file)

        # Verify the result
        assert data_uri.startswith("data:image/webp;base64,")
        assert "base64," in data_uri

        # Verify the base64 part is valid
        base64_part = data_uri.split("base64,")[1]
        try:
            decoded = base64.b64decode(base64_part)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Failed to decode base64 data: {e}")

    def test_image_to_data_uri_bmp_input(self, qapp, temp_dir):
        """Test converting a BMP file to JPEG data URI."""
        # Create a test BMP file
        bmp_file = create_test_image(temp_dir, "test.bmp", "BMP")

        # Convert to data URI
        data_uri = filepath_to_data_uri(bmp_file)

        # Verify always outputs WEBP format
        assert data_uri.startswith("data:image/webp;base64,")

    def test_image_to_data_uri_jpeg_input(self, qapp, temp_dir):
        """Test converting a JPEG file (should still output JPEG)."""
        # Create a test JPEG file
        jpeg_file = create_test_image(temp_dir, "test.jpg", "JPEG")

        # Convert to data URI
        data_uri = filepath_to_data_uri(jpeg_file)

        # Verify outputs WEBP format
        assert data_uri.startswith("data:image/webp;base64,")

    def test_image_to_data_uri_nonexistent_file(self, qapp, temp_dir):
        """Test error handling for non-existent files."""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.png")

        with pytest.raises(ValueError):
            filepath_to_data_uri(nonexistent_file)

    def test_image_to_data_uri_invalid_file(self, qapp, temp_dir):
        """Test error handling for invalid image files."""
        # Create a text file with image extension
        invalid_file = os.path.join(temp_dir, "invalid.png")
        with open(invalid_file, "w") as f:
            f.write("This is not an image file")

        with pytest.raises(ValueError):
            filepath_to_data_uri(invalid_file)

    def test_data_uri_to_pixmap_valid(self, qapp, temp_dir):
        """Test converting a valid data URI to QPixmap."""
        # First create a data URI from a test image
        png_file = create_test_image(temp_dir, "test.png", "PNG")
        data_uri = filepath_to_data_uri(png_file)

        # Convert back to pixmap
        pixmap = data_uri_to_pixmap(data_uri)

        # Verify the result
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0

    def test_data_uri_to_pixmap_invalid(self, qapp):
        """Test data_uri_to_pixmap with invalid input."""
        # Test with invalid data URI
        invalid_uri = "data:image/jpeg;base64,invalid_base64_data"
        pixmap = data_uri_to_pixmap(invalid_uri)
        assert pixmap is None

    def test_data_uri_to_pixmap_empty(self, qapp):
        """Test data_uri_to_pixmap with empty input."""
        # Test with empty string
        pixmap = data_uri_to_pixmap("")
        assert pixmap is None

    def test_data_uri_to_pixmap_malformed(self, qapp):
        """Test data_uri_to_pixmap with malformed data URI."""
        # Test without base64 marker
        malformed_uri = "data:image/jpeg;notbase64"
        pixmap = data_uri_to_pixmap(malformed_uri)
        assert pixmap is None

    def test_round_trip_conversion(self, qapp, temp_dir):
        """Test full round-trip: image file -> data URI -> pixmap."""
        # Create a test image
        original_file = create_test_image(temp_dir, "original.png", "PNG", (50, 75))

        # Convert to data URI
        data_uri = filepath_to_data_uri(original_file)

        # Convert back to pixmap
        pixmap = data_uri_to_pixmap(data_uri)

        # Verify the pixmap is valid and has reasonable dimensions
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0

    def test_webp_compression_quality(self, qapp, temp_dir):
        """Test that WEBP compression is applied with reasonable quality."""
        # Create a larger test image for better compression testing
        large_file = create_test_image(temp_dir, "large.png", "PNG", (400, 300))

        # Convert to data URI
        data_uri = filepath_to_data_uri(large_file)

        # Decode the base64 to check size
        base64_part = data_uri.split("base64,")[1]
        image_bytes = base64.b64decode(base64_part)

        # Verify we have a reasonable file size
        # WEBP is very efficient, so even a 400x300 simple image might be quite small
        assert len(image_bytes) > 50  # Should be larger than 50 bytes for a valid image
        assert (
            len(image_bytes) < 50000
        )  # But shouldn't be ridiculously large for our simple test image

        # Verify the image is actually valid by converting it back to a pixmap
        pixmap = data_uri_to_pixmap(data_uri)
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0

    def test_pixmap_to_data_uri_valid_pixmap(self, qapp):
        """Test converting a valid QPixmap to data URI."""
        # Create a test pixmap
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.GlobalColor.blue)

        # Add some content
        painter = QPainter(pixmap)
        painter.setPen(Qt.GlobalColor.yellow)
        painter.drawEllipse(20, 20, 60, 60)
        painter.end()

        # Convert to data URI
        data_uri = pixmap_to_data_uri(pixmap)

        # Verify the result
        assert data_uri.startswith("data:image/png;base64,")
        assert "base64," in data_uri
        assert len(data_uri) > 50  # Should have meaningful content

        # Verify the base64 part is valid
        base64_part = data_uri.split("base64,")[1]
        try:
            decoded = base64.b64decode(base64_part)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Failed to decode base64 data: {e}")

    def test_pixmap_to_data_uri_null_pixmap(self, qapp):
        """Test pixmap_to_data_uri with null/invalid pixmap."""
        # Create a null pixmap
        null_pixmap = QPixmap()

        # Convert to data URI
        data_uri = pixmap_to_data_uri(null_pixmap)

        # Should return empty string for null pixmap
        assert data_uri == ""

    def test_pixmap_to_data_uri_round_trip(self, qapp):
        """Test round-trip: pixmap -> data URI -> pixmap."""
        # Create original pixmap with specific content
        original_pixmap = QPixmap(80, 60)
        original_pixmap.fill(Qt.GlobalColor.green)

        # Add distinctive content
        painter = QPainter(original_pixmap)
        painter.setPen(Qt.GlobalColor.red)
        painter.drawLine(0, 0, 80, 60)
        painter.drawLine(0, 60, 80, 0)
        painter.end()

        # Convert to data URI and back
        data_uri = pixmap_to_data_uri(original_pixmap)
        converted_pixmap = data_uri_to_pixmap(data_uri)

        # Verify the converted pixmap is valid
        assert converted_pixmap is not None
        assert not converted_pixmap.isNull()
        assert converted_pixmap.width() == 80
        assert converted_pixmap.height() == 60

    def test_pixmap_to_data_uri_large_pixmap(self, qapp):
        """Test pixmap_to_data_uri with a larger pixmap."""
        # Create a larger pixmap
        large_pixmap = QPixmap(500, 300)
        large_pixmap.fill(Qt.GlobalColor.white)

        # Add some complex content
        painter = QPainter(large_pixmap)
        painter.setPen(Qt.GlobalColor.black)
        for i in range(0, 500, 20):
            painter.drawLine(i, 0, i, 300)
        for i in range(0, 300, 15):
            painter.drawLine(0, i, 500, i)
        painter.end()

        # Convert to data URI
        data_uri = pixmap_to_data_uri(large_pixmap)

        # Verify the result
        assert data_uri.startswith("data:image/png;base64,")
        assert len(data_uri) > 1000  # Should be substantial for a complex image

        # Verify it can be decoded back
        converted_pixmap = data_uri_to_pixmap(data_uri)
        assert converted_pixmap is not None
        assert not converted_pixmap.isNull()

    def test_pixmap_save_failure(self, qapp, mocker, temp_dir):
        """Test error handling when QPixmap.save() fails."""
        # Create a mock pixmap that fails to save
        mock_pixmap = mocker.MagicMock()
        mock_pixmap.isNull.return_value = False
        mock_pixmap.save.return_value = False  # Simulate save failure
        mocker.patch(
            "metaeditor_safetensors.services.utility.QPixmap",
            return_value=mock_pixmap,
        )

        # Create a test file (content doesn't matter since we're mocking)
        test_file = os.path.join(temp_dir, "test.png")
        with open(test_file, "wb") as f:
            f.write(b"fake image data")

        # Test that conversion raises an appropriate error
        with pytest.raises(ValueError) as exc_info:
            filepath_to_data_uri(test_file)

        assert "Failed to convert image to WebP" in str(exc_info.value)
