from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator


class ModelCategory(Enum):
    IMAGE_GENERATION = "image_generation"
    TEXT_PREDICTION = "text_prediction"
    UNKNOWN = "unknown"


class ComplianceLevel(Enum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"


class FieldRequirement(Enum):
    MUST = "must"
    SHOULD = "should"
    CAN = "can"


class ComplianceResult(BaseModel):
    level: ComplianceLevel
    missing_must_fields: List[str]
    missing_should_fields: List[str]
    present_fields: Set[str]
    model_category: ModelCategory
    summary: str
    details: List[str]


class ModelSpec(BaseModel):
    """
    Data model for safetensors metadata validation and compliance.

    This model handles ONLY modelspec.* fields. Non-ModelSpec metadata
    is handled separately to avoid interfering with unknown fields.
    """

    class Config:
        # Allow extra fields but don't validate them (for unknown modelspec fields)
        extra = "allow"
        # Use field aliases to map to actual metadata keys (Pydantic V2)
        populate_by_name = True

    # === Core MUST Fields (all models) ===
    sai_model_spec: Optional[str] = Field(
        None,
        alias="modelspec.sai_model_spec",
        description="ModelSpec version identifier",
    )
    architecture: Optional[str] = Field(
        None, alias="modelspec.architecture", description="Model architecture type"
    )
    implementation: Optional[str] = Field(
        None,
        alias="modelspec.implementation",
        description="Implementation codebase identifier",
    )
    title: Optional[str] = Field(
        None, alias="modelspec.title", description="Human-readable model title"
    )

    # === SHOULD Fields (recommended) ===
    description: Optional[str] = Field(
        None, alias="modelspec.description", description="Detailed model description"
    )
    author: Optional[str] = Field(
        None, alias="modelspec.author", description="Model creator/author"
    )
    date: Optional[str] = Field(
        None, alias="modelspec.date", description="Creation/publication date (ISO 8601)"
    )
    hash_sha256: Optional[str] = Field(
        None, alias="modelspec.hash_sha256", description="SHA256 hash of tensor content"
    )

    # === General CAN Fields ===
    license: Optional[str] = Field(
        None, alias="modelspec.license", description="License information"
    )
    usage_hint: Optional[str] = Field(
        None, alias="modelspec.usage_hint", description="Usage instructions or hints"
    )
    tags: Optional[str] = Field(
        None, alias="modelspec.tags", description="Comma-separated category tags"
    )
    merged_from: Optional[str] = Field(
        None, alias="modelspec.merged_from", description="Source models if merged"
    )
    thumbnail: Optional[str] = Field(
        None, alias="modelspec.thumbnail", description="Base64-encoded preview image"
    )
    implementation_version: Optional[str] = Field(
        None,
        alias="modelspec.implementation_version",
        description="Implementation version requirement",
    )

    # === Image Generation Fields ===
    resolution: Optional[str] = Field(
        None,
        alias="modelspec.resolution",
        description="Base resolution (e.g., 512x512)",
    )
    trigger_phrase: Optional[str] = Field(
        None,
        alias="modelspec.trigger_phrase",
        description="Required trigger phrase for adapters",
    )
    prediction_type: Optional[str] = Field(
        None,
        alias="modelspec.prediction_type",
        description="Prediction type (v or epsilon)",
    )
    timestep_range: Optional[str] = Field(
        None,
        alias="modelspec.timestep_range",
        description="Timestep range (e.g., 0,999)",
    )
    encoder_layer: Optional[int] = Field(
        None,
        alias="modelspec.encoder_layer",
        ge=1,
        description="Encoder layer for clip skip",
    )
    preprocessor: Optional[str] = Field(
        None,
        alias="modelspec.preprocessor",
        description="Preprocessor type for ControlNet",
    )
    is_negative_embedding: Optional[bool] = Field(
        None,
        alias="modelspec.is_negative_embedding",
        description="For negative prompt embeddings",
    )
    unet_dtype: Optional[str] = Field(
        None, alias="modelspec.unet_dtype", description="UNet data type requirements"
    )
    vae_dtype: Optional[str] = Field(
        None, alias="modelspec.vae_dtype", description="VAE data type requirements"
    )

    # === Text Prediction Fields ===
    data_format: Optional[str] = Field(
        None,
        alias="modelspec.data_format",
        description="Data format (e.g., fp16, gptq-4bit)",
    )
    format_type: Optional[str] = Field(
        None,
        alias="modelspec.format_type",
        description="Format type (chat, writing, code, etc.)",
    )
    language: Optional[str] = Field(
        None,
        alias="modelspec.language",
        description="Primary language(s) (comma-separated)",
    )
    format_template: Optional[str] = Field(
        None,
        alias="modelspec.format_template",
        description="Chat format template with placeholders",
    )

    @field_validator("hash_sha256")
    @classmethod
    def validate_hash_format(cls, v):
        """Validate SHA256 hash format."""
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
        """Validate resolution format."""
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
        """Validate prediction type."""
        if v is not None and v not in ["v", "epsilon"]:
            raise ValueError('Prediction type must be "v" or "epsilon"')
        return v

    @field_validator("timestep_range")
    @classmethod
    def validate_timestep_range(cls, v):
        """Validate timestep range format."""
        if v is not None:
            import re

            if not re.match(r"^\d+,\d+$", v):
                raise ValueError(
                    "Timestep range must be in format MIN,MAX (e.g., 0,999)"
                )
        return v

    @field_validator("format_type")
    @classmethod
    def validate_format_type(cls, v):
        """Validate format type."""
        valid_types = ["general", "writing", "chat", "code", "technical"]
        if v is not None and v not in valid_types:
            raise ValueError(f'Format type must be one of: {", ".join(valid_types)}')
        return v

    @field_validator("thumbnail")
    @classmethod
    def validate_thumbnail_format(cls, v):
        """Validate thumbnail data URI format."""
        if v is not None:
            import re

            if not re.match(r"^data:image/[^;]+;base64,", v):
                raise ValueError(
                    "Thumbnail must be a valid data URI (data:image/...;base64,...)"
                )
        return v

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_format(cls, v):
        """Validate ISO 8601 date format."""
        if v is None:
            return v
        # Basic ISO 8601 validation - in production you'd use dateutil
        import re

        if not re.match(r"^\d{4}-\d{2}-\d{2}", str(v)):
            raise ValueError("Date must be in ISO 8601 format (YYYY-MM-DD...)")
        return v

    def determine_category(self) -> ModelCategory:
        """Determine model category based on architecture."""
        if not self.architecture:
            return ModelCategory.UNKNOWN

        arch_lower = self.architecture.lower()

        # Image generation patterns
        image_patterns = {
            "stable-diffusion",
            "stable-video-diffusion",
            "stable-cascade",
        }
        if any(pattern in arch_lower for pattern in image_patterns):
            return ModelCategory.IMAGE_GENERATION

        # Text prediction patterns
        text_patterns = {"gpt-neo-x", "transformer", "llama", "bert"}
        if any(pattern in arch_lower for pattern in text_patterns):
            return ModelCategory.TEXT_PREDICTION

        return ModelCategory.UNKNOWN

    def get_required_fields(self, requirement: FieldRequirement) -> List[str]:
        """Get required fields based on model category and requirement level."""
        category = self.determine_category()

        # Core MUST fields for all models
        must_fields = [
            "modelspec.sai_model_spec",
            "modelspec.architecture",
            "modelspec.implementation",
            "modelspec.title",
        ]

        # Category-specific MUST fields
        if category == ModelCategory.IMAGE_GENERATION:
            must_fields.append("modelspec.resolution")
        elif category == ModelCategory.TEXT_PREDICTION:
            must_fields.append("modelspec.data_format")

        # SHOULD fields (recommended for all)
        should_fields = [
            "modelspec.description",
            "modelspec.author",
            "modelspec.date",
            "modelspec.hash_sha256",
        ]

        if requirement == FieldRequirement.MUST:
            return must_fields
        elif requirement == FieldRequirement.SHOULD:
            return should_fields
        else:  # CAN - return all other defined fields
            all_fields = set(self.__fields__.keys())
            defined_fields = set(must_fields + should_fields)
            return [f for f in all_fields if f not in defined_fields]

    def get_present_fields(self) -> Set[str]:
        """Get all present (non-None) ModelSpec fields."""
        present = set()
        for field_name, field_info in self.__fields__.items():
            value = getattr(self, field_name)
            if value is not None and value != "":
                # Use the alias (actual metadata key) if available
                key = field_info.alias or f"modelspec.{field_name}"
                present.add(key)
        return present

    def analyze_compliance(self) -> ComplianceResult:
        """
        Analyze ModelSpec compliance.

        This is separate from Pydantic validation - it checks ModelSpec
        MUST/SHOULD/CAN requirements based on the model category.
        """
        category = self.determine_category()
        present_fields = self.get_present_fields()

        # Get required fields
        must_fields = self.get_required_fields(FieldRequirement.MUST)
        should_fields = self.get_required_fields(FieldRequirement.SHOULD)

        # Check for missing fields
        missing_must = [f for f in must_fields if f not in present_fields]
        missing_should = [f for f in should_fields if f not in present_fields]

        # Determine compliance level
        if not missing_must:
            level = ComplianceLevel.COMPLIANT
        elif len(missing_must) < len(must_fields):
            level = ComplianceLevel.PARTIAL
        else:
            level = ComplianceLevel.NON_COMPLIANT

        # Generate summary and details
        summary, details = self._generate_summary_and_details(
            level, missing_must, missing_should, present_fields, category
        )

        return ComplianceResult(
            level=level,
            missing_must_fields=missing_must,
            missing_should_fields=missing_should,
            present_fields=present_fields,
            model_category=category,
            summary=summary,
            details=details,
        )

    def _generate_summary_and_details(
        self,
        level: ComplianceLevel,
        missing_must: List[str],
        missing_should: List[str],
        present: Set[str],
        category: ModelCategory,
    ) -> tuple[str, List[str]]:
        """Generate human-readable summary and details."""
        details = []

        # Status summary
        if level == ComplianceLevel.COMPLIANT:
            summary = "✅ ModelSpec Compliant"
            details.append("All required fields are present.")
        elif level == ComplianceLevel.PARTIAL:
            summary = f"⚠️ Partially Compliant ({len(missing_must)} missing)"
            details.append(f"Missing {len(missing_must)} required field(s).")
        else:
            summary = f"❌ Non-Compliant ({len(missing_must)} missing)"
            details.append("Missing critical required fields.")

        # Category information
        if category != ModelCategory.UNKNOWN:
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

    @classmethod
    def from_raw_metadata(cls, metadata: Dict[str, Any]) -> "ModelSpec":
        """
        Create ModelSpec instance from raw metadata dictionary.

        Extracts only modelspec.* fields and handles missing fields gracefully.
        Validation errors are caught and stored for later handling.
        """
        # Extract only ModelSpec fields
        modelspec_data = {
            key: value
            for key, value in metadata.items()
            if key.startswith("modelspec.")
        }

        try:
            return cls(**modelspec_data)
        except Exception:
            # For invalid data, create instance with minimal data
            # This allows the app to continue working with partial/invalid ModelSpec
            minimal_data = {
                key: value
                for key, value in modelspec_data.items()
                if key
                in [
                    "modelspec.title",
                    "modelspec.architecture",
                    "modelspec.sai_model_spec",
                ]
            }
            try:
                return cls(**minimal_data)
            except Exception:
                # Absolute fallback - empty instance with no required fields
                return cls.model_construct()

    @classmethod
    def get_field_name(cls, field: str) -> str:
        """
        Get the metadata key name for a model field.

        Args:
            field: The Pydantic field name (e.g., 'title', 'sai_model_spec')

        Returns:
            The metadata key (e.g., 'modelspec.title', 'modelspec.sai_model_spec')
        """
        if field in cls.__fields__:
            field_info = cls.__fields__[field]
            return field_info.alias or f"modelspec.{field}"
        raise ValueError(f"Unknown ModelSpec field: {field}")

    @classmethod
    def get_all_field_names(cls) -> Dict[str, str]:
        """
        Get mapping of Pydantic field names to metadata keys.

        Returns:
            Dictionary mapping field names to their metadata keys
        """
        return {
            field_name: field_info.alias or f"modelspec.{field_name}"
            for field_name, field_info in cls.__fields__.items()
        }
