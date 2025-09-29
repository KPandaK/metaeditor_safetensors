from typing import Any, Dict

from PySide6.QtCore import QObject, Signal


class LoadWorker(QObject):
    progress = Signal(int)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, service: Any, filepath: str, parent=None) -> None:
        super().__init__(parent)
        self._service = service
        self._filepath = filepath

    def run(self) -> None:
        try:

            def progress_callback(value: int) -> None:
                self.progress.emit(value)

            metadata: Dict[str, Any] = self._service.read_metadata(
                self._filepath,
                progress_callback=progress_callback,
            )
            self.finished.emit(metadata)
        except Exception as exc:  # pragma: no cover - defensive
            self.error.emit(str(exc))
