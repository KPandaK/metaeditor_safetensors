"""
Metadata Model
==============

This module defines the `MetadataModel`, which is the central data store for the
application. It manages the safetensors metadata, tracks changes, and notifies
observers when the data is modified.

It is designed to be completely independent of the UI (View) and the application
logic (Controller).
"""

import copy
from typing import Any, Callable, Dict, List, Set


class MetadataModel:
    """
    Manages the application's metadata.

    This class holds the metadata from a safetensors file, keeps track of
    the original state to detect changes ("dirty" state), and allows observers
    to register for notifications when the data changes.
    """

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._original_data: Dict[str, Any] = {}
        self._observers: List[Callable] = []

    def load_data(self, data: Dict[str, Any]):
        """
        Loads a new set of metadata.

        This resets the model with new data, typically after loading a file.
        The original state is stored for future comparisons.

        Args:
            data: The metadata dictionary to load.
        """
        self._data = copy.deepcopy(data)
        self._original_data = copy.deepcopy(data)
        self._notify_observers()

    def get_all_data(self) -> Dict[str, Any]:
        """Returns a copy of the current metadata."""
        return copy.deepcopy(self._data)

    def get_value(self, key: str, default: Any = "") -> Any:
        """
        Retrieves the value for a specific metadata key.

        Args:
            key: The key of the value to retrieve.
            default: The value to return if the key is not found.

        Returns:
            The value associated with the key, or the default.
        """
        return self._data.get(key, default)

    def set_value(self, key: str, value: Any):
        """
        Sets the value for a specific metadata key.

        If the new value is different from the current value, the model's
        data is updated, and observers are notified.

        Args:
            key: The key of the value to set.
            value: The new value.
        """
        if self.get_value(key) != value:
            self._data[key] = value
            self._notify_observers()

    def is_dirty(self) -> bool:
        """
        Checks if the metadata has been modified since it was last loaded
        or saved.

        Returns:
            True if the data has changed, False otherwise.
        """
        return self._data != self._original_data

    def get_dirty_fields(self) -> Set[str]:
        """
        Returns a set of keys that have been changed from the original.

        Returns:
            A set containing the keys of all modified fields.
        """
        original_keys = set(self._original_data.keys())
        current_keys = set(self._data.keys())

        changed_keys = set()

        # Check for modified and added keys
        for key in current_keys:
            if key not in original_keys or self._data[key] != self._original_data[key]:
                changed_keys.add(key)

        # Check for removed keys
        changed_keys.update(original_keys - current_keys)

        return changed_keys

    def mark_saved(self):
        """
        Marks the current state as saved by updating the original data.
        This is typically called after a successful save operation.
        """
        self._original_data = copy.deepcopy(self._data)
        self._notify_observers()

    def add_observer(self, observer: Callable):
        """
        Registers an observer to be notified of data changes.

        Args:
            observer: A callable (function or method) that will be called
                      when the model's data changes.
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Callable):
        """
        Unregisters an observer.

        Args:
            observer: The observer to remove.
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self):
        """Calls all registered observers."""
        for observer in self._observers:
            observer()
