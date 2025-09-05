"""
Save Worker
===========

This module defines the `SaveWorker`, a QObject designed to run on a separate
thread to perform the time-consuming task of saving a .safetensors file
without freezing the user interface.
"""

from typing import Any, Dict

from PySide6.QtCore import QObject, Signal

from ..services.safetensors_service import SafetensorsService


class SaveWorker(QObject):
    """
    A worker that saves safetensors metadata in the background.

    This QObject is intended to be moved to a separate QThread. Its `run` method
    performs the save operation and emits signals to communicate progress,
    completion, or errors back to the main thread.
    """

    # Signal emitted to report progress (e.g., percentage)
    progress = Signal(int)

    # Signal emitted on successful completion, carrying the saved filepath
    finished = Signal(str)

    # Signal emitted when an error occurs, carrying the error message
    error = Signal(str)

    def __init__(
        self, service: SafetensorsService, filepath: str, metadata: Dict[str, Any]
    ):
        """
        Args:
            service: An instance of SafetensorService to perform the save.
            filepath: The path to the file to be saved.
            metadata: The metadata dictionary to save into the file.
        """
        super().__init__()
        self._service = service
        self._filepath = filepath
        self._metadata = metadata

    def run(self):
        """
        The main work method. This is called when the thread starts.
        It performs the save operation and emits signals based on the outcome.
        """
        try:
            # The `write_metadata` method in the service will accept the
            # progress signal's `emit` method as a callback to report progress.
            new_filepath = self._service.write_metadata(
                self._filepath, self._metadata, progress_callback=self.progress.emit
            )
            self.finished.emit(new_filepath)
        except Exception as e:
            self.error.emit(str(e))
