import logging
from typing import Callable, List, Optional

from ..models.metadata import Metadata
from ..models.modelspec import (
    ComplianceLevel,
    ComplianceResult,
    ModelSpec,
    ModelType,
)

logger = logging.getLogger(__name__)


class ModelSpecService:
    def __init__(self, metadata: Metadata):
        self._metadata = metadata

        # Cached validation state
        self._cached_compliance: Optional[ComplianceResult] = None

        # Observers for compliance changes
        self._observers: List[Callable[[ComplianceResult], None]] = []

        # Register as metadata observer for real-time validation
        self._metadata.add_observer(self._on_metadata_changed)

        logger.debug("ModelSpecService initialized with metadata observer")

    def _on_metadata_changed(self):
        try:
            logger.debug("Metadata changed, invalidating compliance cache")

            self._cached_compliance = None

            # Notify compliance observers of changes
            for observer in self._observers:
                try:
                    # Pass current compliance result (will trigger validation if needed)
                    observer(self.get_compliance_result())
                except Exception as e:
                    logger.warning(f"Error notifying compliance observer: {e}")
        except Exception as e:
            logger.error(f"Error in metadata change handler: {e}")

    def _validate(self):
        try:
            # Create a fresh ModelSpec instance for validation
            all_data = self._metadata.get_all_data()
            modelspec = ModelSpec.from_raw_metadata(all_data)

            # Analyze compliance
            self._cached_compliance = modelspec.analyze_compliance()

            logger.debug(f"Validation completed: {self._cached_compliance.level.value}")

        except Exception as e:
            logger.warning(f"ModelSpec validation failed: {e}")
            # Handle validation errors gracefully
            self._cached_compliance = self._create_error_compliance_result(str(e))

    def _create_error_compliance_result(self, error_message: str) -> ComplianceResult:
        return ComplianceResult(
            level=ComplianceLevel.NON_COMPLIANT,
            missing_must_fields=[],
            missing_should_fields=[],
            present_fields=set(),
            model_category=ModelType.UNKNOWN,  # Use unknown for error cases
            summary="Validation Error",
            details=[f"ModelSpec validation failed: {error_message}"],
        )

    def get_compliance_result(self) -> ComplianceResult:
        if self._cached_compliance is None:
            self._validate()
        assert self._cached_compliance is not None
        return self._cached_compliance

    def is_validation_current(self) -> bool:
        return self._cached_compliance is not None

    def add_observer(self, observer: Callable[[ComplianceResult], None]):
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(
                f"Added compliance observer: {observer.__name__ if hasattr(observer, '__name__') else repr(observer)}"
            )

    def remove_observer(self, observer: Callable[[ComplianceResult], None]):
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(
                f"Removed compliance observer: {observer.__name__ if hasattr(observer, '__name__') else repr(observer)}"
            )
