"""
Unit tests for Model Detection Service
=====================================

Tests for the ModelDetectionService class which handles configurable
model type detection based on architecture patterns.
"""

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
            service.detect_model_type("stable-diffusion") == ModelType.IMAGE_GENERATION
        )
        assert service.detect_model_type("gpt") == ModelType.TEXT_PREDICTION

    def test_detect_image_generation_models(self):
        """Test detection of image generation models."""
        service = ModelDetectionService()

        # Test models that should be detected as image generation
        assert (
            service.detect_model_type("stable-diffusion") == ModelType.IMAGE_GENERATION
        )
        assert service.detect_model_type("sd-xl") == ModelType.IMAGE_GENERATION
        assert service.detect_model_type("controlnet") == ModelType.IMAGE_GENERATION
        assert service.detect_model_type("lora") == ModelType.IMAGE_GENERATION

        # Test substring matches
        assert (
            service.detect_model_type("stable-diffusion-v1.5")
            == ModelType.IMAGE_GENERATION
        )
        assert service.detect_model_type("my-custom-lora") == ModelType.IMAGE_GENERATION

        # Test case insensitive matching
        assert (
            service.detect_model_type("STABLE-DIFFUSION") == ModelType.IMAGE_GENERATION
        )
        assert service.detect_model_type("ControlNet") == ModelType.IMAGE_GENERATION

    def test_detect_text_prediction_models(self):
        """Test detection of text prediction models."""
        service = ModelDetectionService()

        # Test models that should be detected as text prediction
        assert service.detect_model_type("gpt") == ModelType.TEXT_PREDICTION
        assert service.detect_model_type("llama") == ModelType.TEXT_PREDICTION
        assert service.detect_model_type("bert") == ModelType.TEXT_PREDICTION
        assert service.detect_model_type("transformer") == ModelType.TEXT_PREDICTION

        # Test substring matches
        assert service.detect_model_type("gpt-4") == ModelType.TEXT_PREDICTION
        assert service.detect_model_type("llama-2-7b") == ModelType.TEXT_PREDICTION

        # Test case insensitive matching
        assert service.detect_model_type("GPT-3") == ModelType.TEXT_PREDICTION
        assert service.detect_model_type("BERT-Base") == ModelType.TEXT_PREDICTION

    def test_detect_unknown_models(self):
        """Test detection returns UNKNOWN for unrecognized patterns."""
        service = ModelDetectionService()

        assert service.detect_model_type("unknown-architecture") == ModelType.UNKNOWN
        assert service.detect_model_type("random-model") == ModelType.UNKNOWN
        assert service.detect_model_type("") == ModelType.UNKNOWN
        assert service.detect_model_type(None) == ModelType.UNKNOWN

    def test_secondary_field_detection(self):
        """Test model detection using secondary field hints."""
        service = ModelDetectionService()

        # Image generation hints
        secondary_image = {"resolution": "512x512", "other_field": "value"}
        assert (
            service.detect_model_type("unknown", secondary_image)
            == ModelType.IMAGE_GENERATION
        )

        secondary_image2 = {"trigger_phrase": "my_trigger"}
        assert (
            service.detect_model_type("unknown", secondary_image2)
            == ModelType.IMAGE_GENERATION
        )

        # Text prediction hints
        secondary_text = {"format_type": "chat", "other_field": "value"}
        assert (
            service.detect_model_type("unknown", secondary_text)
            == ModelType.TEXT_PREDICTION
        )

        secondary_text2 = {"language": "english"}
        assert (
            service.detect_model_type("unknown", secondary_text2)
            == ModelType.TEXT_PREDICTION
        )

        # No matching hints
        secondary_none = {"random_field": "value"}
        assert service.detect_model_type("unknown", secondary_none) == ModelType.UNKNOWN

    def test_architecture_takes_priority_over_secondary(self):
        """Test that architecture patterns take priority over secondary hints."""
        service = ModelDetectionService()

        # Architecture says image generation, secondary hints say text prediction
        secondary_text = {"format_type": "chat", "language": "english"}
        assert (
            service.detect_model_type("stable-diffusion", secondary_text)
            == ModelType.IMAGE_GENERATION
        )

        # Architecture says text prediction, secondary hints say image generation
        secondary_image = {"resolution": "512x512", "trigger_phrase": "trigger"}
        assert (
            service.detect_model_type("gpt-4", secondary_image)
            == ModelType.TEXT_PREDICTION
        )

    def test_modelspec_integration(self):
        """Test integration with ModelSpec fields format."""
        service = ModelDetectionService()

        # Test with modelspec.* prefixed fields
        secondary_fields = {
            "modelspec.resolution": "1024x1024",
            "modelspec.trigger_phrase": "my_trigger",
            "other_field": "value",
        }

        # Should detect even with modelspec prefix
        result = service.detect_model_type("unknown", secondary_fields)
        assert result == ModelType.IMAGE_GENERATION

    def test_empty_architecture_with_secondary_fields(self):
        """Test detection when architecture is empty but secondary fields provide hints."""
        service = ModelDetectionService()

        # Empty architecture should fall back to secondary detection
        secondary_image = {"resolution": "1024x1024"}
        assert (
            service.detect_model_type("", secondary_image) == ModelType.IMAGE_GENERATION
        )

        secondary_text = {"format_type": "instruct"}
        assert (
            service.detect_model_type(None, secondary_text) == ModelType.TEXT_PREDICTION
        )

    def test_case_sensitivity_and_substring_matching(self):
        """Test case insensitive and substring matching behavior."""
        service = ModelDetectionService()

        # Should work with different cases
        assert (
            service.detect_model_type("Stable-Diffusion") == ModelType.IMAGE_GENERATION
        )
        assert service.detect_model_type("LLAMA") == ModelType.TEXT_PREDICTION

        # Should work with substrings
        assert (
            service.detect_model_type("my-stable-diffusion-model")
            == ModelType.IMAGE_GENERATION
        )
        assert (
            service.detect_model_type("custom-gpt-variant") == ModelType.TEXT_PREDICTION
        )
