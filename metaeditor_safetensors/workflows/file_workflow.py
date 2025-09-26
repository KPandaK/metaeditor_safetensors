from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QObject

from ..models.metadata import Metadata
from ..services.config_service import ConfigService
from ..services.model_detection_service import ModelDetectionService
from ..services.safetensors_service import SafetensorsService
from ..services.utility import ModelType


@dataclass
class LoadResult:
    success: bool
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
