from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

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
class LoadDispatch:
    started: bool
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
class PreparedSaveCallbacks:
    progress: Optional[Callable[[int], None]]
    success: Callable[[str], None]
    error: Optional[Callable[[str], None]]


@dataclass
class PreparedLoadCallbacks:
    progress: Optional[Callable[[int], None]]
    success: Callable[[Dict[str, Any]], None]
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

    def load_file(
        self,
        filepath: str,
        *,
        progress_callback: Optional[Callable[[int], None]] = None,
        success_callback: Optional[Callable[[LoadResult], None]] = None,
        error_callback: Optional[Callable[[LoadResult], None]] = None,
    ) -> LoadDispatch:
        guard = self._ensure_load_ready()
        if guard:
            return guard

        callbacks = self._prepare_load_callbacks(
            filepath=filepath,
            progress_cb=progress_callback,
            success_cb=success_callback,
            error_cb=error_callback,
        )

        started = self._safetensors.read_metadata_async(
            filepath,
            progress_callback=callbacks.progress,
            success_callback=callbacks.success,
            error_callback=callbacks.error,
        )

        if not started:
            return LoadDispatch(
                started=False, message="Load operation already in progress."
            )

        return LoadDispatch(
            started=True,
            message=f"Loading {filepath}...",
            filepath=filepath,
        )

    def save(
        self,
        progress_callback: Callable[[int], None],
        success_callback: Callable[[str], None],
        error_callback: Callable[[str], None],
    ) -> SaveDispatch:
        guard = self._ensure_save_ready(require_current_file=True)
        if guard:
            return guard

        assert self._current_file is not None

        callbacks = self._prepare_save_callbacks(
            progress_cb=progress_callback,
            success_cb=success_callback,
            error_cb=error_callback,
            success_actions=(self._config_service.add_recent_file,),
        )

        return self._start_save_internal(
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
        guard = self._ensure_save_ready(require_current_file=False)
        if guard:
            return guard

        callbacks = self._prepare_save_callbacks(
            progress_cb=progress_callback,
            success_cb=success_callback,
            error_cb=error_callback,
            success_actions=(
                self._update_current_file,
                self._config_service.add_recent_file,
            ),
        )

        return self._start_save_internal(
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

    def _ensure_save_ready(
        self, *, require_current_file: bool
    ) -> Optional[SaveDispatch]:
        if require_current_file and not self._current_file:
            return SaveDispatch(started=False, message="Please open a file first.")

        if self._safetensors.is_saving():
            return SaveDispatch(
                started=False, message="Save operation already in progress."
            )

        return None

    def _ensure_load_ready(self) -> Optional[LoadDispatch]:
        if self._safetensors.is_loading():
            return LoadDispatch(
                started=False, message="Load operation already in progress."
            )
        return None

    def _prepare_save_callbacks(
        self,
        *,
        progress_cb: Optional[Callable[[int], None]],
        success_cb: Callable[[str], None],
        error_cb: Optional[Callable[[str], None]],
        success_actions: Tuple[Callable[[str], None], ...] = (),
    ) -> PreparedSaveCallbacks:
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

        return PreparedSaveCallbacks(progress=progress, success=success, error=error)

    def _prepare_load_callbacks(
        self,
        *,
        filepath: str,
        progress_cb: Optional[Callable[[int], None]],
        success_cb: Optional[Callable[[LoadResult], None]],
        error_cb: Optional[Callable[[LoadResult], None]],
    ) -> PreparedLoadCallbacks:
        progress: Optional[Callable[[int], None]] = None
        if progress_cb:

            def progress_wrapper(value: int, cb=progress_cb) -> None:
                self._dispatch(lambda: cb(value))

            progress = progress_wrapper

        def success(metadata: Dict[str, Any]) -> None:
            def runner() -> None:
                self._metadata.load_data(metadata)
                self._auto_detect_model_type()
                self._config_service.add_recent_file(filepath)
                self._current_file = filepath
                if success_cb:
                    success_cb(
                        LoadResult(
                            success=True,
                            message=f"Loaded file: {filepath}",
                            filepath=filepath,
                        )
                    )

            self._dispatch(runner)

        def error(message: str) -> None:
            def runner() -> None:
                self._metadata.load_data({})
                self._current_file = None
                if error_cb:
                    error_cb(
                        LoadResult(
                            success=False,
                            message=f"Error loading file: {message}",
                            error=message,
                        )
                    )

            self._dispatch(runner)

        return PreparedLoadCallbacks(progress=progress, success=success, error=error)

    def _start_save_internal(
        self,
        *,
        target_path: str,
        callbacks: PreparedSaveCallbacks,
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
