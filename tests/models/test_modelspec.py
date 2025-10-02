import pytest

from metaeditor_safetensors.models.modelspec import (
    ComplianceLevel,
    ModelSpec,
)
from metaeditor_safetensors.services.utility import ModelType


@pytest.fixture
def base_metadata():
    return {
        "modelspec.sai_model_spec": "1.0.0",
        "modelspec.architecture": "stable-diffusion",
        "modelspec.implementation": "diffusers",
        "modelspec.title": "Example Model",
        "modelspec.description": "Sample description",
    }


def test_analyze_compliance_compliant_image_model(base_metadata):
    modelspec = ModelSpec.from_raw_metadata(base_metadata)

    result = modelspec.analyze_compliance(ModelType.IMAGE_GENERATION)

    assert result.level == ComplianceLevel.COMPLIANT
    assert result.missing_must_fields == []
    assert set(result.missing_should_fields) == {
        "modelspec.author",
        "modelspec.date",
        "modelspec.hash_sha256",
    }
    assert result.model_category == ModelType.IMAGE_GENERATION


def test_analyze_compliance_partial_when_single_must_missing(base_metadata):
    incomplete_metadata = {
        key: value
        for key, value in base_metadata.items()
        if key != "modelspec.architecture"
    }
    modelspec = ModelSpec.from_raw_metadata(incomplete_metadata)

    result = modelspec.analyze_compliance(ModelType.TEXT_PREDICTION)

    assert result.level == ComplianceLevel.PARTIAL
    assert result.missing_must_fields == ["modelspec.architecture"]
    assert result.model_category == ModelType.TEXT_PREDICTION


def test_analyze_compliance_non_compliant_when_all_must_missing():
    modelspec = ModelSpec.from_raw_metadata({})

    result = modelspec.analyze_compliance(ModelType.IMAGE_GENERATION)

    assert result.level == ComplianceLevel.NON_COMPLIANT
    assert set(result.missing_must_fields) == {
        "modelspec.sai_model_spec",
        "modelspec.architecture",
        "modelspec.implementation",
        "modelspec.title",
    }


def test_analyze_compliance_unknown_model_type(base_metadata):
    modelspec = ModelSpec.from_raw_metadata(base_metadata)

    result = modelspec.analyze_compliance(ModelType.UNKNOWN)

    assert result.level == ComplianceLevel.UNKNOWN
    assert result.missing_must_fields == []
    assert "Select a model type" in result.details[0]
