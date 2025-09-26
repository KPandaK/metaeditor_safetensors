from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import QObject

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


class FileWorkflow(QObject):
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
        if not self._current_file:
            return SaveDispatch(started=False, message="Please open a file first.")

        if self._safetensors.is_saving():
            return SaveDispatch(
                started=False, message="Save operation already in progress."
            )

        def wrapped_success(filepath: str) -> None:
            self._config_service.add_recent_file(filepath)
            success_callback(filepath)

        started = self._safetensors.write_metadata_async(
            filepath=self._current_file,
            metadata=self._metadata.get_all_data(),
            progress_callback=progress_callback,
            success_callback=wrapped_success,
            error_callback=error_callback,
        )

        if not started:
            return SaveDispatch(
                started=False, message="Save operation already in progress."
            )

        return SaveDispatch(
            started=True,
            message=f"Saving {self._current_file}...",
            filepath=self._current_file,
        )

    def save_as(
        self,
        filepath: str,
        progress_callback: Callable[[int], None],
        success_callback: Callable[[str], None],
        error_callback: Callable[[str], None],
    ) -> SaveDispatch:
        if self._safetensors.is_saving():
            return SaveDispatch(
                started=False, message="Save operation already in progress."
            )

        def wrapped_success(completed_path: str) -> None:
            self._current_file = completed_path
            self._config_service.add_recent_file(completed_path)
            success_callback(completed_path)

        started = self._safetensors.write_metadata_async(
            filepath=filepath,
            metadata=self._metadata.get_all_data(),
            progress_callback=progress_callback,
            success_callback=wrapped_success,
            error_callback=error_callback,
            source_filepath=self._current_file,
        )

        if not started:
            return SaveDispatch(
                started=False, message="Save operation already in progress."
            )

        return SaveDispatch(
            started=True,
            message=f"Saving to {filepath}...",
            filepath=filepath,
        )

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
