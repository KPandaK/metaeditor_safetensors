"""
Metadata Model - manages safetensors metadata with validation and change tracking.
"""

import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime
import copy

logger = logging.getLogger(__name__)


class MetadataModel:
    """
    Manages metadata for a safetensors file with validation and change tracking.
    
    This model handles:
    - Storing and retrieving metadata values
    - Tracking changes and dirty state
    - Validation of field values
    - Undo/redo capabilities
    """
    
    def __init__(self, field_config=None):
        """
        Initialize metadata model.
        
        Args:
            field_config: FieldConfiguration instance for validation
        """
        self._data: Dict[str, Any] = {}
        self._original_data: Dict[str, Any] = {}
        self._field_config = field_config
        self._dirty_fields: Set[str] = set()
        self._history: list[Dict[str, Any]] = []
        self._history_index = -1
        self._max_history = 50
        
        # Observers for change notifications
        self._observers: list = []
    
    def load_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Load metadata from external source (e.g., file).
        
        Args:
            metadata: Dictionary containing metadata
        """
        self._data = copy.deepcopy(metadata)
        self._original_data = copy.deepcopy(metadata)
        self._dirty_fields.clear()
        self._save_to_history()
        self._notify_observers('metadata_loaded')
        
        logger.info(f"Loaded metadata with {len(metadata)} fields")
    
    def get_field_value(self, field_name: str) -> str:
        """
        Get value for a field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Field value as string, empty string if not found
        """
        if self._field_config:
            metadata_key = self._field_config.get_metadata_key(field_name)
        else:
            metadata_key = field_name
        
        return str(self._data.get(metadata_key, ""))
    
    def set_field_value(self, field_name: str, value: str) -> None:
        """
        Set value for a field.
        
        Args:
            field_name: Name of the field
            value: New value for the field
        """
        if self._field_config:
            metadata_key = self._field_config.get_metadata_key(field_name)
        else:
            metadata_key = field_name
        
        old_value = self._data.get(metadata_key, "")
        
        if str(old_value) != value:
            self._data[metadata_key] = value
            self._dirty_fields.add(field_name)
            self._save_to_history()
            self._notify_observers('field_changed', field_name, value)
    
    def get_all_metadata(self) -> Dict[str, Any]:
        """
        Get all metadata as a dictionary.
        
        Returns:
            Copy of all metadata
        """
        return copy.deepcopy(self._data)
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple metadata fields at once.
        
        Args:
            updates: Dictionary of field updates
        """
        for key, value in updates.items():
            old_value = self._data.get(key, "")
            if str(old_value) != str(value):
                self._data[key] = value
                # Try to find the field name for this key
                if self._field_config:
                    for field_name in self._field_config.get_field_names():
                        if self._field_config.get_metadata_key(field_name) == key:
                            self._dirty_fields.add(field_name)
                            break
        
        self._save_to_history()
        self._notify_observers('metadata_updated')
    
    def is_dirty(self) -> bool:
        """
        Check if metadata has been modified.
        
        Returns:
            True if metadata has unsaved changes
        """
        return len(self._dirty_fields) > 0
    
    def get_dirty_fields(self) -> Set[str]:
        """
        Get set of fields that have been modified.
        
        Returns:
            Set of field names that have been changed
        """
        return self._dirty_fields.copy()
    
    def mark_clean(self) -> None:
        """Mark metadata as clean (saved)."""
        self._dirty_fields.clear()
        self._original_data = copy.deepcopy(self._data)
        self._notify_observers('metadata_saved')
    
    def reset_to_original(self) -> None:
        """Reset all changes back to original loaded state."""
        self._data = copy.deepcopy(self._original_data)
        self._dirty_fields.clear()
        self._save_to_history()
        self._notify_observers('metadata_reset')
    
    def validate_all_fields(self) -> tuple[bool, Dict[str, list[str]]]:
        """
        Validate all fields against their rules.
        
        Returns:
            Tuple of (is_valid, dict_of_field_errors)
        """
        if not self._field_config:
            return True, {}
        
        all_errors = {}
        is_valid = True
        
        for field_name in self._field_config.get_field_names():
            value = self.get_field_value(field_name)
            field_valid, errors = self._field_config.validate_field_value(field_name, value)
            
            if not field_valid:
                all_errors[field_name] = errors
                is_valid = False
        
        return is_valid, all_errors
    
    def validate_field(self, field_name: str) -> tuple[bool, list[str]]:
        """
        Validate a single field.
        
        Args:
            field_name: Name of the field to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if not self._field_config:
            return True, []
        
        value = self.get_field_value(field_name)
        return self._field_config.validate_field_value(field_name, value)
    
    def _save_to_history(self) -> None:
        """Save current state to history for undo/redo."""
        # Remove any history beyond current index
        self._history = self._history[:self._history_index + 1]
        
        # Add current state
        self._history.append(copy.deepcopy(self._data))
        
        # Limit history size
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        self._history_index = len(self._history) - 1
    
    def can_undo(self) -> bool:
        """Check if undo operation is possible."""
        return self._history_index > 0
    
    def can_redo(self) -> bool:
        """Check if redo operation is possible."""
        return self._history_index < len(self._history) - 1
    
    def undo(self) -> bool:
        """
        Undo last change.
        
        Returns:
            True if undo was performed
        """
        if self.can_undo():
            self._history_index -= 1
            self._data = copy.deepcopy(self._history[self._history_index])
            self._recalculate_dirty_fields()
            self._notify_observers('metadata_undone')
            return True
        return False
    
    def redo(self) -> bool:
        """
        Redo last undone change.
        
        Returns:
            True if redo was performed
        """
        if self.can_redo():
            self._history_index += 1
            self._data = copy.deepcopy(self._history[self._history_index])
            self._recalculate_dirty_fields()
            self._notify_observers('metadata_redone')
            return True
        return False
    
    def _recalculate_dirty_fields(self) -> None:
        """Recalculate which fields are dirty after undo/redo."""
        self._dirty_fields.clear()
        
        if not self._field_config:
            return
        
        for field_name in self._field_config.get_field_names():
            metadata_key = self._field_config.get_metadata_key(field_name)
            current_value = str(self._data.get(metadata_key, ""))
            original_value = str(self._original_data.get(metadata_key, ""))
            
            if current_value != original_value:
                self._dirty_fields.add(field_name)
    
    def add_observer(self, observer) -> None:
        """
        Add an observer for change notifications.
        
        Args:
            observer: Object with methods to handle notifications
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer) -> None:
        """
        Remove an observer.
        
        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, event_type: str, *args) -> None:
        """
        Notify all observers of a change.
        
        Args:
            event_type: Type of event that occurred
            *args: Additional event arguments
        """
        for observer in self._observers:
            method_name = f'on_{event_type}'
            if hasattr(observer, method_name):
                try:
                    method = getattr(observer, method_name)
                    method(*args)
                except Exception as e:
                    logger.error(f"Error notifying observer {observer}: {e}")
    
    def clear(self) -> None:
        """Clear all metadata."""
        self._data.clear()
        self._original_data.clear()
        self._dirty_fields.clear()
        self._history.clear()
        self._history_index = -1
        self._notify_observers('metadata_cleared')
    
    def __len__(self) -> int:
        """Get number of metadata fields."""
        return len(self._data)
    
    def __contains__(self, key: str) -> bool:
        """Check if metadata contains a key."""
        return key in self._data
    
    def __str__(self) -> str:
        """String representation of metadata model."""
        return f"MetadataModel({len(self._data)} fields, dirty={self.is_dirty()})"
