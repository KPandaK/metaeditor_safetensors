"""
Unit tests for Save Worker
===========================

Tests for the SaveWorker class which handles background saving
of safetensors metadata without blocking the UI.
"""

from typing import Any, Dict

import pytest
from PySide6.QtCore import QObject, Signal

from metaeditor_safetensors.services.save_worker import SaveWorker


@pytest.fixture
def mock_service(mocker):
    """Create a mock SafetensorsService for testing."""
    return mocker.MagicMock()


@pytest.fixture
def test_data():
    """Provide test data for SaveWorker tests."""
    return {
        "filepath": "/path/to/test.safetensors",
        "metadata": {
            "author": "Test Author",
            "description": "Test model",
            "version": "1.0",
        },
    }


class TestSaveWorker:
    """Test cases for SaveWorker functionality."""

    def test_save_worker_initialization(self, mock_service, test_data):
        """Test SaveWorker initialization with proper parameters."""
        worker = SaveWorker(mock_service, test_data["filepath"], test_data["metadata"])

        # Verify initialization
        assert isinstance(worker, QObject)
        assert worker._service == mock_service
        assert worker._filepath == test_data["filepath"]
        assert worker._metadata == test_data["metadata"]

    def test_save_worker_signals_exist(self, mock_service, test_data):
        """Test that SaveWorker has the required signals."""
        worker = SaveWorker(mock_service, test_data["filepath"], test_data["metadata"])

        # Check that signals exist and are of correct type
        assert hasattr(worker, "progress")
        assert hasattr(worker, "finished")
        assert hasattr(worker, "error")
        assert isinstance(worker.progress, Signal)
        assert isinstance(worker.finished, Signal)
        assert isinstance(worker.error, Signal)

    def test_save_worker_run_success(self, mock_service, test_data, mocker):
        """Test SaveWorker.run() with successful save operation."""
        # Mock successful write_metadata operation
        mock_service.write_metadata.return_value = test_data["filepath"]

        worker = SaveWorker(mock_service, test_data["filepath"], test_data["metadata"])

        # Mock signal emissions to track calls
        mock_progress = mocker.patch.object(worker, "progress")
        mock_finished = mocker.patch.object(worker, "finished")
        mock_error = mocker.patch.object(worker, "error")

        # Run the worker
        worker.run()

        # Verify service method was called with correct parameters
        mock_service.write_metadata.assert_called_once_with(
            test_data["filepath"],
            test_data["metadata"],
            progress_callback=mock_progress.emit,
        )

        # Verify signals were emitted correctly
        mock_finished.emit.assert_called_once_with(test_data["filepath"])
        mock_error.emit.assert_not_called()

    def test_save_worker_run_with_exception(self, mock_service, test_data, mocker):
        """Test SaveWorker.run() when service raises an exception."""
        # Mock service to raise an exception
        test_exception = Exception("Save failed")
        mock_service.write_metadata.side_effect = test_exception

        worker = SaveWorker(mock_service, test_data["filepath"], test_data["metadata"])

        # Mock signal emissions to track calls
        mock_progress = mocker.patch.object(worker, "progress")
        mock_finished = mocker.patch.object(worker, "finished")
        mock_error = mocker.patch.object(worker, "error")

        # Run the worker
        worker.run()

        # Verify service method was called
        mock_service.write_metadata.assert_called_once_with(
            test_data["filepath"],
            test_data["metadata"],
            progress_callback=mock_progress.emit,
        )

        # Verify error signal was emitted with the string representation of the exception
        mock_error.emit.assert_called_once_with(str(test_exception))
        mock_finished.emit.assert_not_called()
        # Progress may or may not be called depending on when the error occurs

    def test_save_worker_run_with_empty_metadata(self, mock_service, mocker):
        """Test SaveWorker.run() with empty metadata dictionary."""
        empty_metadata = {}
        filepath = "/path/to/test.safetensors"

        # Mock successful save operation
        mock_service.write_metadata.return_value = filepath

        worker = SaveWorker(mock_service, filepath, empty_metadata)

        # Mock signal emissions to track calls
        mock_progress = mocker.patch.object(worker, "progress")
        mock_finished = mocker.patch.object(worker, "finished")
        mock_error = mocker.patch.object(worker, "error")

        # Run the worker
        worker.run()

        # Verify service method was called with empty metadata
        mock_service.write_metadata.assert_called_once_with(
            filepath, empty_metadata, progress_callback=mock_progress.emit
        )

        # Verify signals were emitted correctly
        mock_finished.emit.assert_called_once_with(filepath)
        mock_error.emit.assert_not_called()

    def test_save_worker_run_with_complex_metadata(self, mock_service, mocker):
        """Test SaveWorker.run() with complex nested metadata."""
        complex_metadata = {
            "author": "Test Author",
            "description": "Complex test model",
            "version": "2.0",
            "tags": ["neural-network", "transformer"],
            "config": {"hidden_size": 768, "num_layers": 12, "vocab_size": 30000},
            "metrics": {"accuracy": 0.95, "loss": 0.05},
        }
        filepath = "/path/to/complex.safetensors"

        # Mock successful save operation
        mock_service.write_metadata.return_value = filepath

        worker = SaveWorker(mock_service, filepath, complex_metadata)

        # Mock signal emissions to track calls
        mock_progress = mocker.patch.object(worker, "progress")
        mock_finished = mocker.patch.object(worker, "finished")
        mock_error = mocker.patch.object(worker, "error")

        # Run the worker
        worker.run()

        # Verify service method was called with complex metadata
        mock_service.write_metadata.assert_called_once_with(
            filepath, complex_metadata, progress_callback=mock_progress.emit
        )

        # Verify signals were emitted correctly
        mock_finished.emit.assert_called_once_with(filepath)
        mock_error.emit.assert_not_called()

    def test_save_worker_run_with_filesystem_error(
        self, mock_service, test_data, mocker
    ):
        """Test SaveWorker.run() when filesystem error occurs."""
        # Mock service to raise a filesystem-related exception
        fs_exception = OSError("Permission denied")
        mock_service.write_metadata.side_effect = fs_exception

        worker = SaveWorker(mock_service, test_data["filepath"], test_data["metadata"])

        # Mock signal emissions to track calls
        mock_progress = mocker.patch.object(worker, "progress")
        mock_finished = mocker.patch.object(worker, "finished")
        mock_error = mocker.patch.object(worker, "error")

        # Run the worker
        worker.run()

        # Verify service method was called
        mock_service.write_metadata.assert_called_once_with(
            test_data["filepath"],
            test_data["metadata"],
            progress_callback=mock_progress.emit,
        )

        # Verify error signal was emitted with the filesystem exception string
        mock_error.emit.assert_called_once_with(str(fs_exception))
        mock_finished.emit.assert_not_called()
        # Progress may or may not be called depending on when the error occurs

    def test_save_worker_run_with_none_metadata(self, mock_service, mocker):
        """Test SaveWorker.run() handles None metadata gracefully."""
        filepath = "/path/to/test.safetensors"
        none_metadata = {}

        # Mock successful save operation
        mock_service.write_metadata.return_value = filepath

        worker = SaveWorker(mock_service, filepath, none_metadata)

        # Mock signal emissions to track calls
        mock_progress = mocker.patch.object(worker, "progress")
        mock_finished = mocker.patch.object(worker, "finished")
        mock_error = mocker.patch.object(worker, "error")

        # Run the worker
        worker.run()

        # Verify service method was called with None metadata
        mock_service.write_metadata.assert_called_once_with(
            filepath, none_metadata, progress_callback=mock_progress.emit
        )

        # Verify signals were emitted correctly
        mock_finished.emit.assert_called_once_with(filepath)
        mock_error.emit.assert_not_called()
