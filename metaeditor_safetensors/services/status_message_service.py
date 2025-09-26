from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Final, Optional

from PySide6.QtCore import QObject, Qt, QThread, Signal


class StatusLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CUSTOM = "custom"


DEFAULT_TIMEOUT_MS: Final[dict[StatusLevel, Optional[int]]] = {
    StatusLevel.INFO: 3000,
    StatusLevel.SUCCESS: 5000,
    StatusLevel.WARNING: 5000,
    StatusLevel.ERROR: None,
    StatusLevel.CUSTOM: None,
}


@dataclass(frozen=True)
class StatusMessage:
    text: str
    level: StatusLevel = StatusLevel.INFO
    timeout_ms: Optional[int] = None


StatusListener = Callable[[StatusMessage], None]


class StatusMessageService(QObject):
    _message_posted = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._listeners: list[StatusListener] = []
        self._message_posted.connect(
            self._dispatch_message, Qt.ConnectionType.QueuedConnection
        )

    def add_listener(self, listener: StatusListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: StatusListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def post(
        self,
        message: str,
        *,
        level: StatusLevel = StatusLevel.INFO,
        timeout_ms: Optional[int] = None,
    ) -> None:
        resolved_timeout = (
            timeout_ms if timeout_ms is not None else DEFAULT_TIMEOUT_MS[level]
        )
        status_message = StatusMessage(message, level, resolved_timeout)
        thread = self.thread()
        if thread is None or QThread.currentThread() == thread:
            self._dispatch_message(status_message)
        else:
            self._message_posted.emit(status_message)

    def _dispatch_message(self, status_message: StatusMessage) -> None:
        for listener in list(self._listeners):
            try:
                listener(status_message)
            except Exception:  # pragma: no cover - defensive logging
                logging.getLogger(__name__).exception(
                    "Status message listener raised an exception"
                )

    def info(self, message: str, *, timeout_ms: Optional[int] = None) -> None:
        self.post(message, level=StatusLevel.INFO, timeout_ms=timeout_ms)

    def success(self, message: str, *, timeout_ms: Optional[int] = None) -> None:
        self.post(message, level=StatusLevel.SUCCESS, timeout_ms=timeout_ms)

    def warning(self, message: str, *, timeout_ms: Optional[int] = None) -> None:
        self.post(message, level=StatusLevel.WARNING, timeout_ms=timeout_ms)

    def error(self, message: str, *, timeout_ms: Optional[int] = None) -> None:
        self.post(message, level=StatusLevel.ERROR, timeout_ms=timeout_ms)

    def custom(self, message: str, *, timeout_ms: Optional[int] = None) -> None:
        self.post(message, level=StatusLevel.INFO, timeout_ms=timeout_ms)

    def clear(self) -> None:
        self.post("", timeout_ms=0)
