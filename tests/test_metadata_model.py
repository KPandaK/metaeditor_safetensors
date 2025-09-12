"""
Unit tests for Metadata Model
=============================

Tests for metadata model functionality including data management,
observer pattern, dirty state tracking, and change detection.
"""

import unittest
from typing import Any, Dict

from metaeditor_safetensors.models.metadata_model import MetadataModel


class TestMetadataModel(unittest.TestCase):
    """Test cases for MetadataModel class functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.model = MetadataModel()
        self.observer_called = False
        self.observer_call_count = 0

    def test_initialization(self):
        """Test that MetadataModel initializes correctly."""
        model = MetadataModel()
        self.assertEqual(model.get_all_data(), {})
        self.assertFalse(model.is_dirty())
        self.assertEqual(model.get_dirty_fields(), set())

    def test_load_data(self):
        """Test loading data into the model."""
        test_data = {
            "title": "Test Model",
            "author": "Test Author",
            "description": "A test model"
        }
        
        self.model.load_data(test_data)
        self.assertEqual(self.model.get_all_data(), test_data)
        self.assertFalse(self.model.is_dirty())

    def test_load_data_creates_copy(self):
        """Test that load_data creates a deep copy of the input data."""
        test_data = {
            "nested": {"inner": "value"},
            "list": [1, 2, 3]
        }
        
        self.model.load_data(test_data)
        
        # Modify original data
        test_data["nested"]["inner"] = "modified"
        test_data["list"].append(4)
        
        # Model data should be unchanged
        model_data = self.model.get_all_data()
        self.assertEqual(model_data["nested"]["inner"], "value")
        self.assertEqual(model_data["list"], [1, 2, 3])

    def test_get_all_data_returns_copy(self):
        """Test that get_all_data returns a copy, not a reference."""
        test_data = {"key": "value"}
        self.model.load_data(test_data)
        
        retrieved_data = self.model.get_all_data()
        retrieved_data["key"] = "modified"
        
        # Original model data should be unchanged
        self.assertEqual(self.model.get_value("key"), "value")

    def test_get_value(self):
        """Test retrieving values from the model."""
        test_data = {
            "string_key": "test_value",
            "number_key": 42,
            "bool_key": True,
            "none_key": None
        }
        self.model.load_data(test_data)
        
        self.assertEqual(self.model.get_value("string_key"), "test_value")
        self.assertEqual(self.model.get_value("number_key"), 42)
        self.assertEqual(self.model.get_value("bool_key"), True)
        self.assertIsNone(self.model.get_value("none_key"))

    def test_get_value_with_default(self):
        """Test retrieving values with default fallback."""
        self.model.load_data({"existing_key": "value"})
        
        # Existing key should return actual value
        self.assertEqual(self.model.get_value("existing_key"), "value")
        
        # Non-existing key should return default
        self.assertEqual(self.model.get_value("missing_key"), "")
        self.assertEqual(self.model.get_value("missing_key", "custom_default"), "custom_default")
        self.assertEqual(self.model.get_value("missing_key", None), None)
        self.assertEqual(self.model.get_value("missing_key", 42), 42)

    def test_set_value(self):
        """Test setting values in the model."""
        self.model.set_value("new_key", "new_value")
        self.assertEqual(self.model.get_value("new_key"), "new_value")
        self.assertTrue(self.model.is_dirty())

    def test_set_value_same_value_no_change(self):
        """Test that setting the same value doesn't mark model as dirty."""
        self.model.load_data({"key": "value"})
        self.assertFalse(self.model.is_dirty())
        
        # Set same value
        self.model.set_value("key", "value")
        self.assertFalse(self.model.is_dirty())

    def test_set_value_different_value_marks_dirty(self):
        """Test that setting a different value marks model as dirty."""
        self.model.load_data({"key": "original"})
        self.assertFalse(self.model.is_dirty())
        
        # Set different value
        self.model.set_value("key", "modified")
        self.assertTrue(self.model.is_dirty())

    def test_set_value_updates_existing(self):
        """Test updating existing values."""
        self.model.load_data({"key": "original"})
        self.model.set_value("key", "updated")
        self.assertEqual(self.model.get_value("key"), "updated")

    def test_is_dirty_initial_state(self):
        """Test dirty state after initialization."""
        self.assertFalse(self.model.is_dirty())

    def test_is_dirty_after_load(self):
        """Test dirty state after loading data."""
        self.model.load_data({"key": "value"})
        self.assertFalse(self.model.is_dirty())

    def test_is_dirty_after_modification(self):
        """Test dirty state after modifying data."""
        self.model.load_data({"key": "value"})
        self.model.set_value("key", "new_value")
        self.assertTrue(self.model.is_dirty())

    def test_get_dirty_fields_no_changes(self):
        """Test getting dirty fields when no changes exist."""
        self.model.load_data({"key1": "value1", "key2": "value2"})
        self.assertEqual(self.model.get_dirty_fields(), set())

    def test_get_dirty_fields_modified_keys(self):
        """Test getting dirty fields for modified keys."""
        self.model.load_data({"key1": "value1", "key2": "value2"})
        self.model.set_value("key1", "modified")
        
        dirty_fields = self.model.get_dirty_fields()
        self.assertEqual(dirty_fields, {"key1"})

    def test_get_dirty_fields_added_keys(self):
        """Test getting dirty fields for added keys."""
        self.model.load_data({"key1": "value1"})
        self.model.set_value("key2", "new_value")
        
        dirty_fields = self.model.get_dirty_fields()
        self.assertEqual(dirty_fields, {"key2"})

    def test_get_dirty_fields_removed_keys(self):
        """Test getting dirty fields for conceptually removed keys."""
        # Note: The current implementation doesn't have explicit remove functionality,
        # but we can test the logic by manipulating internal state
        self.model.load_data({"key1": "value1", "key2": "value2"})
        
        # Simulate removal by directly modifying internal data
        del self.model._data["key2"]
        
        dirty_fields = self.model.get_dirty_fields()
        self.assertIn("key2", dirty_fields)

    def test_get_dirty_fields_multiple_changes(self):
        """Test getting dirty fields with multiple types of changes."""
        self.model.load_data({"key1": "value1", "key2": "value2"})
        
        # Modify existing key
        self.model.set_value("key1", "modified")
        # Add new key
        self.model.set_value("key3", "new")
        
        dirty_fields = self.model.get_dirty_fields()
        expected_dirty = {"key1", "key3"}
        self.assertEqual(dirty_fields, expected_dirty)

    def test_mark_saved(self):
        """Test marking the model as saved."""
        self.model.load_data({"key": "value"})
        self.model.set_value("key", "modified")
        self.assertTrue(self.model.is_dirty())
        
        self.model.mark_saved()
        self.assertFalse(self.model.is_dirty())
        self.assertEqual(self.model.get_dirty_fields(), set())

    def test_mark_saved_updates_original_data(self):
        """Test that mark_saved updates the original data reference."""
        self.model.load_data({"key": "original"})
        self.model.set_value("key", "modified")
        
        self.model.mark_saved()
        
        # Further changes should be detected against the new "saved" state
        self.model.set_value("key", "further_modified")
        self.assertTrue(self.model.is_dirty())
        self.assertEqual(self.model.get_dirty_fields(), {"key"})

    def _test_observer(self):
        """Helper method to track observer calls."""
        self.observer_called = True
        self.observer_call_count += 1

    def test_add_observer(self):
        """Test adding observers to the model."""
        self.model.add_observer(self._test_observer)
        
        # Observer should be called when data changes
        self.model.set_value("key", "value")
        self.assertTrue(self.observer_called)

    def test_add_observer_duplicate(self):
        """Test that adding the same observer twice doesn't duplicate it."""
        self.model.add_observer(self._test_observer)
        self.model.add_observer(self._test_observer)  # Add again
        
        self.model.set_value("key", "value")
        self.assertEqual(self.observer_call_count, 1)

    def test_remove_observer(self):
        """Test removing observers from the model."""
        self.model.add_observer(self._test_observer)
        self.model.remove_observer(self._test_observer)
        
        # Observer should not be called after removal
        self.model.set_value("key", "value")
        self.assertFalse(self.observer_called)

    def test_remove_observer_not_present(self):
        """Test removing an observer that was never added."""
        # Should not raise an exception
        self.model.remove_observer(self._test_observer)

    def test_observer_called_on_load_data(self):
        """Test that observers are notified when data is loaded."""
        self.model.add_observer(self._test_observer)
        self.model.load_data({"key": "value"})
        self.assertTrue(self.observer_called)

    def test_observer_called_on_set_value(self):
        """Test that observers are notified when values are set."""
        self.model.add_observer(self._test_observer)
        self.model.set_value("key", "value")
        self.assertTrue(self.observer_called)

    def test_observer_not_called_on_same_value(self):
        """Test that observers are not notified when setting the same value."""
        self.model.load_data({"key": "value"})
        self.model.add_observer(self._test_observer)
        
        self.model.set_value("key", "value")  # Same value
        self.assertFalse(self.observer_called)

    def test_observer_called_on_mark_saved(self):
        """Test that observers are notified when model is marked as saved."""
        self.model.set_value("key", "value")
        self.model.add_observer(self._test_observer)
        
        self.model.mark_saved()
        self.assertTrue(self.observer_called)

    def test_multiple_observers(self):
        """Test that multiple observers are all notified."""
        observer_calls = []
        
        def observer1():
            observer_calls.append(1)
            
        def observer2():
            observer_calls.append(2)
        
        self.model.add_observer(observer1)
        self.model.add_observer(observer2)
        
        self.model.set_value("key", "value")
        
        self.assertEqual(len(observer_calls), 2)
        self.assertIn(1, observer_calls)
        self.assertIn(2, observer_calls)

    def test_complex_data_types(self):
        """Test that the model handles complex data types correctly."""
        complex_data = {
            "string": "test",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "empty_list": [],
            "empty_dict": {}
        }
        
        self.model.load_data(complex_data)
        
        for key, expected_value in complex_data.items():
            self.assertEqual(self.model.get_value(key), expected_value)

    def test_deep_copy_behavior(self):
        """Test that deep copying works correctly for nested structures."""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": ["item1", "item2"]
                }
            }
        }
        
        self.model.load_data(nested_data)
        
        # Modify the nested structure
        self.model.set_value("level1", {
            "level2": {
                "level3": ["item1", "item2", "item3"]
            }
        })
        
        # Verify the change was tracked
        self.assertTrue(self.model.is_dirty())
        self.assertIn("level1", self.model.get_dirty_fields())


if __name__ == "__main__":
    unittest.main()