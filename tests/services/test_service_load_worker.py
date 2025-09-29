"""
Unit tests for LoadWorker.
"""

from typing import Any, Dict

import pytest

from metaeditor_safetensors.services.load_worker import LoadWorker


@pytest.fixture
def mock_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def test_filepath():
    return "/path/to/file.safetensors"


class TestLoadWorker:
    def test_initialization(self, mock_service, test_filepath):
        worker = LoadWorker(mock_service, test_filepath)

        assert worker._service is mock_service
        assert worker._filepath == test_filepath

    def test_signals_exist(self, mock_service, test_filepath):
        worker = LoadWorker(mock_service, test_filepath)

        assert hasattr(worker, "progress")
        assert hasattr(worker, "finished")
        assert hasattr(worker, "error")

    def test_run_success(self, mock_service, test_filepath, mocker):
        expected_metadata: Dict[str, Any] = {"modelspec.title": "Demo"}

        def fake_read_metadata(filepath, *, progress_callback=None):
            assert filepath == test_filepath
            assert progress_callback is not None
            progress_callback(10)
            progress_callback(100)
            return expected_metadata

        mock_service.read_metadata.side_effect = fake_read_metadata

        worker = LoadWorker(mock_service, test_filepath)

        progress_signal = mocker.patch.object(worker, "progress")
        finished_signal = mocker.patch.object(worker, "finished")
        error_signal = mocker.patch.object(worker, "error")

        worker.run()

        mock_service.read_metadata.assert_called_once()
        progress_signal.emit.assert_has_calls([mocker.call(10), mocker.call(100)])
        finished_signal.emit.assert_called_once_with(expected_metadata)
        error_signal.emit.assert_not_called()

    def test_run_error_emits_error(self, mock_service, test_filepath, mocker):
        mock_service.read_metadata.side_effect = RuntimeError("boom")

        worker = LoadWorker(mock_service, test_filepath)

        progress_signal = mocker.patch.object(worker, "progress")
        finished_signal = mocker.patch.object(worker, "finished")
        error_signal = mocker.patch.object(worker, "error")

        worker.run()

        mock_service.read_metadata.assert_called_once_with(
            test_filepath, progress_callback=mocker.ANY
        )
        error_signal.emit.assert_called_once_with("boom")
        progress_signal.emit.assert_not_called()
        finished_signal.emit.assert_not_called()
