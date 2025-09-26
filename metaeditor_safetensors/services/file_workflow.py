from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from PySide6.QtCore import QObject, Signal, Slot

from ..models.metadata import Metadata
from .config_service import ConfigService
from .model_detection_service import ModelDetectionService
from .safetensors_service import SafetensorsService
from .utility import ModelType


@dataclass
class LoadResult:
    success: bool
    message: str
    error: Optional[str] = None
    filepath: Optional[str] = None


@dataclass
class SaveDispatch:
    started: bool
    message: str
    error: Optional[str] = None
    filepath: Optional[str] = None


@dataclass
class PreparedCallbacks:
    progress: Optional[Callable[[int], None]]
    success: Callable[[str], None]
    error: Optional[Callable[[str], None]]


class FileWorkflow(QObject):
    _invoke_signal = Signal(object)

    def __init__(
        self,
        metadata: Metadata,
        safetensors_service: SafetensorsService,
        config_service: ConfigService,
        model_detection_service: Optional[ModelDetectionService] = None,
    ) -> None:
        super().__init__()
        self._metadata = metadata
        self._safetensors = safetensors_service
        self._config_service = config_service
        self._model_detection_service = (
            model_detection_service or ModelDetectionService()
        )
        self._current_file: Optional[str] = None
        self._invoke_signal.connect(self._execute_on_main)

    @property
    def current_file(self) -> Optional[str]:
        return self._current_file

    @current_file.setter
    def current_file(self, value: Optional[str]) -> None:
        self._current_file = value

    def clear_current_file(self) -> None:
        self._current_file = None

    def load_file(self, filepath: str) -> LoadResult:
        try:
            metadata = self._safetensors.read_metadata(filepath)
            self._metadata.load_data(metadata)
            self._auto_detect_model_type()
            self._config_service.add_recent_file(filepath)
            self._current_file = filepath
            return LoadResult(
                success=True, message=f"Loaded file: {filepath}", filepath=filepath
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            self._metadata.load_data({})
            self._current_file = None
            return LoadResult(
                success=False,
                message=f"Error loading file: {exc}",
                error=str(exc),
            )

    def save(
        self,
        progress_callback: Callable[[int], None],
        success_callback: Callable[[str], None],
        error_callback: Callable[[str], None],
    ) -> SaveDispatch:
        guard = self._ensure_ready(require_current_file=True)
        if guard:
            return guard

        assert self._current_file is not None

        callbacks = self._prepare_callbacks(
            progress_cb=progress_callback,
            success_cb=success_callback,
            error_cb=error_callback,
            success_actions=(self._config_service.add_recent_file,),
        )

        return self._start_save(
            target_path=self._current_file,
            callbacks=callbacks,
            source_path=None,
            started_message=f"Saving {self._current_file}...",
        )

    def save_as(
        self,
        filepath: str,
        progress_callback: Callable[[int], None],
        success_callback: Callable[[str], None],
        error_callback: Callable[[str], None],
    ) -> SaveDispatch:
        guard = self._ensure_ready(require_current_file=False)
        if guard:
            return guard

        callbacks = self._prepare_callbacks(
            progress_cb=progress_callback,
            success_cb=success_callback,
            error_cb=error_callback,
            success_actions=(
                self._update_current_file,
                self._config_service.add_recent_file,
            ),
        )

        return self._start_save(
            target_path=filepath,
            callbacks=callbacks,
            source_path=self._current_file,
            started_message=f"Saving to {filepath}...",
        )

    @Slot(object)
    def _execute_on_main(self, fn: Callable[[], None]) -> None:
        fn()

    def _dispatch(self, fn: Optional[Callable[[], None]]) -> None:
        if fn is None:
            return
        self._invoke_signal.emit(fn)

    def _ensure_ready(self, *, require_current_file: bool) -> Optional[SaveDispatch]:
        if require_current_file and not self._current_file:
            return SaveDispatch(started=False, message="Please open a file first.")

        if self._safetensors.is_saving():
            return SaveDispatch(
                started=False, message="Save operation already in progress."
            )

        return None

    def _prepare_callbacks(
        self,
        *,
        progress_cb: Optional[Callable[[int], None]],
        success_cb: Callable[[str], None],
        error_cb: Optional[Callable[[str], None]],
        success_actions: Tuple[Callable[[str], None], ...] = (),
    ) -> PreparedCallbacks:
        progress: Optional[Callable[[int], None]] = None
        if progress_cb:

            def progress_wrapper(value: int, cb=progress_cb) -> None:
                self._dispatch(lambda: cb(value))

            progress = progress_wrapper

        actions: Tuple[Callable[[str], None], ...] = success_actions or tuple()

        def success(filepath: str, cb=success_cb, actions=actions) -> None:
            def runner() -> None:
                for action in actions:
                    action(filepath)
                cb(filepath)

            self._dispatch(runner)

        error: Optional[Callable[[str], None]] = None
        if error_cb:

            def error_wrapper(message: str, cb=error_cb) -> None:
                self._dispatch(lambda: cb(message))

            error = error_wrapper

        return PreparedCallbacks(progress=progress, success=success, error=error)

    def _start_save(
        self,
        *,
        target_path: str,
        callbacks: PreparedCallbacks,
        source_path: Optional[str],
        started_message: str,
    ) -> SaveDispatch:
        started = self._safetensors.write_metadata_async(
            filepath=target_path,
            metadata=self._metadata.get_all_data(),
            progress_callback=callbacks.progress,
            success_callback=callbacks.success,
            error_callback=callbacks.error,
            source_filepath=source_path,
        )

        if not started:
            return SaveDispatch(
                started=False, message="Save operation already in progress."
            )

        return SaveDispatch(
            started=True,
            message=started_message,
            filepath=target_path,
        )

    def _update_current_file(self, filepath: str) -> None:
        self._current_file = filepath

    def _auto_detect_model_type(self) -> None:
        model_type_value = self._metadata.get_value("metaeditor.model_type")
        if model_type_value:
            return
        data = self._metadata.get_all_data()
        detected_type = self._model_detection_service.detect_model_type(data)
        if detected_type != ModelType.UNKNOWN:
            self._metadata.set_value(
                "metaeditor.model_type",
                detected_type.value,
            )
