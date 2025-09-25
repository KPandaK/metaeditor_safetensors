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

from ..services.model_detection_service import ModelDetectionService
from ..services.utility import ModelType


class ComplianceLevel(Enum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"


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
    present_fields: Set[str]
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
    def get_all_field_placeholders(cls) -> Dict[str, str]:
        return {
            field_name: field_info.description or ""
            for field_name, field_info in cls.model_fields.items()
            if field_info.description
        }

    # TODO: Can we implement this as a bitfield so that we can check for multiple categories at the same time?
    # Category should also be specified, not queried.
    # def get_required_fields(self, requirement: FieldRequirement) -> List[str]:
    # Map ModelType to FieldCategory for filtering
    # category_to_field_category = {
    #     ModelType.IMAGE_GENERATION: FieldCategory.IMAGE_GENERATION,
    #     ModelType.TEXT_PREDICTION: FieldCategory.TEXT_PREDICTION,
    #     ModelType.UNKNOWN: None,  # Include all categories for unknown models
    # }
    # relevant_field_category = category_to_field_category.get(category)

    # # Get fields by requirement level from Annotated type metadata
    # field_list = []
    # type_hints = get_type_hints(self.__class__, include_extras=True)
    # model_fields = type(self).model_fields

    # for field_name, field_type in type_hints.items():
    #     # Skip non-field attributes
    #     if field_name not in model_fields:
    #         continue

    #     # Extract metadata from Annotated types
    #     if get_origin(field_type) is Annotated:
    #         args = get_args(field_type)
    #         # Look for FieldMeta in the annotation metadata
    #         for arg in args[1:]:  # Skip the actual type, check metadata
    #             if isinstance(arg, FieldMeta):
    #                 field_meta = arg
    #                 if field_meta.requirement == requirement:
    #                     # Check category-specific fields
    #                     if (
    #                         field_meta.category == FieldCategory.GENERAL
    #                         or field_meta.category == relevant_field_category
    #                         or relevant_field_category
    #                         is None  # Include all for unknown models
    #                     ):
    #                         # Get the alias from the field info
    #                         field_info = model_fields[field_name]
    #                         alias = field_info.alias or f"modelspec.{field_name}"
    #                         field_list.append(alias)
    #                 break

    # # Add category-specific MUST fields for special cases
    # if requirement == FieldRequirement.MUST:
    #     if category == ModelType.IMAGE_GENERATION:
    #         # Resolution is MUST for image generation models
    #         if "modelspec.resolution" not in field_list:
    #             field_list.append("modelspec.resolution")
    #     elif category == ModelType.TEXT_PREDICTION:
    #         # Data format is MUST for text prediction models
    #         if "modelspec.data_format" not in field_list:
    #             field_list.append("modelspec.data_format")

    # return field_list

    # TODO: The way that compliance is determined should be updated - this seems kind of gross
    def get_present_fields(self) -> Set[str]:
        present = set()
        fields = type(self).model_fields.items()
        for field_name, field_info in fields:
            value = getattr(self, field_name)
            if value is not None and value != "":
                # Use the alias (actual metadata key) if available
                key = field_info.alias or f"modelspec.{field_name}"
                present.add(key)
        return present

    # def analyze_compliance(self) -> ComplianceResult:
    #     present_fields = self.get_present_fields()

    #     # Get required fields
    #     must_fields = self.get_required_fields(FieldRequirement.MUST)
    #     should_fields = self.get_required_fields(FieldRequirement.SHOULD)

    #     # Check for missing fields
    #     missing_must = [f for f in must_fields if f not in present_fields]
    #     missing_should = [f for f in should_fields if f not in present_fields]

    #     # Determine compliance level
    #     if not missing_must:
    #         level = ComplianceLevel.COMPLIANT
    #     elif len(missing_must) < len(must_fields):
    #         level = ComplianceLevel.PARTIAL
    #     else:
    #         level = ComplianceLevel.NON_COMPLIANT

    #     # Generate summary and details
    #     summary, details = self._generate_summary_and_details(
    #         level, missing_must, missing_should, present_fields, category
    #     )

    #     return ComplianceResult(
    #         level=level,
    #         missing_must_fields=missing_must,
    #         missing_should_fields=missing_should,
    #         present_fields=present_fields,
    #         model_category=category,
    #         summary=summary,
    #         details=details,
    #     )

    def _generate_summary_and_details(
        self,
        level: ComplianceLevel,
        missing_must: List[str],
        missing_should: List[str],
        present: Set[str],
        category: ModelType,
    ) -> tuple[str, List[str]]:
        """Generate human-readable summary and details."""
        details = []

        # Status summary
        if level == ComplianceLevel.COMPLIANT:
            summary = "ModelSpec Compliant"
            details.append("All required fields are present.")
        elif level == ComplianceLevel.PARTIAL:
            summary = f"Partially Compliant ({len(missing_must)} missing)"
            details.append(f"Missing {len(missing_must)} required field(s).")
        else:
            summary = f"Non-Compliant ({len(missing_must)} missing)"
            details.append("Missing critical required fields.")

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

        # Present fields count
        details.append(f"Present: {len(present)} ModelSpec field(s)")

        return summary, details

    # TODO:  If we only extract raw metadata, how are non-modelspec.* fields handled? Especially when we save the safetensors file again.
    @classmethod
    def from_raw_metadata(cls, metadata: Dict[str, Any]) -> "ModelSpec":
        # Extract only ModelSpec fields
        modelspec_data = {
            key: value
            for key, value in metadata.items()
            if key.startswith("modelspec.")
        }

        try:
            return cls(**modelspec_data)
        except Exception as exc:
            raise ValueError(f"Invalid ModelSpec data: {exc}") from exc
