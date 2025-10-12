import pytest

from metaeditor_safetensors.models.modelspec import (
    ComplianceLevel,
    FieldRequirement,
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


def test_get_filtered_fields_respects_model_category():
    image_fields = dict(
        ModelSpec.get_filtered_fields(FieldRequirement.CAN, ModelType.IMAGE_GENERATION)
    )
    text_fields = dict(
        ModelSpec.get_filtered_fields(FieldRequirement.CAN, ModelType.TEXT_PREDICTION)
    )

    assert image_fields["modelspec.resolution"] == "resolution"
    assert "modelspec.format_template" not in image_fields

    assert text_fields["modelspec.format_template"] == "format_template"
    assert "modelspec.resolution" not in text_fields


def test_partially_compliant_summary_reports_missing_fields(base_metadata):
    metadata = {
        **base_metadata,
        "modelspec.architecture": " ",
    }
    modelspec = ModelSpec.from_raw_metadata(metadata)

    result = modelspec.analyze_compliance(ModelType.IMAGE_GENERATION)

    assert result.summary == "Partially Compliant (1 missing)"
    assert any("Missing required fields" in detail for detail in result.details)
    assert any("architecture" in detail for detail in result.details)
    assert any(
        detail.startswith("  • ") and "author" in detail for detail in result.details
    )


def test_create_error_compliance_result_sets_defaults():
    result = ModelSpec.create_error_compliance_result("boom")

    assert result.level == ComplianceLevel.NON_COMPLIANT
    assert result.missing_must_fields == []
    assert result.missing_should_fields == []
    assert result.model_category == ModelType.UNKNOWN
    assert result.summary == "Validation Error"
    assert "boom" in result.details[0]


def test_date_validator_normalizes_z_suffix(base_metadata):
    metadata = {**base_metadata, "modelspec.date": "2024-01-02T03:04:05Z"}

    modelspec = ModelSpec.from_raw_metadata(metadata)

    assert modelspec.date == "2024-01-02T03:04:05+00:00"


def test_date_validator_rejects_bad_format(base_metadata):
    metadata = {**base_metadata, "modelspec.date": "2024/01/02"}

    with pytest.raises(ValueError):
        ModelSpec.from_raw_metadata(metadata)


def test_recommended_fields_summary_truncates_list(base_metadata):
    minimal = {
        "modelspec.sai_model_spec": base_metadata["modelspec.sai_model_spec"],
        "modelspec.architecture": base_metadata["modelspec.architecture"],
        "modelspec.implementation": base_metadata["modelspec.implementation"],
        "modelspec.title": base_metadata["modelspec.title"],
    }
    modelspec = ModelSpec.from_raw_metadata(minimal)

    result = modelspec.analyze_compliance(ModelType.IMAGE_GENERATION)

    assert result.summary == "ModelSpec Compliant"
    recommended_section = [
        line for line in result.details if line.startswith("Missing recommended")
    ]
    assert recommended_section
    bullet_lines = [
        line for line in result.details if line.strip().startswith("\u2022 ")
    ]
    assert len(bullet_lines) == 4
    assert bullet_lines[-1].endswith("more")


@pytest.mark.parametrize(
    "field_key,value,attr,expected",
    [
        (
            "modelspec.hash_sha256",
            "0x" + "a" * 64,
            "hash_sha256",
            "0x" + "a" * 64,
        ),
        ("modelspec.resolution", "512x512", "resolution", "512x512"),
        ("modelspec.prediction_type", "v", "prediction_type", "v"),
        ("modelspec.timestep_range", "0,999", "timestep_range", "0,999"),
        (
            "modelspec.thumbnail",
            "data:image/png;base64,AAAA",
            "thumbnail",
            "data:image/png;base64,AAAA",
        ),
        (
            "modelspec.date",
            "2024-01-02",
            "date",
            "2024-01-02T00:00:00",
        ),
    ],
)
def test_field_validators_accept_valid_input(base_metadata, field_key, value, attr, expected):
    metadata = {**base_metadata, field_key: value}

    modelspec = ModelSpec.from_raw_metadata(metadata)

    assert getattr(modelspec, attr) == expected


@pytest.mark.parametrize(
    "field_key,value",
    [
        ("modelspec.hash_sha256", "0x1234"),
        ("modelspec.resolution", "512"),
        ("modelspec.prediction_type", "bad"),
        ("modelspec.timestep_range", "0-999"),
        ("modelspec.thumbnail", "image/png;base64,AAAA"),
    ],
)
def test_field_validators_raise_for_invalid_input(base_metadata, field_key, value):
    metadata = {**base_metadata, field_key: value}

    with pytest.raises(ValueError):
        ModelSpec.from_raw_metadata(metadata)
