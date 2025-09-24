import logging
import os
from typing import Any, Dict, Optional, Set

import yaml

from ..services.utility import ModelType, get_package_root


class ModelDetectionService:
    def __init__(self):
        self._config: Dict = {}
        self._image_patterns: Set[str] = set()
        self._text_patterns: Set[str] = set()
        self._image_hints: Set[str] = set()
        self._text_hints: Set[str] = set()
        self._case_insensitive: bool = True
        self._substring_match: bool = True

        # Load configuration
        package_root = get_package_root()
        config_path = os.path.join(package_root, "", "models.yaml")
        self._load_config(config_path)

    def _load_config(self, config_path: str) -> None:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}

            # Extract patterns
            model_types = self._config.get("model_types", {})

            # Image generation patterns
            image_config = model_types.get("image_generation", {})
            self._image_patterns = set(image_config.get("patterns", []))

            # Text prediction patterns
            text_config = model_types.get("text_prediction", {})
            self._text_patterns = set(text_config.get("patterns", []))

            # Secondary hints
            hints = self._config.get("secondary_hints", {})
            self._image_hints = set(hints.get("image_generation", []))
            self._text_hints = set(hints.get("text_prediction", []))

            # Matching configuration
            matching = self._config.get("matching", {})
            self._case_insensitive = matching.get("case_insensitive", True)
            self._substring_match = matching.get("substring_match", True)

        except Exception as e:
            logging.warning(
                f"Error loading model detection config from {config_path}: {e}"
            )
            self._config = {}

    def detect_model_type(self, fields: Dict[str, Any]) -> ModelType:
        architecture = fields.get("modelspec.architecture")
        secondary_fields = {
            k: v
            for k, v in fields.items()
            if k.startswith("modelspec.") and k != "modelspec.architecture"
        }

        if not architecture:
            # Try secondary detection if no architecture
            if secondary_fields:
                return self._detect_from_secondary_fields(secondary_fields)
            return ModelType.UNKNOWN

        # Normalize architecture for matching
        arch_normalized = (
            architecture.lower() if self._case_insensitive else architecture
        )

        # Check image generation patterns
        if self._matches_patterns(arch_normalized, self._image_patterns):
            return ModelType.IMAGE_GENERATION

        # Check text prediction patterns
        if self._matches_patterns(arch_normalized, self._text_patterns):
            return ModelType.TEXT_PREDICTION

        # Try secondary detection if primary patterns don't match
        if secondary_fields:
            secondary_type = self._detect_from_secondary_fields(secondary_fields)
            if secondary_type != ModelType.UNKNOWN:
                return secondary_type

        return ModelType.UNKNOWN

    def _matches_patterns(self, text: str, patterns: Set[str]) -> bool:
        for pattern in patterns:
            pattern_normalized = pattern.lower() if self._case_insensitive else pattern

            if self._substring_match:
                if pattern_normalized in text:
                    return True
            else:
                if pattern_normalized == text:
                    return True

        return False

    def _detect_from_secondary_fields(self, fields: Dict[str, Any]) -> ModelType:
        present_fields = set()

        # Extract field names that have non-empty values
        for key, value in fields.items():
            if value is not None and value != "":
                # Convert from alias format to field name format
                field_name = (
                    key.replace("modelspec.", "")
                    if key.startswith("modelspec.")
                    else key
                )
                present_fields.add(field_name)

        # Check for image generation hints
        if present_fields & self._image_hints:
            return ModelType.IMAGE_GENERATION

        # Check for text prediction hints
        if present_fields & self._text_hints:
            return ModelType.TEXT_PREDICTION

        return ModelType.UNKNOWN
