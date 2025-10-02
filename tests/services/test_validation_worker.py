import pytest

from metaeditor_safetensors.models.modelspec import ComplianceLevel
from metaeditor_safetensors.services.utility import ModelType
from metaeditor_safetensors.services.validation_worker import (
    _resolve_model_type,
    compute_compliance_result,
)


@pytest.fixture
def base_snapshot():
    return {
        "modelspec.sai_model_spec": "1.0.0",
        "modelspec.architecture": "stable-diffusion",
        "modelspec.implementation": "diffusers",
        "modelspec.title": "Example Model",
    }


def test_resolve_model_type_accepts_strings():
    assert _resolve_model_type("image_generation") == ModelType.IMAGE_GENERATION
    assert _resolve_model_type("TEXT_PREDICTION") == ModelType.TEXT_PREDICTION
    assert _resolve_model_type("unknown-value") == ModelType.UNKNOWN


def test_compute_compliance_result_success(base_snapshot):
    snapshot = {
        **base_snapshot,
        "metaeditor.model_type": "image_generation",
    }

    result = compute_compliance_result(snapshot)

    assert result.level == ComplianceLevel.COMPLIANT
    assert result.model_category == ModelType.IMAGE_GENERATION
    assert result.missing_must_fields == []


def test_compute_compliance_result_handles_invalid_metadata(base_snapshot):
    snapshot = {
        **base_snapshot,
        "metaeditor.model_type": ModelType.IMAGE_GENERATION,
        "modelspec.hash_sha256": "bad-value",
    }

    result = compute_compliance_result(snapshot)

    assert result.level == ComplianceLevel.NON_COMPLIANT
    assert result.summary == "Validation Error"
    assert "Hash must" in result.details[0]
    assert result.model_category == ModelType.UNKNOWN


def test_compute_compliance_result_unknown_category(base_snapshot):
    snapshot = {
        **base_snapshot,
        "metaeditor.model_type": "something-new",
    }

    result = compute_compliance_result(snapshot)

    assert result.level == ComplianceLevel.UNKNOWN
    assert result.model_category == ModelType.UNKNOWN
    assert result.summary == "Model type not set"
