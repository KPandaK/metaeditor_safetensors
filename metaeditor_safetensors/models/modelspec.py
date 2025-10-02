import datetime
from enum import Enum
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Optional,
    Set,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, Field, field_validator

from ..services.utility import ModelType


class ComplianceLevel(Enum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


class FieldRequirement(Enum):
    MUST = "must"
    SHOULD = "should"
    CAN = "can"


class FieldCategory(Enum):
    GENERAL = 0
    IMAGE_GENERATION = 1
    TEXT_PREDICTION = 2


class FieldMeta:
    def __init__(
        self,
        requirement: FieldRequirement,
        category: FieldCategory = FieldCategory.GENERAL,
    ):
        self.requirement = requirement
        self.category = category


class ComplianceResult(BaseModel):
    level: ComplianceLevel
    missing_must_fields: List[str]
    missing_should_fields: List[str]
    model_category: ModelType
    summary: str
    details: List[str]


class ModelSpec(BaseModel):
    class Config:
        # Allow extra fields but don't validate them (for unknown modelspec fields)
        extra = "allow"
        # Use field aliases to map to actual metadata keys (Pydantic V2)
        populate_by_name = True

    sai_model_spec: Annotated[Optional[str], FieldMeta(FieldRequirement.MUST)] = Field(
        None,
        alias="modelspec.sai_model_spec",
        description="ModelSpec version (e.g., 1.0.0)",
    )
    architecture: Annotated[Optional[str], FieldMeta(FieldRequirement.MUST)] = Field(
        None,
        alias="modelspec.architecture",
        description="Model architecture (e.g., stable-diffusion-v1, llama-2)",
    )
    implementation: Annotated[Optional[str], FieldMeta(FieldRequirement.MUST)] = Field(
        None,
        alias="modelspec.implementation",
        description="Implementation framework (e.g., diffusers, transformers)",
    )
    title: Annotated[Optional[str], FieldMeta(FieldRequirement.MUST)] = Field(
        None, alias="modelspec.title"
    )
    description: Annotated[Optional[str], FieldMeta(FieldRequirement.SHOULD)] = Field(
        None,
        alias="modelspec.description",
    )
    author: Annotated[Optional[str], FieldMeta(FieldRequirement.SHOULD)] = Field(
        None, alias="modelspec.author"
    )
    date: Annotated[Optional[str], FieldMeta(FieldRequirement.SHOULD)] = Field(
        None, alias="modelspec.date"
    )
    hash_sha256: Annotated[Optional[str], FieldMeta(FieldRequirement.SHOULD)] = Field(
        None,
        alias="modelspec.hash_sha256",
    )
    license: Annotated[Optional[str], FieldMeta(FieldRequirement.CAN)] = Field(
        None, alias="modelspec.license"
    )
    usage_hint: Annotated[Optional[str], FieldMeta(FieldRequirement.CAN)] = Field(
        None,
        alias="modelspec.usage_hint",
    )
    tags: Annotated[Optional[str], FieldMeta(FieldRequirement.CAN)] = Field(
        None, alias="modelspec.tags"
    )
    merged_from: Annotated[Optional[str], FieldMeta(FieldRequirement.CAN)] = Field(
        None, alias="modelspec.merged_from"
    )
    thumbnail: Annotated[Optional[str], FieldMeta(FieldRequirement.CAN)] = Field(
        None, alias="modelspec.thumbnail"
    )
    implementation_version: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN)
    ] = Field(
        None,
        alias="modelspec.implementation_version",
        description="Implementation version requirement",
    )

    # === Image Generation Fields ===
    resolution: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.IMAGE_GENERATION)
    ] = Field(
        None,
        alias="modelspec.resolution",
        description="Base resolution (e.g., 512x512, 1024x1024)",
    )
    trigger_phrase: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.IMAGE_GENERATION)
    ] = Field(
        None,
        alias="modelspec.trigger_phrase",
        description="Activation phrase for LoRA/embeddings (leave empty if not needed)",
    )
    prediction_type: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.IMAGE_GENERATION)
    ] = Field(
        None,
        alias="modelspec.prediction_type",
        description="Prediction type: epsilon or v_prediction",
    )
    timestep_range: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.IMAGE_GENERATION)
    ] = Field(
        None,
        alias="modelspec.timestep_range",
        description="Timestep range (e.g., 0,999)",
    )
    encoder_layer: Annotated[
        Optional[int], FieldMeta(FieldRequirement.CAN, FieldCategory.IMAGE_GENERATION)
    ] = Field(
        None,
        alias="modelspec.encoder_layer",
        ge=1,
        description="Encoder layer for clip skip",
    )
    preprocessor: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.IMAGE_GENERATION)
    ] = Field(
        None,
        alias="modelspec.preprocessor",
        description="Preprocessor type for ControlNet",
    )
    is_negative_embedding: Annotated[
        Optional[bool], FieldMeta(FieldRequirement.CAN, FieldCategory.IMAGE_GENERATION)
    ] = Field(
        None,
        alias="modelspec.is_negative_embedding",
        description="For negative prompt embeddings",
    )
    unet_dtype: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.IMAGE_GENERATION)
    ] = Field(
        None, alias="modelspec.unet_dtype", description="UNet data type requirements"
    )
    vae_dtype: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.IMAGE_GENERATION)
    ] = Field(
        None, alias="modelspec.vae_dtype", description="VAE data type requirements"
    )

    # === Text Prediction Fields ===
    data_format: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.TEXT_PREDICTION)
    ] = Field(
        None,
        alias="modelspec.data_format",
        description="Data format (e.g., fp16, gptq-4bit)",
    )
    format_type: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.TEXT_PREDICTION)
    ] = Field(
        None,
        alias="modelspec.format_type",
        description="Format type (chat, writing, code, etc.)",
    )
    language: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.TEXT_PREDICTION)
    ] = Field(
        None,
        alias="modelspec.language",
        description="Primary language(s) (comma-separated)",
    )
    format_template: Annotated[
        Optional[str], FieldMeta(FieldRequirement.CAN, FieldCategory.TEXT_PREDICTION)
    ] = Field(
        None,
        alias="modelspec.format_template",
        description="Chat format template with placeholders",
    )

    @field_validator("hash_sha256")
    @classmethod
    def validate_hash_format(cls, v):
        if v is not None:
            import re

            if not re.match(r"^0x[a-f0-9]{64}$", v):
                raise ValueError(
                    "Hash must be in format 0x followed by 64 hex characters"
                )
        return v

    @field_validator("resolution")
    @classmethod
    def validate_resolution_format(cls, v):
        if v is not None:
            import re

            if not re.match(r"^\d+x\d+$", v):
                raise ValueError(
                    "Resolution must be in format WIDTHxHEIGHT (e.g., 512x512)"
                )
        return v

    @field_validator("prediction_type")
    @classmethod
    def validate_prediction_type(cls, v):
        if v is not None and v not in ["v", "epsilon"]:
            raise ValueError('Prediction type must be "v" or "epsilon"')
        return v

    @field_validator("timestep_range")
    @classmethod
    def validate_timestep_range(cls, v):
        if v is not None:
            import re

            if not re.match(r"^\d+,\d+$", v):
                raise ValueError(
                    "Timestep range must be in format MIN,MAX (e.g., 0,999)"
                )
        return v

    @field_validator("thumbnail")
    @classmethod
    def validate_thumbnail_format(cls, v):
        if v is not None:
            import re

            if not re.match(r"^data:image/[^;]+;base64,", v):
                raise ValueError(
                    "Thumbnail must be a valid data URI (data:image/...;base64,...)"
                )
        return v

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_format(cls, v: Optional[str]):
        if v is None:
            return v
        try:
            # allow both date-only and datetime strings
            if v.endswith("Z"):
                v = v[:-1] + "+00:00"
            date_obj = datetime.datetime.fromisoformat(v)
        except ValueError as exc:
            raise ValueError("Date must be in ISO 8601 format (YYYY-MM-DD...)") from exc
        return date_obj.isoformat()

    @classmethod
    def _iter_field_metadata(cls):
        type_hints = get_type_hints(cls, include_extras=True)
        for field_name, field_type in type_hints.items():
            if field_name not in cls.model_fields:
                continue

            field_info = cls.model_fields[field_name]
            alias = field_info.alias or f"modelspec.{field_name}"

            if get_origin(field_type) is Annotated:
                for arg in get_args(field_type)[1:]:
                    if isinstance(arg, FieldMeta):
                        yield field_name, alias, arg
                        break

    @classmethod
    def get_filtered_fields(
        cls, requirement: FieldRequirement, model_type: ModelType
    ) -> List[tuple[str, str]]:
        filtered_categories = {FieldCategory.GENERAL}
        if model_type == ModelType.IMAGE_GENERATION:
            filtered_categories.add(FieldCategory.IMAGE_GENERATION)
        elif model_type == ModelType.TEXT_PREDICTION:
            filtered_categories.add(FieldCategory.TEXT_PREDICTION)

        fields: List[tuple[str, str]] = []
        for field_name, alias, meta in cls._iter_field_metadata():
            if meta.requirement == requirement and meta.category in filtered_categories:
                fields.append((alias, field_name))
        return fields

    @staticmethod
    def create_error_compliance_result(error_message: str) -> ComplianceResult:
        return ComplianceResult(
            level=ComplianceLevel.NON_COMPLIANT,
            missing_must_fields=[],
            missing_should_fields=[],
            model_category=ModelType.UNKNOWN,
            summary="Validation Error",
            details=[f"ModelSpec validation failed: {error_message}"],
        )

    def analyze_compliance(self, model_type: ModelType) -> ComplianceResult:
        if model_type == ModelType.UNKNOWN:
            summary, details = self._generate_summary_and_details(
                ComplianceLevel.UNKNOWN,
                [],
                [],
                model_type,
            )
            return ComplianceResult(
                level=ComplianceLevel.UNKNOWN,
                missing_must_fields=[],
                missing_should_fields=[],
                model_category=model_type,
                summary=summary,
                details=details,
            )

        must_fields = self.get_filtered_fields(FieldRequirement.MUST, model_type)
        should_fields = self.get_filtered_fields(FieldRequirement.SHOULD, model_type)

        missing_must = [
            alias
            for alias, field_name in must_fields
            if not self._field_has_value(field_name)
        ]
        missing_should = [
            alias
            for alias, field_name in should_fields
            if not self._field_has_value(field_name)
        ]

        if not missing_must:
            level = ComplianceLevel.COMPLIANT
        elif len(missing_must) < len(must_fields):
            level = ComplianceLevel.PARTIAL
        else:
            level = ComplianceLevel.NON_COMPLIANT

        summary, details = self._generate_summary_and_details(
            level, missing_must, missing_should, model_type
        )

        return ComplianceResult(
            level=level,
            missing_must_fields=missing_must,
            missing_should_fields=missing_should,
            model_category=model_type,
            summary=summary,
            details=details,
        )

    def _field_has_value(self, field_name: str) -> bool:
        value = getattr(self, field_name)
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        return True

    def _generate_summary_and_details(
        self,
        level: ComplianceLevel,
        missing_must: List[str],
        missing_should: List[str],
        category: ModelType,
    ) -> tuple[str, List[str]]:
        details = []

        # Status summary
        if level == ComplianceLevel.COMPLIANT:
            summary = "ModelSpec Compliant"
            details.append("All required fields are present.")
        elif level == ComplianceLevel.PARTIAL:
            summary = f"Partially Compliant ({len(missing_must)} missing)"
            details.append(f"Missing {len(missing_must)} required field(s).")
        elif level == ComplianceLevel.NON_COMPLIANT:
            summary = f"Non-Compliant ({len(missing_must)} missing)"
            details.append("Missing critical required fields.")
        else:
            summary = "Model type not set"
            details.append("Select a model type to evaluate ModelSpec compliance.")

        # Category information
        if category != ModelType.UNKNOWN:
            category_name = category.value.replace("_", " ").title()
            details.append(f"Detected: {category_name} model")

        # Missing MUST fields
        if missing_must:
            details.append("Missing required fields:")
            for field in missing_must:
                field_name = field.replace("modelspec.", "")
                details.append(f"  • {field_name}")

        # Missing SHOULD fields (only show if not too many issues)
        if missing_should and len(missing_must) <= 2:
            details.append("Missing recommended fields:")
            for field in missing_should[:3]:  # Limit to first 3
                field_name = field.replace("modelspec.", "")
                details.append(f"  • {field_name}")
            if len(missing_should) > 3:
                details.append(f"  • ... and {len(missing_should) - 3} more")

        return summary, details

    @classmethod
    def from_raw_metadata(cls, metadata: Dict[str, Any]) -> "ModelSpec":
        try:
            return cls(**metadata)
        except Exception as exc:
            raise ValueError(f"Invalid ModelSpec data: {exc}") from exc
