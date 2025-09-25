"""
Unit tests for Metadata Model
=============================

Tests for metadata model functionality including data management,
observer pattern, dirty state tracking, and change detection.
"""

from typing import Any, Dict

import pytest

from metaeditor_safetensors.models.metadata import Metadata


@pytest.fixture
def model():
    """Create a fresh Metadata instance for each test."""
    return Metadata()


@pytest.fixture
def observer_tracker():
    """Create an observer tracker for testing observer pattern."""

    class ObserverTracker:
        def __init__(self):
            self.called = False
            self.call_count = 0

        def observer(self):
            """Observer method to track calls."""
            self.called = True
            self.call_count += 1

        def reset(self):
            """Reset the tracker state."""
            self.called = False
            self.call_count = 0

    return ObserverTracker()


class TestMetadata:
    """Test cases for Metadata class functionality."""

    def test_initialization(self, model):
        """Test that Metadata initializes correctly."""
        assert model.get_all_data() == {}
        assert not model.is_dirty()
        assert model.get_dirty_fields() == set()

    def test_load_data(self, model):
        """Test loading data into the model."""
        test_data = {
            "title": "Test Model",
            "author": "Test Author",
            "description": "A test model",
        }

        model.load_data(test_data)
        assert model.get_all_data() == test_data
        assert not model.is_dirty()

    def test_load_data_creates_copy(self, model):
        """Test that load_data creates a deep copy of the input data."""
        test_data = {"nested": {"inner": "value"}, "list": [1, 2, 3]}

        model.load_data(test_data)

        # Modify original data
        test_data["nested"]["inner"] = "modified"
        test_data["list"].append(4)

        # Model data should be unchanged
        model_data = model.get_all_data()
        assert model_data["nested"]["inner"] == "value"
        assert model_data["list"] == [1, 2, 3]

    def test_get_all_data_returns_copy(self, model):
        """Test that get_all_data returns a copy, not a reference."""
        test_data = {"key": "value"}
        model.load_data(test_data)

        retrieved_data = model.get_all_data()
        retrieved_data["key"] = "modified"

        # Original model data should be unchanged
        assert model.get_value("key") == "value"

    def test_get_value(self, model):
        """Test retrieving values from the model."""
        test_data = {
            "string_key": "test_value",
            "number_key": 42,
            "bool_key": True,
            "none_key": None,
        }
        model.load_data(test_data)

        assert model.get_value("string_key") == "test_value"
        assert model.get_value("number_key") == 42
        assert model.get_value("bool_key") is True
        assert model.get_value("none_key") is None

    def test_get_value_with_default(self, model):
        """Test retrieving values with default fallback."""
        model.load_data({"existing_key": "value"})

        # Existing key should return actual value
        assert model.get_value("existing_key") == "value"

        # Non-existing key should return default
        assert model.get_value("missing_key") == ""
        assert model.get_value("missing_key", "custom_default") == "custom_default"
        assert model.get_value("missing_key", None) is None
        assert model.get_value("missing_key", 42) == 42

    def test_set_value(self, model):
        """Test setting values in the model."""
        model.set_value("new_key", "new_value")
        assert model.get_value("new_key") == "new_value"
        assert model.is_dirty()

    def test_set_value_same_value_no_change(self, model):
        """Test that setting the same value doesn't mark model as dirty."""
        model.load_data({"key": "value"})
        assert not model.is_dirty()

        # Set same value
        model.set_value("key", "value")
        assert not model.is_dirty()

    def test_set_value_different_value_marks_dirty(self, model):
        """Test that setting a different value marks model as dirty."""
        model.load_data({"key": "original"})
        assert not model.is_dirty()

        # Set different value
        model.set_value("key", "modified")
        assert model.is_dirty()

    def test_set_value_updates_existing(self, model):
        """Test updating existing values."""
        model.load_data({"key": "original"})
        model.set_value("key", "updated")
        assert model.get_value("key") == "updated"

    def test_is_dirty_initial_state(self, model):
        """Test dirty state after initialization."""
        assert not model.is_dirty()

    def test_is_dirty_after_load(self, model):
        """Test dirty state after loading data."""
        model.load_data({"key": "value"})
        assert not model.is_dirty()

    def test_is_dirty_after_modification(self, model):
        """Test dirty state after modifying data."""
        model.load_data({"key": "value"})
        model.set_value("key", "new_value")
        assert model.is_dirty()

    def test_get_dirty_fields_no_changes(self, model):
        """Test getting dirty fields when no changes exist."""
        model.load_data({"key1": "value1", "key2": "value2"})
        assert model.get_dirty_fields() == set()

    def test_get_dirty_fields_modified_keys(self, model):
        """Test getting dirty fields for modified keys."""
        model.load_data({"key1": "value1", "key2": "value2"})
        model.set_value("key1", "modified")

        dirty_fields = model.get_dirty_fields()
        assert dirty_fields == {"key1"}

    def test_get_dirty_fields_added_keys(self, model):
        """Test getting dirty fields for added keys."""
        model.load_data({"key1": "value1"})
        model.set_value("key2", "new_value")

        dirty_fields = model.get_dirty_fields()
        assert dirty_fields == {"key2"}

    def test_get_dirty_fields_removed_keys(self, model):
        """Test getting dirty fields for conceptually removed keys."""
        # Note: The current implementation doesn't have explicit remove functionality,
        # but we can test the logic by manipulating internal state
        model.load_data({"key1": "value1", "key2": "value2"})

        # Simulate removal by directly modifying internal data
        del model._data["key2"]

        dirty_fields = model.get_dirty_fields()
        assert "key2" in dirty_fields

    def test_get_dirty_fields_multiple_changes(self, model):
        """Test getting dirty fields with multiple types of changes."""
        model.load_data({"key1": "value1", "key2": "value2"})

        # Modify existing key
        model.set_value("key1", "modified")
        # Add new key
        model.set_value("key3", "new")

        dirty_fields = model.get_dirty_fields()
        expected_dirty = {"key1", "key3"}
        assert dirty_fields == expected_dirty

    def test_mark_saved(self, model):
        """Test marking the model as saved."""
        model.load_data({"key": "value"})
        model.set_value("key", "modified")
        assert model.is_dirty()

        model.mark_saved()
        assert not model.is_dirty()
        assert model.get_dirty_fields() == set()

    def test_mark_saved_updates_original_data(self, model):
        """Test that mark_saved updates the original data reference."""
        model.load_data({"key": "original"})
        model.set_value("key", "modified")

        model.mark_saved()

        # Further changes should be detected against the new "saved" state
        model.set_value("key", "further_modified")
        assert model.is_dirty()
        assert model.get_dirty_fields() == {"key"}

    def test_add_observer(self, model, observer_tracker):
        """Test adding observers to the model."""
        model.add_observer(observer_tracker.observer)

        # Observer should be called when data changes
        model.set_value("key", "value")
        assert observer_tracker.called

    def test_add_observer_duplicate(self, model, observer_tracker):
        """Test that adding the same observer twice doesn't duplicate it."""
        model.add_observer(observer_tracker.observer)
        model.add_observer(observer_tracker.observer)  # Add again

        model.set_value("key", "value")
        assert observer_tracker.call_count == 1

    def test_remove_observer(self, model, observer_tracker):
        """Test removing observers from the model."""
        model.add_observer(observer_tracker.observer)
        model.remove_observer(observer_tracker.observer)

        # Observer should not be called after removal
        model.set_value("key", "value")
        assert not observer_tracker.called

    def test_remove_observer_not_present(self, model):
        """Test removing an observer that was never added."""

        # Should not raise an exception
        def dummy_observer():
            pass

        model.remove_observer(dummy_observer)

    def test_observer_called_on_load_data(self, model, observer_tracker):
        """Test that observers are notified when data is loaded."""
        model.add_observer(observer_tracker.observer)
        model.load_data({"key": "value"})
        assert observer_tracker.called

    def test_observer_called_on_set_value(self, model, observer_tracker):
        """Test that observers are notified when values are set."""
        model.add_observer(observer_tracker.observer)
        model.set_value("key", "value")
        assert observer_tracker.called

    def test_observer_not_called_on_same_value(self, model, observer_tracker):
        """Test that observers are not notified when setting the same value."""
        model.load_data({"key": "value"})
        model.add_observer(observer_tracker.observer)

        model.set_value("key", "value")  # Same value
        assert not observer_tracker.called

    def test_observer_called_on_mark_saved(self, model, observer_tracker):
        """Test that observers are notified when model is marked as saved."""
        model.set_value("key", "value")
        model.add_observer(observer_tracker.observer)

        model.mark_saved()
        assert observer_tracker.called

    def test_multiple_observers(self, model):
        """Test that multiple observers are all notified."""
        observer_calls = []

        def observer1():
            observer_calls.append(1)

        def observer2():
            observer_calls.append(2)

        model.add_observer(observer1)
        model.add_observer(observer2)

        model.set_value("key", "value")

        assert len(observer_calls) == 2
        assert 1 in observer_calls
        assert 2 in observer_calls

    def test_complex_data_types(self, model):
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
            "empty_dict": {},
        }

        model.load_data(complex_data)

        for key, expected_value in complex_data.items():
            assert model.get_value(key) == expected_value

    def test_deep_copy_behavior(self, model):
        """Test that deep copying works correctly for nested structures."""
        nested_data = {"level1": {"level2": {"level3": ["item1", "item2"]}}}

        model.load_data(nested_data)

        # Modify the nested structure
        model.set_value("level1", {"level2": {"level3": ["item1", "item2", "item3"]}})

        # Verify the change was tracked
        assert model.is_dirty()
        assert "level1" in model.get_dirty_fields()
