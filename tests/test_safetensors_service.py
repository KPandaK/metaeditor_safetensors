import os
import shutil
import tempfile
from unittest.mock import mock_open, patch

import numpy as np
import pytest
from safetensors import safe_open
from safetensors.numpy import load_file, save_file

from metaeditor_safetensors.services.safetensors_service import SafetensorsService


@pytest.fixture
def test_dir():
    """Set up a temporary directory for test files."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    # Remove the temporary directory after tests
    shutil.rmtree(test_dir)


@pytest.fixture
def service():
    """Create a SafetensorsService instance."""
    return SafetensorsService()


@pytest.fixture
def dummy_tensors():
    """Create dummy tensor data for testing."""
    return {
        "weight1": np.array([1, 2, 3]),
        "weight2": np.array([[4, 5], [6, 7]], dtype=np.float32),
    }


@pytest.fixture
def dummy_metadata():
    """Create dummy metadata for testing."""
    return {
        "author": "Test Suite",
        "license": "MIT",
        "description": "A file generated for compatibility testing.",
    }


@pytest.fixture
def test_filepath(test_dir):
    """Create a test file path."""
    return os.path.join(test_dir, "format_test.safetensors")


class TestSafetensorsService:
    """
    Tests that our custom SafetensorService can correctly read and write files
    compatible with the official safetensors library.
    """

    def test_read_compatibility(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """
        Verify metadata reader is compatible with the safetensors file format.
        """
        # Save a file using the official library
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Read the metadata using our custom service
        read_metadata = service.read_metadata(test_filepath)

        # Assert that the metadata is identical
        assert read_metadata == dummy_metadata, (
            "READ FAILED: The metadata read does not match the safetensors file format."
        )

    def test_write_equivalency(self, service, dummy_tensors, dummy_metadata, test_dir):
        """
        Verify metadata writer is compatible with the numpy save function.
        """
        # 1. Define paths for the two files we will compare
        their_path = os.path.join(test_dir, "theirs.safetensors")
        our_path = os.path.join(test_dir, "ours.safetensors")

        # 2. Create the first file using the official library
        save_file(dummy_tensors, their_path, metadata=dummy_metadata)

        # 3. Create the second file using our service.
        # Our service modifies an existing file, so we first create a base
        # file (it can be a copy of the official one or a new one).
        shutil.copy(their_path, our_path)
        # Now, "save" the metadata into it using our service.
        service.write_metadata(our_path, dummy_metadata)

        # 4. Load both files back using the official library
        tensors_theirs = load_file(their_path)
        tensors_ours = load_file(our_path)

        # Read metadata separately using safe_open
        with safe_open(their_path, framework="numpy") as f:
            metadata_theirs = f.metadata()

        with safe_open(our_path, framework="numpy") as f:
            metadata_ours = f.metadata()

        # 5. Assert that metadata is identical
        assert metadata_theirs == metadata_ours, (
            "WRITE FAILED: The metadata does not match the numpy library's output."
        )

        # 6. Assert that tensor data is identical
        assert len(tensors_theirs) == len(tensors_ours), (
            "WRITE FAILED: The number of tensors changed between numpy's save and our save."
        )

        for key, their_tensor in tensors_theirs.items():
            assert key in tensors_ours, (
                f"WRITE FAILED: Tensor '{key}' is missing from our service's output."
            )
            our_tensor = tensors_ours[key]
            np.testing.assert_array_equal(
                their_tensor,
                our_tensor,
                f"WRITE FAILED: Tensor '{key}' was corrupted by our service's save operation.",
            )

    def test_read_metadata_file_not_found(self, service):
        """Test FileNotFoundError handling when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            service.read_metadata("nonexistent_file.safetensors")

    def test_read_metadata_file_too_small(self, service, test_dir):
        """Test file too small error handling."""
        # Create a file with less than 8 bytes
        tiny_file = os.path.join(test_dir, "tiny.safetensors")
        with open(tiny_file, "wb") as f:
            f.write(b"tiny")  # Only 4 bytes

        with pytest.raises(ValueError) as exc_info:
            service.read_metadata(tiny_file)
        assert "too small" in str(exc_info.value)

    def test_read_metadata_invalid_header_length(self, service, test_dir):
        """Test when header length field doesn't equal 8 bytes."""
        invalid_header_file = os.path.join(test_dir, "invalid_header.safetensors")
        with open(invalid_header_file, "wb") as f:
            # Write only 6 bytes instead of 8 for the header length
            f.write(b"123456")

        with pytest.raises(ValueError) as exc_info:
            service.read_metadata(invalid_header_file)
        assert "too small" in str(exc_info.value)

    def test_write_metadata_invalid_header_length(self, service, test_dir):
        """Test write_metadata when header length field doesn't equal 8 bytes during write operation."""
        invalid_header_file = os.path.join(test_dir, "invalid_header_write.safetensors")
        with open(invalid_header_file, "wb") as f:
            # Write only 6 bytes instead of 8 for the header length
            f.write(b"123456")

        with pytest.raises(IOError) as exc_info:
            service.write_metadata(invalid_header_file, {"new": "data"})
        assert "Failed to save file" in str(exc_info.value)
        assert "Invalid safetensors file" in str(exc_info.value)

    def test_read_metadata_truncated_header(self, service, test_dir):
        """Test truncated header error handling."""
        truncated_file = os.path.join(test_dir, "truncated.safetensors")
        with open(truncated_file, "wb") as f:
            # Write valid 8-byte header length indicating 100 bytes
            f.write((100).to_bytes(8, "little"))
            # But only write 10 bytes instead of 100
            f.write(b"short_data")

        with pytest.raises(ValueError) as exc_info:
            service.read_metadata(truncated_file)
        assert "truncated" in str(exc_info.value)

    def test_read_metadata_invalid_json(self, service, test_dir):
        """Test JSON decode error handling."""
        invalid_json_file = os.path.join(test_dir, "invalid_json.safetensors")
        invalid_json = b"invalid json content"

        with open(invalid_json_file, "wb") as f:
            # Write header length
            f.write(len(invalid_json).to_bytes(8, "little"))
            # Write invalid JSON
            f.write(invalid_json)

        with pytest.raises(ValueError) as exc_info:
            service.read_metadata(invalid_json_file)
        assert "Failed to parse JSON" in str(exc_info.value)

    def test_write_metadata_with_progress_callback(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test progress callback functionality."""
        # Create initial file
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        progress_calls = []

        def progress_callback(progress):
            progress_calls.append(progress)

        # Test with callback
        result = service.write_metadata(
            test_filepath, {"new": "data"}, progress_callback
        )

        # Verify progress was called and ended at 100%
        assert len(progress_calls) > 0
        assert progress_calls[-1] == 100
        assert result == test_filepath

    def test_write_metadata_cleanup_on_error(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test temp file cleanup when write fails."""
        # Create initial file
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)
        temp_file = test_filepath + ".tmp"

        # Mock to cause an error during file operations
        with patch("builtins.open", side_effect=IOError("Simulated write error")):
            with pytest.raises(IOError) as exc_info:
                service.write_metadata(test_filepath, {"new": "data"})
            assert "Failed to save file" in str(exc_info.value)

        # Verify temp file was cleaned up
        assert not os.path.exists(temp_file)

    def test_read_metadata_unexpected_error(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test general exception handling in read_metadata."""
        # Create valid file first
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Mock struct.unpack to raise an unexpected error
        with patch(
            "metaeditor_safetensors.services.safetensors_service.struct.unpack",
            side_effect=RuntimeError("Unexpected error"),
        ):
            with pytest.raises(ValueError) as exc_info:
                service.read_metadata(test_filepath)
            assert "unexpected error occurred" in str(exc_info.value)
