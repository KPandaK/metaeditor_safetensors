"""
Unit tests for Save Worker
===========================

Tests for the SaveWorker class which handles background saving
of safetensors metadata without blocking the UI.
"""

import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject, Signal

from metaeditor_safetensors.services.save_worker import SaveWorker


class TestSaveWorker(unittest.TestCase):
    """Test cases for SaveWorker functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock SafetensorsService
        self.mock_service = MagicMock()
        
        # Test data
        self.test_filepath = "/path/to/test.safetensors"
        self.test_metadata = {
            "author": "Test Author",
            "description": "Test model",
            "version": "1.0"
        }

    def test_save_worker_initialization(self):
        """Test SaveWorker initialization with proper parameters."""
        worker = SaveWorker(self.mock_service, self.test_filepath, self.test_metadata)
        
        # Verify initialization
        self.assertIsInstance(worker, QObject)
        self.assertEqual(worker._service, self.mock_service)
        self.assertEqual(worker._filepath, self.test_filepath)
        self.assertEqual(worker._metadata, self.test_metadata)

    def test_save_worker_signals_exist(self):
        """Test that SaveWorker has the required signals."""
        worker = SaveWorker(self.mock_service, self.test_filepath, self.test_metadata)
        
        # Check that signals exist and are of correct type
        self.assertTrue(hasattr(worker, 'progress'))
        self.assertTrue(hasattr(worker, 'finished'))
        self.assertTrue(hasattr(worker, 'error'))
        
        self.assertIsInstance(worker.progress, Signal)
        self.assertIsInstance(worker.finished, Signal)
        self.assertIsInstance(worker.error, Signal)

    def test_run_successful_save(self):
        """Test successful save operation in run method."""
        # Setup mock service to return success
        expected_new_filepath = "/path/to/saved_test.safetensors"
        self.mock_service.write_metadata.return_value = expected_new_filepath
        
        worker = SaveWorker(self.mock_service, self.test_filepath, self.test_metadata)
        
        # Mock the signals to track emissions
        finished_signal_mock = MagicMock()
        error_signal_mock = MagicMock()
        progress_signal_mock = MagicMock()
        
        worker.finished.connect(finished_signal_mock)
        worker.error.connect(error_signal_mock)
        worker.progress.connect(progress_signal_mock)
        
        # Run the worker
        worker.run()
        
        # Verify service was called correctly
        self.mock_service.write_metadata.assert_called_once_with(
            self.test_filepath, 
            self.test_metadata, 
            progress_callback=worker.progress.emit
        )
        
        # Verify finished signal was emitted with correct filepath
        finished_signal_mock.assert_called_once_with(expected_new_filepath)
        
        # Verify error signal was not emitted
        error_signal_mock.assert_not_called()

    def test_run_save_exception(self):
        """Test save operation that raises an exception."""
        # Setup mock service to raise exception
        test_error_message = "Failed to write metadata"
        self.mock_service.write_metadata.side_effect = Exception(test_error_message)
        
        worker = SaveWorker(self.mock_service, self.test_filepath, self.test_metadata)
        
        # Mock the signals to track emissions
        finished_signal_mock = MagicMock()
        error_signal_mock = MagicMock()
        
        worker.finished.connect(finished_signal_mock)
        worker.error.connect(error_signal_mock)
        
        # Run the worker
        worker.run()
        
        # Verify service was called
        self.mock_service.write_metadata.assert_called_once_with(
            self.test_filepath, 
            self.test_metadata, 
            progress_callback=worker.progress.emit
        )
        
        # Verify error signal was emitted with correct error message
        error_signal_mock.assert_called_once_with(test_error_message)
        
        # Verify finished signal was not emitted
        finished_signal_mock.assert_not_called()

    def test_run_progress_callback_integration(self):
        """Test that progress callback is properly passed to service."""
        worker = SaveWorker(self.mock_service, self.test_filepath, self.test_metadata)
        
        # Mock progress signal to track calls
        progress_signal_mock = MagicMock()
        worker.progress.connect(progress_signal_mock)
        
        # Configure mock service to call progress callback
        def mock_write_metadata(filepath, metadata, progress_callback=None):
            if progress_callback:
                progress_callback(25)  # 25% progress
                progress_callback(50)  # 50% progress
                progress_callback(100) # 100% progress
            return "/path/to/saved_file.safetensors"
        
        self.mock_service.write_metadata.side_effect = mock_write_metadata
        
        # Run the worker
        worker.run()
        
        # Verify progress signals were emitted
        expected_calls = [unittest.mock.call(25), unittest.mock.call(50), unittest.mock.call(100)]
        progress_signal_mock.assert_has_calls(expected_calls)

    def test_run_io_error_exception(self):
        """Test save operation that raises IOError."""
        # Setup mock service to raise IOError
        test_error_message = "Permission denied"
        self.mock_service.write_metadata.side_effect = IOError(test_error_message)
        
        worker = SaveWorker(self.mock_service, self.test_filepath, self.test_metadata)
        
        # Mock the signals to track emissions
        finished_signal_mock = MagicMock()
        error_signal_mock = MagicMock()
        
        worker.finished.connect(finished_signal_mock)
        worker.error.connect(error_signal_mock)
        
        # Run the worker
        worker.run()
        
        # Verify error signal was emitted with correct error message
        error_signal_mock.assert_called_once_with(test_error_message)
        
        # Verify finished signal was not emitted
        finished_signal_mock.assert_not_called()

    def test_run_value_error_exception(self):
        """Test save operation that raises ValueError."""
        # Setup mock service to raise ValueError
        test_error_message = "Invalid metadata format"
        self.mock_service.write_metadata.side_effect = ValueError(test_error_message)
        
        worker = SaveWorker(self.mock_service, self.test_filepath, self.test_metadata)
        
        # Mock the signals to track emissions
        error_signal_mock = MagicMock()
        worker.error.connect(error_signal_mock)
        
        # Run the worker
        worker.run()
        
        # Verify error signal was emitted with correct error message
        error_signal_mock.assert_called_once_with(test_error_message)

    def test_run_with_empty_metadata(self):
        """Test save operation with empty metadata dictionary."""
        empty_metadata: Dict[str, Any] = {}
        expected_new_filepath = "/path/to/saved_test.safetensors"
        self.mock_service.write_metadata.return_value = expected_new_filepath
        
        worker = SaveWorker(self.mock_service, self.test_filepath, empty_metadata)
        
        # Mock the signals to track emissions
        finished_signal_mock = MagicMock()
        worker.finished.connect(finished_signal_mock)
        
        # Run the worker
        worker.run()
        
        # Verify service was called with empty metadata
        self.mock_service.write_metadata.assert_called_once_with(
            self.test_filepath, 
            empty_metadata, 
            progress_callback=worker.progress.emit
        )
        
        # Verify finished signal was emitted
        finished_signal_mock.assert_called_once_with(expected_new_filepath)

    def test_run_with_complex_metadata(self):
        """Test save operation with complex nested metadata."""
        complex_metadata = {
            "model_info": {
                "name": "Test Model",
                "version": "2.0",
                "tags": ["test", "demo", "sample"]
            },
            "training": {
                "epochs": 100,
                "learning_rate": 0.001,
                "batch_size": 32
            },
            "metrics": {
                "accuracy": 0.95,
                "loss": 0.05
            }
        }
        expected_new_filepath = "/path/to/complex_saved_test.safetensors"
        self.mock_service.write_metadata.return_value = expected_new_filepath
        
        worker = SaveWorker(self.mock_service, self.test_filepath, complex_metadata)
        
        # Mock the signals to track emissions
        finished_signal_mock = MagicMock()
        worker.finished.connect(finished_signal_mock)
        
        # Run the worker
        worker.run()
        
        # Verify service was called with complex metadata
        self.mock_service.write_metadata.assert_called_once_with(
            self.test_filepath, 
            complex_metadata, 
            progress_callback=worker.progress.emit
        )
        
        # Verify finished signal was emitted
        finished_signal_mock.assert_called_once_with(expected_new_filepath)


if __name__ == "__main__":
    unittest.main()