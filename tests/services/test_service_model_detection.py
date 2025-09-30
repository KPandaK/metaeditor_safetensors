"""
Unit tests for Model Detection Service
=====================================

Tests for the ModelDetectionService class which handles configurable
model type detection based on architecture patterns.
"""

import logging

import pytest

from metaeditor_safetensors.services.model_detection_service import (
    ModelDetectionService,
)
from metaeditor_safetensors.services.utility import ModelType


class TestModelDetectionService:
    """Test cases for ModelDetectionService functionality."""

    def test_initialization_with_default_config(self):
        """Test service initialization with default configuration."""
        service = ModelDetectionService()

        # Should load without errors
        assert service is not None

        # Test that it can detect some basic model types from the default config
        assert (
            service.detect_model_type({"modelspec.architecture": "stable-diffusion"})
            == ModelType.IMAGE_GENERATION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "gpt"})
            == ModelType.TEXT_PREDICTION
        )

    def test_detect_image_generation_models(self):
        """Test detection of image generation models."""
        service = ModelDetectionService()

        # Test models that should be detected as image generation
        assert (
            service.detect_model_type({"modelspec.architecture": "stable-diffusion"})
            == ModelType.IMAGE_GENERATION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "sd-xl"})
            == ModelType.IMAGE_GENERATION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "controlnet"})
            == ModelType.IMAGE_GENERATION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "lora"})
            == ModelType.IMAGE_GENERATION
        )

        # Test substring matches
        assert (
            service.detect_model_type(
                {"modelspec.architecture": "stable-diffusion-v1.5"}
            )
            == ModelType.IMAGE_GENERATION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "my-custom-lora"})
            == ModelType.IMAGE_GENERATION
        )

        # Test case insensitive matching
        assert (
            service.detect_model_type({"modelspec.architecture": "STABLE-DIFFUSION"})
            == ModelType.IMAGE_GENERATION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "ControlNet"})
            == ModelType.IMAGE_GENERATION
        )

    def test_detect_text_prediction_models(self):
        """Test detection of text prediction models."""
        service = ModelDetectionService()

        # Test models that should be detected as text prediction
        assert (
            service.detect_model_type({"modelspec.architecture": "gpt"})
            == ModelType.TEXT_PREDICTION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "llama"})
            == ModelType.TEXT_PREDICTION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "bert"})
            == ModelType.TEXT_PREDICTION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "transformer"})
            == ModelType.TEXT_PREDICTION
        )

        # Test substring matches
        assert (
            service.detect_model_type({"modelspec.architecture": "gpt-4"})
            == ModelType.TEXT_PREDICTION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "llama-2-7b"})
            == ModelType.TEXT_PREDICTION
        )

        # Test case insensitive matching
        assert (
            service.detect_model_type({"modelspec.architecture": "GPT-3"})
            == ModelType.TEXT_PREDICTION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "BERT-Base"})
            == ModelType.TEXT_PREDICTION
        )

    def test_detect_unknown_models(self):
        """Test detection returns UNKNOWN for unrecognized patterns."""
        service = ModelDetectionService()

        assert (
            service.detect_model_type(
                {"modelspec.architecture": "unknown-architecture"}
            )
            == ModelType.UNKNOWN
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "random-model"})
            == ModelType.UNKNOWN
        )
        assert (
            service.detect_model_type({"modelspec.architecture": ""})
            == ModelType.UNKNOWN
        )
        assert service.detect_model_type({}) == ModelType.UNKNOWN

    def test_secondary_field_detection(self):
        """Test model detection using secondary field hints."""
        service = ModelDetectionService()

        # Image generation hints
        secondary_image = {
            "modelspec.architecture": "unknown",
            "modelspec.resolution": "512x512",
            "other_field": "value",
        }
        assert service.detect_model_type(secondary_image) == ModelType.IMAGE_GENERATION

        secondary_image2 = {
            "modelspec.architecture": "unknown",
            "modelspec.trigger_phrase": "my_trigger",
        }
        assert service.detect_model_type(secondary_image2) == ModelType.IMAGE_GENERATION

        # Text prediction hints
        secondary_text = {
            "modelspec.architecture": "unknown",
            "modelspec.format_type": "chat",
            "other_field": "value",
        }
        assert service.detect_model_type(secondary_text) == ModelType.TEXT_PREDICTION

        secondary_text2 = {
            "modelspec.architecture": "unknown",
            "modelspec.language": "english",
        }
        assert service.detect_model_type(secondary_text2) == ModelType.TEXT_PREDICTION

        # No matching hints
        secondary_none = {"modelspec.architecture": "unknown", "random_field": "value"}
        assert service.detect_model_type(secondary_none) == ModelType.UNKNOWN

    def test_architecture_takes_priority_over_secondary(self):
        """Test that architecture patterns take priority over secondary hints."""
        service = ModelDetectionService()

        # Architecture says image generation, secondary hints say text prediction
        fields_with_image_arch = {
            "modelspec.architecture": "stable-diffusion",
            "modelspec.format_type": "chat",
            "modelspec.language": "english",
        }
        assert (
            service.detect_model_type(fields_with_image_arch)
            == ModelType.IMAGE_GENERATION
        )

        # Architecture says text prediction, secondary hints say image generation
        fields_with_text_arch = {
            "modelspec.architecture": "gpt-4",
            "modelspec.resolution": "512x512",
            "modelspec.trigger_phrase": "trigger",
        }
        assert (
            service.detect_model_type(fields_with_text_arch)
            == ModelType.TEXT_PREDICTION
        )

    def test_modelspec_integration(self):
        """Test integration with ModelSpec fields format."""
        service = ModelDetectionService()

        # Test with modelspec.* prefixed fields
        secondary_fields = {
            "modelspec.architecture": "unknown",
            "modelspec.resolution": "1024x1024",
            "modelspec.trigger_phrase": "my_trigger",
            "other_field": "value",
        }

        # Should detect even with modelspec prefix
        result = service.detect_model_type(secondary_fields)
        assert result == ModelType.IMAGE_GENERATION

    def test_empty_architecture_with_secondary_fields(self):
        """Test detection when architecture is empty but secondary fields provide hints."""
        service = ModelDetectionService()

        # Empty architecture should fall back to secondary detection
        secondary_image = {
            "modelspec.architecture": "",
            "modelspec.resolution": "1024x1024",
        }
        assert service.detect_model_type(secondary_image) == ModelType.IMAGE_GENERATION

        secondary_text = {"modelspec.format_type": "instruct"}
        assert service.detect_model_type(secondary_text) == ModelType.TEXT_PREDICTION

    def test_case_sensitivity_and_substring_matching(self):
        """Test case insensitive and substring matching behavior."""
        service = ModelDetectionService()

        # Should work with different cases
        assert (
            service.detect_model_type({"modelspec.architecture": "Stable-Diffusion"})
            == ModelType.IMAGE_GENERATION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "LLAMA"})
            == ModelType.TEXT_PREDICTION
        )

        # Should work with substrings
        assert (
            service.detect_model_type(
                {"modelspec.architecture": "my-stable-diffusion-model"}
            )
            == ModelType.IMAGE_GENERATION
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "custom-gpt-variant"})
            == ModelType.TEXT_PREDICTION
        )

    def test_load_config_failure_sets_defaults(self, mocker, caplog):
        """Configuration load failures should log a warning and fall back to defaults."""
        mocker.patch(
            "metaeditor_safetensors.services.model_detection_service.open",
            side_effect=OSError("missing config"),
            create=True,
        )

        with caplog.at_level(logging.WARNING):
            service = ModelDetectionService()

        assert service._config == {}
        assert any(
            "Error loading model detection config" in record.message
            for record in caplog.records
        )
        assert (
            service.detect_model_type({"modelspec.architecture": "stable-diffusion"})
            == ModelType.UNKNOWN
        )

    def test_exact_match_when_substring_disabled(self):
        """Exact equality matching should be honored when substring checks are disabled."""
        service = ModelDetectionService()
        service._image_patterns = {"ExactMatch"}
        service._text_patterns = set()
        service._image_hints = set()
        service._text_hints = set()
        service._case_insensitive = False
        service._substring_match = False

        result = service.detect_model_type({"modelspec.architecture": "ExactMatch"})
        assert result == ModelType.IMAGE_GENERATION

    def test_unknown_return_when_no_patterns_match(self):
        """Should return UNKNOWN when no patterns or hints match."""
        service = ModelDetectionService()
        service._image_patterns = set()
        service._text_patterns = set()
        service._image_hints = set()
        service._text_hints = set()

        result = service.detect_model_type({"modelspec.architecture": "no-match"})
        assert result == ModelType.UNKNOWN
