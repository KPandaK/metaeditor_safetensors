from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class StatusLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


DEFAULT_TIMEOUT_MS: dict[StatusLevel, Optional[int]] = {
    StatusLevel.INFO: 3000,
    StatusLevel.SUCCESS: 5000,
    StatusLevel.WARNING: 5000,
    StatusLevel.ERROR: None,
}


@dataclass(frozen=True)
class StatusMessage:
    text: str
    level: StatusLevel = StatusLevel.INFO
    timeout_ms: Optional[int] = None


StatusListener = Callable[[StatusMessage], None]


class StatusMessageService:
    def __init__(self) -> None:
        self._listeners: list[StatusListener] = []

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
        for listener in list(self._listeners):
            listener(status_message)

    def info(self, message: str, *, timeout_ms: Optional[int] = None) -> None:
        self.post(message, level=StatusLevel.INFO, timeout_ms=timeout_ms)

    def success(self, message: str, *, timeout_ms: Optional[int] = None) -> None:
        self.post(message, level=StatusLevel.SUCCESS, timeout_ms=timeout_ms)

    def warning(self, message: str, *, timeout_ms: Optional[int] = None) -> None:
        self.post(message, level=StatusLevel.WARNING, timeout_ms=timeout_ms)

    def error(self, message: str, *, timeout_ms: Optional[int] = None) -> None:
        self.post(message, level=StatusLevel.ERROR, timeout_ms=timeout_ms)

    def clear(self) -> None:
        self.post("", timeout_ms=0)
