"""
Unit tests for Metadata Keys
============================

Tests for metadata key constants and their values.
"""

import unittest

from metaeditor_safetensors.models.metadata_keys import MetadataKeys


class TestMetadataKeys(unittest.TestCase):
    """Test cases for MetadataKeys class constants."""

    def test_main_field_keys(self):
        """Test that main field keys have correct values."""
        self.assertEqual(MetadataKeys.TITLE, "modelspec.title")
        self.assertEqual(MetadataKeys.DESCRIPTION, "modelspec.description")
        self.assertEqual(MetadataKeys.AUTHOR, "modelspec.author")
        self.assertEqual(MetadataKeys.DATE, "modelspec.date")
        self.assertEqual(MetadataKeys.LICENSE, "modelspec.license")
        self.assertEqual(MetadataKeys.USAGE_HINT, "modelspec.usage_hint")

    def test_complex_field_keys(self):
        """Test that complex field keys have correct values."""
        self.assertEqual(MetadataKeys.TAGS, "modelspec.tags")
        self.assertEqual(MetadataKeys.MERGED_FROM, "modelspec.merged_from")

    def test_thumbnail_key(self):
        """Test that thumbnail key has correct value."""
        self.assertEqual(MetadataKeys.THUMBNAIL, "modelspec.thumbnail")

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
            self.assertIsInstance(key, str, f"Key {key} should be a string")

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
            self.assertTrue(
                key.startswith("modelspec."),
                f"Key {key} should start with 'modelspec.'"
            )

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
        self.assertEqual(
            len(keys), 
            len(unique_keys),
            "All metadata keys should be unique"
        )

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
            self.assertTrue(key.strip(), f"Key {key} should not be empty or whitespace")

    def test_metadata_keys_class_attributes(self):
        """Test that MetadataKeys class has expected attributes."""
        expected_attributes = [
            'TITLE', 'DESCRIPTION', 'AUTHOR', 'DATE', 'LICENSE', 'USAGE_HINT',
            'TAGS', 'MERGED_FROM', 'THUMBNAIL'
        ]
        
        for attr in expected_attributes:
            self.assertTrue(
                hasattr(MetadataKeys, attr),
                f"MetadataKeys should have attribute {attr}"
            )


if __name__ == "__main__":
    unittest.main()