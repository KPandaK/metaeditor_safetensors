from typing import Any, Dict

from PySide6.QtCore import QObject, Signal


class SaveWorker(QObject):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, service, filepath: str, metadata: Dict[str, Any], parent=None):
        super().__init__(parent)
        self._service = service
        self._filepath = filepath
        self._metadata = metadata

    def run(self):
        try:

            def progress_callback(progress_value: int):
                self.progress.emit(progress_value)

            result = self._service.write_metadata(
                self._filepath, self._metadata, progress_callback=progress_callback
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
