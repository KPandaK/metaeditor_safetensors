"""
Metadata Controller - handles metadata operations and validation.
"""

import logging
from typing import Dict, Any, Optional
from models import MetadataModel, FieldConfiguration

logger = logging.getLogger(__name__)


class MetadataController:
    """
    Controller for metadata operations.
    
    Handles:
    - Metadata validation
    - Field value management
    - Change tracking
    - Undo/redo operations
    """
    
    def __init__(self, metadata_model: MetadataModel, field_config: FieldConfiguration):
        """
        Initialize metadata controller.
        
        Args:
            metadata_model: MetadataModel instance
            field_config: FieldConfiguration instance
        """
        self.metadata_model = metadata_model
        self.field_config = field_config
        
        # Observers for notifications
        self._observers = []
        
        # Register as observer of metadata model
        self.metadata_model.add_observer(self)
    
    def update_field(self, field_name: str, value: str) -> bool:
        """
        Update a metadata field value.
        
        Args:
            field_name: Name of the field
            value: New value for the field
            
        Returns:
            True if update was successful
        """
        try:
            # Validate the new value
            is_valid, errors = self.field_config.validate_field_value(field_name, value)
            
            if not is_valid:
                self._notify_observers('field_validation_failed', field_name, errors)
                return False
            
            # Update the model
            self.metadata_model.set_field_value(field_name, value)
            
            self._notify_observers('field_updated', field_name, value)
            return True
            
        except Exception as e:
            logger.error(f"Error updating field {field_name}: {e}")
            self._notify_observers('field_update_error', field_name, str(e))
            return False
    
    def get_field_value(self, field_name: str) -> str:
        """
        Get the current value of a field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Current field value
        """
        return self.metadata_model.get_field_value(field_name)
    
    def validate_all_fields(self) -> tuple[bool, Dict[str, list[str]]]:
        """
        Validate all metadata fields.
        
        Returns:
            Tuple of (is_valid, dict_of_field_errors)
        """
        return self.metadata_model.validate_all_fields()
    
    def validate_field(self, field_name: str) -> tuple[bool, list[str]]:
        """
        Validate a single field.
        
        Args:
            field_name: Name of the field to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        return self.metadata_model.validate_field(field_name)
    
    def get_all_field_values(self) -> Dict[str, str]:
        """
        Get all field values as a dictionary.
        
        Returns:
            Dictionary mapping field names to values
        """
        result = {}
        for field_name in self.field_config.get_field_names():
            result[field_name] = self.get_field_value(field_name)
        return result
    
    def set_all_field_values(self, values: Dict[str, str]) -> None:
        """
        Set multiple field values at once.
        
        Args:
            values: Dictionary mapping field names to values
        """
        for field_name, value in values.items():
            if field_name in self.field_config.get_field_names():
                self.metadata_model.set_field_value(field_name, value)
    
    def clear_all_fields(self) -> None:
        """Clear all metadata fields."""
        self.metadata_model.clear()
        self._notify_observers('all_fields_cleared')
    
    def reset_to_original(self) -> None:
        """Reset all changes back to original loaded state."""
        self.metadata_model.reset_to_original()
        self._notify_observers('metadata_reset')
    
    def mark_saved(self) -> None:
        """Mark metadata as saved (clean state)."""
        self.metadata_model.mark_clean()
        self._notify_observers('metadata_saved')
    
    def undo(self) -> bool:
        """
        Undo last change.
        
        Returns:
            True if undo was performed
        """
        if self.metadata_model.undo():
            self._notify_observers('metadata_undone')
            return True
        return False
    
    def redo(self) -> bool:
        """
        Redo last undone change.
        
        Returns:
            True if redo was performed
        """
        if self.metadata_model.redo():
            self._notify_observers('metadata_redone')
            return True
        return False
    
    def can_undo(self) -> bool:
        """Check if undo operation is possible."""
        return self.metadata_model.can_undo()
    
    def can_redo(self) -> bool:
        """Check if redo operation is possible."""
        return self.metadata_model.can_redo()
    
    def get_metadata_for_saving(self) -> Dict[str, Any]:
        """
        Get metadata formatted for saving to file.
        
        Returns:
            Dictionary containing metadata ready for file save
        """
        return self.metadata_model.get_all_metadata()
    
    def get_dirty_fields(self) -> set[str]:
        """
        Get set of fields that have been modified.
        
        Returns:
            Set of field names that have been changed
        """
        return self.metadata_model.get_dirty_fields()
    
    def is_dirty(self) -> bool:
        """
        Check if metadata has unsaved changes.
        
        Returns:
            True if there are unsaved changes
        """
        return self.metadata_model.is_dirty()
    
    # Observer methods for MetadataModel
    def on_metadata_loaded(self) -> None:
        """Handle metadata loaded event."""
        self._notify_observers('metadata_loaded')
    
    def on_field_changed(self, field_name: str, value: str) -> None:
        """Handle field changed event."""
        self._notify_observers('field_changed', field_name, value)
    
    def on_metadata_updated(self) -> None:
        """Handle metadata updated event."""
        self._notify_observers('metadata_updated')
    
    def on_metadata_saved(self) -> None:
        """Handle metadata saved event."""
        self._notify_observers('metadata_saved')
    
    def on_metadata_reset(self) -> None:
        """Handle metadata reset event."""
        self._notify_observers('metadata_reset')
    
    def on_metadata_undone(self) -> None:
        """Handle metadata undone event."""
        self._notify_observers('metadata_undone')
    
    def on_metadata_redone(self) -> None:
        """Handle metadata redone event."""
        self._notify_observers('metadata_redone')
    
    def on_metadata_cleared(self) -> None:
        """Handle metadata cleared event."""
        self._notify_observers('metadata_cleared')
    
    def add_observer(self, observer) -> None:
        """
        Add an observer for metadata events.
        
        Args:
            observer: Object with methods to handle metadata events
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
        Notify all observers of an event.
        
        Args:
            event_type: Type of event
            *args: Event arguments
        """
        for observer in self._observers:
            method_name = f'on_metadata_{event_type}'
            if hasattr(observer, method_name):
                try:
                    method = getattr(observer, method_name)
                    method(*args)
                except Exception as e:
                    logger.error(f"Error notifying observer {observer}: {e}")
