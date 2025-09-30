import json
import logging
import os
import shutil
import struct
import tempfile
from typing import Any, Dict, List

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

        # Our service automatically adds hash computation
        # Remove the hash field for comparison with original metadata
        expected_metadata = dummy_metadata.copy()
        read_metadata_without_hash = {
            k: v for k, v in read_metadata.items() if k != "modelspec.hash_sha256"
        }

        # Verify hash was added and is in correct format
        assert "modelspec.hash_sha256" in read_metadata
        hash_value = read_metadata["modelspec.hash_sha256"]
        assert hash_value.startswith("0x")
        assert len(hash_value) == 66  # 0x + 64 hex chars

        # Assert that the rest of the metadata is identical
        assert read_metadata_without_hash == expected_metadata, (
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

        # Use synchronous method for testing
        result_filepath = service.write_metadata(our_path, dummy_metadata)

        # Check operation succeeded
        assert result_filepath == our_path

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
        assert "Invalid safetensors file" in str(exc_info.value)

    def test_read_metadata_invalid_header_length(self, service, test_dir):
        """Test when header length field doesn't equal 8 bytes."""
        invalid_header_file = os.path.join(test_dir, "invalid_header.safetensors")
        with open(invalid_header_file, "wb") as f:
            # Write only 6 bytes instead of 8 for the header length
            f.write(b"123456")

        with pytest.raises(ValueError) as exc_info:
            service.read_metadata(invalid_header_file)
        assert "Invalid safetensors file" in str(exc_info.value)

    def test_write_metadata_invalid_header_length(self, service, test_dir):
        """Test write_metadata when header length field doesn't equal 8 bytes during write operation."""
        invalid_header_file = os.path.join(test_dir, "invalid_header_write.safetensors")
        with open(invalid_header_file, "wb") as f:
            # Write only 6 bytes instead of 8 for the header length
            f.write(b"123456")

        # Use synchronous method and expect exception
        with pytest.raises(IOError) as exc_info:
            service.write_metadata(invalid_header_file, {"new": "data"})

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
        result_filepath = service.write_metadata(
            test_filepath,
            {"new": "data"},
            progress_callback=progress_callback,
        )

        # Verify progress was called and ended at 100%
        assert len(progress_calls) > 0
        assert progress_calls[-1] == 100
        assert result_filepath == test_filepath

    def test_write_metadata_cleanup_on_error(
        self, mocker, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test temp file cleanup when write fails."""
        # Create initial file
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)
        temp_file = test_filepath + ".tmp"

        # Mock to cause an error during file operations
        mocker.patch("builtins.open", side_effect=IOError("Simulated write error"))

        # Use synchronous method and expect exception
        with pytest.raises(IOError) as exc_info:
            service.write_metadata(test_filepath, {"new": "data"})

        assert "Simulated write error" in str(exc_info.value)

        # Verify temp file was cleaned up
        assert not os.path.exists(temp_file)

    def test_read_metadata_unexpected_error(
        self, mocker, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test general exception handling in read_metadata."""
        # Create valid file first
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Mock struct.unpack to raise an unexpected error
        mocker.patch(
            "metaeditor_safetensors.services.safetensors_service.struct.unpack",
            side_effect=RuntimeError("Unexpected error"),
        )
        with pytest.raises(ValueError) as exc_info:
            service.read_metadata(test_filepath)
        assert "unexpected error occurred" in str(exc_info.value)

    def test_read_metadata_no_metadata_key(self, service, dummy_tensors, test_filepath):
        """Test reading file that has no __metadata__ key."""
        # Create file without metadata using safetensors directly
        save_file(dummy_tensors, test_filepath)  # No metadata parameter

        # Should return only hash when no __metadata__ key exists
        metadata = service.read_metadata(test_filepath)

        # Should have exactly one key: the computed hash
        assert len(metadata) == 1
        assert "modelspec.hash_sha256" in metadata

        # Verify hash format
        hash_value = metadata["modelspec.hash_sha256"]
        assert hash_value.startswith("0x")
        assert len(hash_value) == 66  # 0x + 64 hex chars

    def test_shutdown_no_worker(self, service):
        """Test shutdown when no worker exists."""
        # Should not raise any errors
        service.shutdown()
        assert service._worker_thread is None
        assert service._save_worker is None

    def test_shutdown_worker_not_running(self, service):
        """Test shutdown when worker exists but not running."""
        from unittest.mock import MagicMock

        # Create a mock thread that's not running
        mock_thread = MagicMock()
        mock_thread.isRunning.return_value = False
        service._worker_thread = mock_thread

        service.shutdown()

        # Should not call quit() since thread is not running
        mock_thread.quit.assert_not_called()
        assert service._worker_thread is None
        assert service._save_worker is None

    def test_read_metadata_progress_callbacks_on_success(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Progress callback should receive 0 at start and 100 at completion."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        progress_values: List[int] = []

        metadata = service.read_metadata(
            test_filepath, progress_callback=lambda value: progress_values.append(value)
        )

        assert progress_values, "Progress callback should be invoked."
        assert progress_values[0] == 0
        assert progress_values[-1] == 100
        assert metadata["author"] == dummy_metadata["author"]

    def test_read_metadata_progress_callback_on_hash_error(
        self, mocker, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """When hash computation fails, progress callback still finishes at 100."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        mocker.patch.object(
            service, "_calculate_hash", side_effect=RuntimeError("hash boom")
        )

        progress_values: List[int] = []

        metadata = service.read_metadata(
            test_filepath, progress_callback=lambda value: progress_values.append(value)
        )

        assert progress_values[0] == 0
        assert progress_values[-1] == 100
        assert "modelspec.hash_sha256" not in metadata

    def test_write_metadata_progress_callback_handles_zero_denominator(
        self, mocker, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Ensure progress callback handles files where denominator becomes zero."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        with open(test_filepath, "rb") as f:
            header_len = struct.unpack("<Q", f.read(8))[0]

        tensor_data_start = 8 + header_len
        real_getsize = os.path.getsize

        def fake_getsize(path: str) -> int:
            size = real_getsize(path)
            if os.path.samefile(path, test_filepath):
                return tensor_data_start
            return size

        mocker.patch(
            "metaeditor_safetensors.services.safetensors_service.os.path.getsize",
            side_effect=fake_getsize,
        )

        progress_values: List[int] = []

        result = service.write_metadata(
            test_filepath,
            {"patched": True},
            progress_callback=lambda value: progress_values.append(value),
        )

        assert result == test_filepath
        assert progress_values
        assert progress_values[-1] == 100

    def test_write_metadata_cleanup_handles_remove_error(
        self, mocker, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Temp file cleanup errors should be suppressed."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        temp_filepath = test_filepath + ".tmp"

        mocker.patch(
            "metaeditor_safetensors.services.safetensors_service.os.path.exists",
            side_effect=lambda path: path == temp_filepath,
        )
        remove_mock = mocker.patch(
            "metaeditor_safetensors.services.safetensors_service.os.remove",
            side_effect=[None, OSError("cleanup failure")],
        )
        mocker.patch(
            "metaeditor_safetensors.services.safetensors_service.open",
            side_effect=IOError("Simulated failure"),
            create=True,
        )

        with pytest.raises(IOError) as exc_info:
            service.write_metadata(test_filepath, {"new": "data"})
        assert "Simulated failure" in str(exc_info.value)
        assert remove_mock.call_count == 2

    def test_calculate_hash_invalid_header_length(self, service, test_dir):
        """_calculate_hash should raise on invalid header length."""
        bad_file = os.path.join(test_dir, "bad_hash.safetensors")
        with open(bad_file, "wb") as f:
            f.write(b"1234")

        with pytest.raises(ValueError) as exc_info:
            service._calculate_hash(bad_file)

        assert "Invalid safetensors file" in str(exc_info.value)

    def test_calculate_hash_progress_reporting(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Progress callback should be notified during hash computation with data."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        progress_values: List[int] = []
        service._calculate_hash(
            test_filepath, progress_callback=lambda value: progress_values.append(value)
        )
        assert progress_values
        assert progress_values[-1] == 100

    def test_calculate_hash_progress_for_empty_tensor_data(self, service, test_dir):
        """Hashing files with no tensor data should immediately report completion."""
        header = json.dumps({"__metadata__": {}}).encode("utf-8")
        filepath = os.path.join(test_dir, "header_only.safetensors")
        with open(filepath, "wb") as f:
            f.write(struct.pack("<Q", len(header)))
            f.write(header)

        progress_values: List[int] = []
        computed_hash = service._calculate_hash(
            filepath, progress_callback=lambda value: progress_values.append(value)
        )

        assert computed_hash.startswith("0x")
        assert progress_values == [100]


class TestSafetensorsServiceAsync:
    """Test async functionality of SafetensorsService."""

    def test_read_metadata_async_success(
        self, service, dummy_tensors, dummy_metadata, test_filepath, qtbot
    ):
        """Ensure async metadata load invokes callbacks and cleans up."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        progress_values = []
        successes = []
        errors = []

        def progress_callback(value: int) -> None:
            progress_values.append(value)

        def success_callback(metadata: Dict[str, Any]) -> None:
            successes.append(metadata)

        def error_callback(message: str) -> None:
            errors.append(message)

        result = service.read_metadata_async(
            test_filepath,
            progress_callback=progress_callback,
            success_callback=success_callback,
            error_callback=error_callback,
        )

        assert result is True

        qtbot.waitUntil(lambda: len(successes) > 0 or len(errors) > 0, timeout=5000)

        assert errors == []
        assert len(successes) == 1
        loaded_metadata = successes[0]
        for key, value in dummy_metadata.items():
            if key != "modelspec.hash_sha256":
                assert loaded_metadata[key] == value
        assert "modelspec.hash_sha256" in loaded_metadata
        assert progress_values
        assert progress_values[0] == 0
        assert progress_values[-1] == 100
        assert not service.is_loading()

    def test_read_metadata_async_error(self, service, qtbot, tmp_path):
        """Async load should report errors when read_metadata fails."""
        missing_file = tmp_path / "missing.safetensors"

        progress_values = []
        successes = []
        errors = []

        def progress_callback(value: int) -> None:
            progress_values.append(value)

        def success_callback(metadata: Dict[str, Any]) -> None:
            successes.append(metadata)

        def error_callback(message: str) -> None:
            errors.append(message)

        result = service.read_metadata_async(
            str(missing_file),
            progress_callback=progress_callback,
            success_callback=success_callback,
            error_callback=error_callback,
        )

        assert result is True

        qtbot.waitUntil(lambda: len(errors) > 0, timeout=5000)

        assert successes == []
        assert errors
        assert "missing" in errors[0].lower() or "no such" in errors[0].lower()
        assert progress_values and progress_values[0] == 0
        assert not service.is_loading()

    def test_read_metadata_async_already_running(self, service, mocker):
        """Starting a second load while one is active should return False."""
        busy_thread = mocker.MagicMock()
        busy_thread.isRunning.return_value = True
        service._load_thread = busy_thread

        result = service.read_metadata_async("/fake/path.safetensors")

        assert result is False
        busy_thread.isRunning.assert_called_once()
        service._load_thread = None

    def test_write_metadata_async_success(
        self, service, dummy_tensors, dummy_metadata, test_filepath, qtbot
    ):
        """Test successful async metadata write."""
        # Create initial file
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Track callback calls
        success_calls = []
        error_calls = []

        def success_callback(filepath):
            success_calls.append(filepath)

        def error_callback(error):
            error_calls.append(error)

        new_metadata = {"new_key": "new_value", "author": "Test Author"}

        # Start async operation
        result = service.write_metadata_async(
            test_filepath,
            new_metadata,
            success_callback=success_callback,
            error_callback=error_callback,
        )

        # Should return True if started successfully
        assert result is True

        # Wait for completion using qtbot
        def check_completion():
            return len(success_calls) > 0 or len(error_calls) > 0

        qtbot.waitUntil(check_completion, timeout=5000)

        # Check results
        assert len(success_calls) == 1
        assert success_calls[0] == test_filepath
        assert len(error_calls) == 0

        # Verify metadata was actually written
        updated_metadata = service.read_metadata(test_filepath)

        # Remove hash for comparison since our service adds it automatically
        updated_metadata_without_hash = {
            k: v for k, v in updated_metadata.items() if k != "modelspec.hash_sha256"
        }
        assert updated_metadata_without_hash == new_metadata

        # Verify hash was added
        assert "modelspec.hash_sha256" in updated_metadata

    def test_write_metadata_async_already_running(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test that starting async operation while one is running returns False."""
        # Create initial file
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Start first operation
        result1 = service.write_metadata_async(test_filepath, {"first": "data"})
        assert result1 is True

        # Try to start second operation while first is running
        result2 = service.write_metadata_async(test_filepath, {"second": "data"})
        assert result2 is False

        # Clean up
        if service._worker_thread:
            service._worker_thread.quit()
            service._worker_thread.wait(5000)

    def test_is_saving(self, service, dummy_tensors, dummy_metadata, test_filepath):
        """Test is_saving() method."""
        # Create initial file
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Initially not saving
        assert not service.is_saving()

        # Start operation
        result = service.write_metadata_async(test_filepath, {"new": "data"})
        assert result is True

        # Wait for completion
        if service._worker_thread:
            service._worker_thread.quit()
            service._worker_thread.wait(5000)

        # Should not be saving after completion
        assert not service.is_saving()

    def test_write_metadata_async_no_callbacks(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test async operation with no callbacks provided."""
        # Create initial file
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Start async operation with no callbacks
        result = service.write_metadata_async(
            test_filepath,
            {"new": "data"},
            # All callbacks are None (default)
        )

        # Should return True if started successfully
        assert result is True

        # Wait for completion
        if service._worker_thread:
            service._worker_thread.quit()
            service._worker_thread.wait(5000)

        # Verify metadata was written even without callbacks
        updated_metadata = service.read_metadata(test_filepath)

        # Remove hash for comparison since our service adds it automatically
        updated_metadata_without_hash = {
            k: v for k, v in updated_metadata.items() if k != "modelspec.hash_sha256"
        }
        assert updated_metadata_without_hash == {"new": "data"}

        # Verify hash was added
        assert "modelspec.hash_sha256" in updated_metadata

    def test_write_metadata_async_progress_callback_invoked(
        self, service, dummy_tensors, dummy_metadata, test_filepath, qtbot
    ):
        """Progress callback provided to async write should receive updates."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        progress_values: List[int] = []
        success_calls: List[str] = []
        error_calls: List[str] = []

        result = service.write_metadata_async(
            test_filepath,
            {"updated": True},
            progress_callback=lambda value: progress_values.append(value),
            success_callback=lambda path: success_calls.append(path),
            error_callback=lambda message: error_calls.append(message),
        )

        assert result is True

        qtbot.waitUntil(lambda: bool(success_calls or error_calls), timeout=5000)

        assert error_calls == []
        assert success_calls == [test_filepath]
        assert progress_values
        assert progress_values[-1] == 100

    def test_shutdown_waits_for_running_threads(self, service, mocker):
        """Shutdown should call quit/wait on active threads."""
        load_thread = mocker.Mock()
        load_thread.isRunning.return_value = True
        worker_thread = mocker.Mock()
        worker_thread.isRunning.return_value = True

        service._load_thread = load_thread
        service._worker_thread = worker_thread

        service.shutdown()

        load_thread.quit.assert_called_once()
        load_thread.wait.assert_called_once_with(5000)
        worker_thread.quit.assert_called_once()
        worker_thread.wait.assert_called_once_with(5000)


class TestSafetensorsServiceHashFunctionality:
    """Test hash computation functionality specifically."""

    def test_hash_computation_consistency(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test that hash computation is consistent across multiple calls."""
        # Create test file
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Read metadata multiple times
        metadata1 = service.read_metadata(test_filepath)
        metadata2 = service.read_metadata(test_filepath)
        metadata3 = service.read_metadata(test_filepath)

        # Hash should be consistent
        hash1 = metadata1["modelspec.hash_sha256"]
        hash2 = metadata2["modelspec.hash_sha256"]
        hash3 = metadata3["modelspec.hash_sha256"]

        assert hash1 == hash2 == hash3
        assert hash1.startswith("0x")
        assert len(hash1) == 66  # 0x + 64 hex chars
        assert all(c in "0123456789abcdef" for c in hash1[2:])  # All lowercase hex

    def test_hash_format_validation(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test that computed hash follows ModelSpec format."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)
        metadata = service.read_metadata(test_filepath)

        hash_value = metadata["modelspec.hash_sha256"]

        # Verify ModelSpec format: 0x prefix + lowercase hex
        assert hash_value.startswith("0x")
        assert len(hash_value) == 66  # 0x + 64 hex characters

        # Verify all characters after 0x are lowercase hexadecimal
        hex_part = hash_value[2:]
        assert all(c in "0123456789abcdef" for c in hex_part)

        # Verify no uppercase characters
        assert hex_part == hex_part.lower()

    def test_hash_mismatch_warning(self, caplog, service, dummy_tensors, test_dir):
        """Test that hash mismatches are logged as warnings."""
        test_filepath = os.path.join(test_dir, "mismatch_test.safetensors")

        # Create a file with correct metadata but incorrect hash
        wrong_hash_metadata = {
            "author": "Test",
            "modelspec.hash_sha256": "0xwrongwrongwrongwrongwrongwrongwrongwrongwrongwrongwrongwrong",
        }
        save_file(dummy_tensors, test_filepath, metadata=wrong_hash_metadata)

        # Read the file - should log a warning about hash mismatch
        with caplog.at_level(logging.WARNING):
            metadata = service.read_metadata(test_filepath)

        # Should have logged a hash mismatch warning
        assert any("Hash mismatch" in record.message for record in caplog.records)

        # Should still return the correct computed hash
        assert "modelspec.hash_sha256" in metadata
        assert (
            metadata["modelspec.hash_sha256"]
            != wrong_hash_metadata["modelspec.hash_sha256"]
        )
        assert metadata["modelspec.hash_sha256"].startswith("0x")

    def test_hash_computation_with_different_tensor_data(
        self, service, dummy_metadata, test_dir
    ):
        """Test that different tensor data produces different hashes."""
        test_filepath1 = os.path.join(test_dir, "tensors1.safetensors")
        test_filepath2 = os.path.join(test_dir, "tensors2.safetensors")

        # Create two files with different tensor data
        tensors1 = {"weight": np.array([1, 2, 3])}
        tensors2 = {"weight": np.array([4, 5, 6])}

        save_file(tensors1, test_filepath1, metadata=dummy_metadata)
        save_file(tensors2, test_filepath2, metadata=dummy_metadata)

        # Read metadata from both files
        metadata1 = service.read_metadata(test_filepath1)
        metadata2 = service.read_metadata(test_filepath2)

        # Hashes should be different for different tensor data
        hash1 = metadata1["modelspec.hash_sha256"]
        hash2 = metadata2["modelspec.hash_sha256"]

        assert hash1 != hash2
        assert hash1.startswith("0x")
        assert hash2.startswith("0x")

    def test_hash_computation_error_handling(
        self, caplog, mocker, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test error handling during hash computation."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Mock hashlib to raise an error
        mocker.patch(
            "hashlib.sha256", side_effect=RuntimeError("Hash computation failed")
        )

        # Should still return metadata without crashing, but log a warning
        with caplog.at_level(logging.WARNING):
            metadata = service.read_metadata(test_filepath)

        # Should have logged a warning about hash computation failure
        assert any(
            "Could not compute hash for file" in record.message
            for record in caplog.records
        )

        # Should still return the other metadata
        assert "author" in metadata  # Original metadata should still be present

        # Hash field should not be present due to computation error
        assert "modelspec.hash_sha256" not in metadata

    def test_hash_preserved_during_write(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test that hash is properly updated when metadata is written."""
        # Create initial file
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Read to get initial hash
        initial_metadata = service.read_metadata(test_filepath)
        initial_hash = initial_metadata["modelspec.hash_sha256"]

        # Write new metadata (tensor data unchanged)
        new_metadata = {"author": "New Author", "version": "2.0"}
        service.write_metadata(test_filepath, new_metadata)

        # Read again - hash should be the same since tensor data didn't change
        updated_metadata = service.read_metadata(test_filepath)
        updated_hash = updated_metadata["modelspec.hash_sha256"]

        # Hash should be identical (same tensor data)
        assert updated_hash == initial_hash

        # But other metadata should be updated
        assert updated_metadata["author"] == "New Author"
        assert updated_metadata["version"] == "2.0"

    def test_direct_hash_calculation_method(
        self, service, dummy_tensors, dummy_metadata, test_filepath
    ):
        """Test the _calculate_hash method directly."""
        save_file(dummy_tensors, test_filepath, metadata=dummy_metadata)

        # Call the private method directly
        computed_hash = service._calculate_hash(test_filepath)

        # Verify format
        assert computed_hash.startswith("0x")
        assert len(computed_hash) == 66

        # Should match what read_metadata returns
        metadata = service.read_metadata(test_filepath)
        assert metadata["modelspec.hash_sha256"] == computed_hash
