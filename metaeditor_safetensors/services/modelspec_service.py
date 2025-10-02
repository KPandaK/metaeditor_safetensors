import logging
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QThreadPool, QTimer

from ..models.metadata import Metadata
from ..models.modelspec import ComplianceResult
from .validation_worker import ValidationWorker

logger = logging.getLogger(__name__)


DEFAULT_VALIDATION_INTERVAL_MS = 1000


class ModelSpecService:
    def __init__(
        self,
        metadata: Metadata,
        *,
        validation_interval_ms: int = DEFAULT_VALIDATION_INTERVAL_MS,
    ):
        self._metadata = metadata
        self._validation_interval_ms = validation_interval_ms

        # Cached validation state
        self._cached_compliance: Optional[ComplianceResult] = None

        # Observers for compliance changes
        self._observers: List[Callable[[ComplianceResult], None]] = []

        # Validation coordination state
        self._last_change_counter: int = 0
        self._last_validated_counter: int = -1
        self._validation_in_flight: bool = False
        self._active_workers: Dict[int, ValidationWorker] = {}

        # Timer and thread-pool resources
        self._validation_timer = QTimer()
        self._validation_timer.setInterval(self._validation_interval_ms)
        self._validation_timer.timeout.connect(self._on_validation_timer)
        self._thread_pool = QThreadPool.globalInstance()

        # Register as metadata observer for real-time validation
        self._metadata.add_observer(self._on_metadata_changed)

        logger.debug(
            "ModelSpecService initialized with async validation (interval=%sms)",
            self._validation_interval_ms,
        )

    def _on_metadata_changed(self, *_, **__):
        try:
            logger.debug("Metadata changed, scheduling compliance validation")
            self._record_change()
        except Exception as exc:
            logger.error("Error in metadata change handler: %s", exc)

    def _record_change(self):
        self._last_change_counter += 1
        self._cached_compliance = None
        self._ensure_timer_running()

    def _ensure_timer_running(self):
        if not self._validation_timer.isActive():
            self._validation_timer.start()

    def _on_validation_timer(self):
        if self._last_validated_counter >= self._last_change_counter:
            if self._validation_timer.isActive():
                self._validation_timer.stop()
            return
        if self._validation_in_flight:
            logger.debug("Validation already running; waiting for completion")
            return
        self._dispatch_validation()

    def _dispatch_validation(self):
        if self._last_validated_counter >= self._last_change_counter:
            return

        counter = self._last_change_counter
        snapshot = self._metadata.get_all_data()
        worker = ValidationWorker(counter=counter, metadata_snapshot=snapshot)
        worker.signals.finished.connect(self._on_validation_finished)

        self._active_workers[counter] = worker
        self._validation_in_flight = True

        logger.debug("Dispatching compliance validation run counter=%s", counter)
        try:
            self._thread_pool.start(worker)
        except Exception as exc:
            logger.error("Failed to start validation worker: %s", exc)
            self._active_workers.pop(counter, None)
            self._validation_in_flight = False
            self._ensure_timer_running()

    def _on_validation_finished(self, counter: int, result: ComplianceResult):
        self._active_workers.pop(counter, None)
        self._validation_in_flight = False

        if counter < self._last_change_counter:
            logger.debug(
                "Discarding stale compliance result counter=%s (latest=%s)",
                counter,
                self._last_change_counter,
            )
            self._ensure_timer_running()
            return

        logger.debug("Validation finished for counter=%s", counter)
        self._cached_compliance = result
        self._last_validated_counter = counter

        for observer in list(self._observers):
            try:
                observer(result)
            except Exception as exc:
                logger.warning("Error notifying compliance observer: %s", exc)

        if self._last_validated_counter < self._last_change_counter:
            self._ensure_timer_running()
        elif self._validation_timer.isActive():
            self._validation_timer.stop()

    def trigger_validation(self):
        if self._validation_in_flight:
            logger.debug("Validation already running; immediate trigger skipped")
            return

        if self._last_validated_counter >= self._last_change_counter:
            logger.debug("Validation already current; nothing to trigger")
            return

        self._dispatch_validation()

    def shutdown(self):
        self._validation_timer.stop()
        self._metadata.remove_observer(self._on_metadata_changed)
        self._observers.clear()
        self._active_workers.clear()

    def get_compliance_result(self) -> ComplianceResult:
        if self._cached_compliance is None:
            raise RuntimeError("Compliance result is not available yet.")
        return self._cached_compliance

    def is_validation_current(self) -> bool:
        return self._last_validated_counter >= self._last_change_counter

    def add_observer(self, observer: Callable[[ComplianceResult], None]):
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(
                "Added compliance observer: %s",
                observer.__name__ if hasattr(observer, "__name__") else repr(observer),
            )

    def remove_observer(self, observer: Callable[[ComplianceResult], None]):
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(
                "Removed compliance observer: %s",
                observer.__name__ if hasattr(observer, "__name__") else repr(observer),
            )
