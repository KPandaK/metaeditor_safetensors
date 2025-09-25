from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, Signal


class SaveWorker(QObject):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        service: Any,
        filepath: str,
        metadata: Dict[str, Any],
        source_filepath: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._service = service
        self._filepath = filepath
        self._metadata = metadata
        self._source_filepath = source_filepath

    def run(self):
        try:

            def progress_callback(progress_value: int):
                self.progress.emit(progress_value)

            result = self._service.write_metadata(
                self._filepath,
                self._metadata,
                progress_callback=progress_callback,
                source_filepath=self._source_filepath,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
