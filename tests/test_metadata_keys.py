"""
Unit tests for Metadata Keys
============================

Tests for metadata key constants and their values.
"""

from metaeditor_safetensors.models.metadata_keys import MetadataKeys


class TestMetadataKeys:
    """Test cases for MetadataKeys class constants."""

    def test_main_field_keys(self):
        """Test that main field keys have correct values."""
        assert MetadataKeys.TITLE == "modelspec.title"
        assert MetadataKeys.DESCRIPTION == "modelspec.description"
        assert MetadataKeys.AUTHOR == "modelspec.author"
        assert MetadataKeys.DATE == "modelspec.date"
        assert MetadataKeys.LICENSE == "modelspec.license"
        assert MetadataKeys.USAGE_HINT == "modelspec.usage_hint"

    def test_complex_field_keys(self):
        """Test that complex field keys have correct values."""
        assert MetadataKeys.TAGS == "modelspec.tags"
        assert MetadataKeys.MERGED_FROM == "modelspec.merged_from"

    def test_thumbnail_key(self):
        """Test that thumbnail key has correct value."""
        assert MetadataKeys.THUMBNAIL == "modelspec.thumbnail"

    def test_all_keys_are_strings(self):
        """Test that all metadata keys are strings."""
        keys = [
            MetadataKeys.TITLE,
            MetadataKeys.DESCRIPTION,
            MetadataKeys.AUTHOR,
            MetadataKeys.DATE,
            MetadataKeys.LICENSE,
            MetadataKeys.USAGE_HINT,
            MetadataKeys.TAGS,
            MetadataKeys.MERGED_FROM,
            MetadataKeys.THUMBNAIL,
        ]

        for key in keys:
            assert isinstance(key, str), f"Key {key} should be a string"

    def test_all_keys_follow_modelspec_format(self):
        """Test that all keys follow the modelspec.* format."""
        keys = [
            MetadataKeys.TITLE,
            MetadataKeys.DESCRIPTION,
            MetadataKeys.AUTHOR,
            MetadataKeys.DATE,
            MetadataKeys.LICENSE,
            MetadataKeys.USAGE_HINT,
            MetadataKeys.TAGS,
            MetadataKeys.MERGED_FROM,
            MetadataKeys.THUMBNAIL,
        ]

        for key in keys:
            assert key.startswith(
                "modelspec."
            ), f"Key {key} should start with 'modelspec.'"

    def test_key_uniqueness(self):
        """Test that all metadata keys are unique."""
        keys = [
            MetadataKeys.TITLE,
            MetadataKeys.DESCRIPTION,
            MetadataKeys.AUTHOR,
            MetadataKeys.DATE,
            MetadataKeys.LICENSE,
            MetadataKeys.USAGE_HINT,
            MetadataKeys.TAGS,
            MetadataKeys.MERGED_FROM,
            MetadataKeys.THUMBNAIL,
        ]

        unique_keys = set(keys)
        assert len(keys) == len(unique_keys), "All metadata keys should be unique"

    def test_key_non_empty(self):
        """Test that all metadata keys are non-empty."""
        keys = [
            MetadataKeys.TITLE,
            MetadataKeys.DESCRIPTION,
            MetadataKeys.AUTHOR,
            MetadataKeys.DATE,
            MetadataKeys.LICENSE,
            MetadataKeys.USAGE_HINT,
            MetadataKeys.TAGS,
            MetadataKeys.MERGED_FROM,
            MetadataKeys.THUMBNAIL,
        ]

        for key in keys:
            assert key.strip(), f"Key {key} should not be empty or whitespace"

    def test_metadata_keys_class_attributes(self):
        """Test that MetadataKeys class has expected attributes."""
        expected_attributes = [
            "TITLE",
            "DESCRIPTION",
            "AUTHOR",
            "DATE",
            "LICENSE",
            "USAGE_HINT",
            "TAGS",
            "MERGED_FROM",
            "THUMBNAIL",
        ]

        for attr in expected_attributes:
            assert hasattr(
                MetadataKeys, attr
            ), f"MetadataKeys should have attribute {attr}"
