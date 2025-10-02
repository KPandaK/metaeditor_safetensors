import time

import pytest
from PySide6.QtCore import QTimer

from metaeditor_safetensors.models.metadata import ChangeSource, Metadata
from metaeditor_safetensors.models.modelspec import (
    ComplianceLevel,
    ComplianceResult,
)
from metaeditor_safetensors.services.modelspec_service import ModelSpecService
from metaeditor_safetensors.services.utility import ModelType


@pytest.fixture
def metadata() -> Metadata:
    return Metadata()


def _make_result(summary: str) -> ComplianceResult:
    return ComplianceResult(
        level=ComplianceLevel.COMPLIANT,
        missing_must_fields=[],
        missing_should_fields=[],
        model_category=ModelType.UNKNOWN,
        summary=summary,
        details=[summary],
    )


def test_validation_runs_after_metadata_change(qtbot, metadata, mocker):
    result = _make_result("first")
    mocker.patch(
        "metaeditor_safetensors.services.validation_worker.compute_compliance_result",
        return_value=result,
    )
    service = ModelSpecService(metadata, validation_interval_ms=50)

    try:
        observer = mocker.Mock()
        service.add_observer(observer)

        metadata.load_data({"modelspec.title": "Title"})
        service.trigger_validation()

        qtbot.waitUntil(lambda: observer.call_count == 1, timeout=2000)

        observer.assert_called_once()
        assert service.get_compliance_result() == result
        assert service.is_validation_current()
    finally:
        service.shutdown()


def test_stale_results_discarded(qtbot, metadata, mocker):
    first_result = _make_result("first")
    second_result = _make_result("second")

    call_count = {"value": 0}

    def compute_side_effect(_snapshot):
        idx = call_count["value"]
        call_count["value"] += 1
        if idx == 0:
            time.sleep(0.1)
            return first_result
        return second_result

    mocker.patch(
        "metaeditor_safetensors.services.validation_worker.compute_compliance_result",
        side_effect=compute_side_effect,
    )
    service = ModelSpecService(metadata, validation_interval_ms=25)

    try:
        observer = mocker.Mock()
        service.add_observer(observer)

        metadata.load_data({"modelspec.title": "Title"})
        service.trigger_validation()

        QTimer.singleShot(
            10,
            lambda: metadata.set_value(
                "modelspec.title",
                "Title Updated",
                source=ChangeSource.USER,
            ),
        )

        qtbot.waitUntil(lambda: observer.call_count == 1, timeout=3000)

        assert call_count["value"] == 2
        (result,) = observer.call_args[0]
        assert result.summary == "second"
        assert service.get_compliance_result().summary == "second"
        assert service.is_validation_current()
    finally:
        service.shutdown()


def test_validation_returns_unknown_when_model_type_missing(qtbot, metadata):
    service = ModelSpecService(metadata, validation_interval_ms=25)

    try:
        results: list[ComplianceResult] = []
        service.add_observer(lambda result: results.append(result))

        metadata.load_data(
            {
                "modelspec.sai_model_spec": "1.0.0",
                "modelspec.architecture": "stable-diffusion",
                "modelspec.implementation": "diffusers",
                "modelspec.title": "Example",
            }
        )

        service.trigger_validation()

        qtbot.waitUntil(lambda: len(results) == 1, timeout=3000)

        (result,) = results
        assert result.level == ComplianceLevel.UNKNOWN
        assert result.summary == "Model type not set"
    finally:
        service.shutdown()


def test_get_compliance_result_raises_when_not_ready(metadata):
    service = ModelSpecService(metadata, validation_interval_ms=100)

    try:
        with pytest.raises(RuntimeError):
            service.get_compliance_result()
    finally:
        service.shutdown()


def test_removed_observer_not_notified(qtbot, metadata, mocker):
    result = _make_result("observer-test")
    mocker.patch(
        "metaeditor_safetensors.services.validation_worker.compute_compliance_result",
        return_value=result,
    )
    service = ModelSpecService(metadata, validation_interval_ms=25)

    try:
        active_observer = mocker.Mock()
        removed_observer = mocker.Mock()

        service.add_observer(active_observer)
        service.add_observer(removed_observer)
        service.remove_observer(removed_observer)

        metadata.load_data({"modelspec.title": "Title"})
        service.trigger_validation()

        qtbot.waitUntil(lambda: active_observer.call_count == 1, timeout=2000)

        active_observer.assert_called_once_with(result)
        removed_observer.assert_not_called()
    finally:
        service.shutdown()


def test_trigger_validation_skips_when_result_current(qtbot, metadata, mocker):
    result = _make_result("cached")
    call_count = {"value": 0}

    def compute(_snapshot):
        call_count["value"] += 1
        return result

    mocker.patch(
        "metaeditor_safetensors.services.validation_worker.compute_compliance_result",
        side_effect=compute,
    )
    service = ModelSpecService(metadata, validation_interval_ms=25)

    try:
        observer = mocker.Mock()
        service.add_observer(observer)

        metadata.load_data({"modelspec.title": "Title"})
        service.trigger_validation()

        qtbot.waitUntil(lambda: call_count["value"] == 1, timeout=2000)

        service.trigger_validation()
        qtbot.wait(100)

        assert call_count["value"] == 1
        observer.assert_called_once_with(result)
        assert service.is_validation_current()
    finally:
        service.shutdown()
