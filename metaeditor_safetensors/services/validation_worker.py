import logging
from typing import Any, Dict

from PySide6.QtCore import QObject, QRunnable, Signal

from ..models.modelspec import ComplianceResult, ModelSpec
from .utility import ModelType

logger = logging.getLogger(__name__)


class ValidationSignals(QObject):
    finished = Signal(int, ComplianceResult)


def _resolve_model_type(raw_value: Any) -> ModelType:
    if isinstance(raw_value, ModelType):
        return raw_value

    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
        for candidate in ModelType:
            if normalized in {candidate.value.lower(), candidate.name.lower()}:
                return candidate

    return ModelType.UNKNOWN


def compute_compliance_result(metadata_snapshot: Dict[str, Any]) -> ComplianceResult:
    model_type = _resolve_model_type(metadata_snapshot.get("metaeditor.model_type"))

    try:
        modelspec = ModelSpec.from_raw_metadata(metadata_snapshot)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("ModelSpec validation failed: %s", exc)
        return ModelSpec.create_error_compliance_result(str(exc))

    try:
        return modelspec.analyze_compliance(model_type)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error during ModelSpec analysis: %s", exc)
        return ModelSpec.create_error_compliance_result(str(exc))


class ValidationWorker(QRunnable):
    def __init__(self, *, counter: int, metadata_snapshot: Dict[str, Any]):
        super().__init__()
        self._counter = counter
        self._metadata_snapshot = metadata_snapshot
        self.signals = ValidationSignals()

    def run(self):  # pragma: no cover - executed in worker thread
        try:
            result = compute_compliance_result(self._metadata_snapshot)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected error during compliance computation: %s", exc)
            result = ModelSpec.create_error_compliance_result(str(exc))

        self.signals.finished.emit(self._counter, result)
