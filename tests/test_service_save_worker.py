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
        mock_finished = mocker.patch.object(worker, "finished")
        mock_error = mocker.patch.object(worker, "error")

        # Run the worker
        worker.run()

        # Verify service method was called with correct filepath and metadata
        # The progress_callback will be a local function, so we check differently
        mock_service.write_metadata.assert_called_once()
        call_args = mock_service.write_metadata.call_args
        assert call_args[0][0] == test_data["filepath"]  # filepath
        assert call_args[0][1] == test_data["metadata"]  # metadata
        assert "progress_callback" in call_args[1]  # progress_callback keyword arg

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
        mock_finished = mocker.patch.object(worker, "finished")
        mock_error = mocker.patch.object(worker, "error")

        # Run the worker
        worker.run()

        # Verify service method was called with correct parameters
        mock_service.write_metadata.assert_called_once()
        call_args = mock_service.write_metadata.call_args
        assert call_args[0][0] == test_data["filepath"]  # filepath
        assert call_args[0][1] == test_data["metadata"]  # metadata
        assert "progress_callback" in call_args[1]  # progress_callback keyword arg

        # Verify error signal was emitted with the string representation of the exception
        mock_error.emit.assert_called_once_with(str(test_exception))
        mock_finished.emit.assert_not_called()

    def test_save_worker_progress_callback(self, mock_service, test_data, mocker):
        """Test that progress callback correctly emits progress signals."""
        # Mock successful save operation
        mock_service.write_metadata.return_value = test_data["filepath"]

        worker = SaveWorker(mock_service, test_data["filepath"], test_data["metadata"])

        # Mock signal emissions to track calls
        mock_progress = mocker.patch.object(worker, "progress")
        mock_finished = mocker.patch.object(worker, "finished")

        # Set up the service to call the progress callback
        def mock_write_metadata(filepath, metadata, progress_callback=None):
            if progress_callback:
                progress_callback(25)
                progress_callback(50)
                progress_callback(75)
                progress_callback(100)
            return filepath

        mock_service.write_metadata.side_effect = mock_write_metadata

        # Run the worker
        worker.run()

        # Verify progress signals were emitted
        expected_calls = [
            mocker.call(25),
            mocker.call(50),
            mocker.call(75),
            mocker.call(100),
        ]
        mock_progress.emit.assert_has_calls(expected_calls)
        mock_finished.emit.assert_called_once_with(test_data["filepath"])
