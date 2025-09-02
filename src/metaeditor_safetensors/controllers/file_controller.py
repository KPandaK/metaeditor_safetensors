"""
File Controller - handles file operations and management.
"""

import logging
from typing import Optional
from safetensors import read_safetensors_metadata
from models import FileModel, MetadataModel

logger = logging.getLogger(__name__)


class FileController:
    """
    Controller for file operations.
    
    Handles:
    - File selection and validation
    - Loading metadata from files
    - File state management
    """
    
    def __init__(self, file_model: FileModel, metadata_model: MetadataModel):
        """
        Initialize file controller.
        
        Args:
            file_model: FileModel instance
            metadata_model: MetadataModel instance
        """
        self.file_model = file_model
        self.metadata_model = metadata_model
        
        # Observers for notifications
        self._observers = []
    
    def open_file(self, filepath: str) -> bool:
        """
        Open a safetensors file.
        
        Args:
            filepath: Path to the file to open
            
        Returns:
            True if file was opened successfully
        """
        try:
            # Update file model
            self.file_model.set_filepath(filepath)
            
            if not self.file_model.is_valid:
                self._notify_observers('file_invalid', filepath, "File is not a valid safetensors file")
                return False
            
            # Notify observers
            self._notify_observers('file_opened', filepath)
            
            logger.info(f"Opened file: {filepath}")
            return True
            
        except Exception as e:
            error_msg = f"Error opening file: {str(e)}"
            logger.error(error_msg)
            self._notify_observers('file_error', filepath, error_msg)
            return False
    
    def load_metadata(self) -> bool:
        """
        Load metadata from the current file.
        
        Returns:
            True if metadata was loaded successfully
        """
        if not self.file_model.filepath:
            self._notify_observers('load_error', "No file selected")
            return False
        
        if not self.file_model.is_valid:
            self._notify_observers('load_error', "File is not valid")
            return False
        
        try:
            self._notify_observers('load_started')
            
            # Read metadata from file
            metadata = read_safetensors_metadata(self.file_model.filepath)
            
            # Update metadata model
            self.metadata_model.load_metadata(metadata)
            
            self._notify_observers('load_completed', metadata)
            
            logger.info(f"Loaded metadata from: {self.file_model.filepath}")
            return True
            
        except Exception as e:
            error_msg = f"Error loading metadata: {str(e)}"
            logger.error(error_msg)
            self._notify_observers('load_error', error_msg)
            return False
    
    def close_file(self) -> None:
        """Close the current file."""
        if self.file_model.filepath:
            logger.info(f"Closing file: {self.file_model.filepath}")
        
        # Clear models
        self.file_model.set_filepath(None)
        self.metadata_model.clear()
        
        self._notify_observers('file_closed')
    
    def reload_file_info(self) -> None:
        """Reload file information from filesystem."""
        self.file_model.reload()
        self._notify_observers('file_info_updated')
    
    def get_file_info(self) -> dict:
        """
        Get information about the current file.
        
        Returns:
            Dictionary containing file information
        """
        return {
            'filepath': self.file_model.filepath,
            'filename': self.file_model.filename,
            'file_size': self.file_model.file_size,
            'file_size_mb': self.file_model.file_size_mb,
            'last_modified': self.file_model.last_modified,
            'is_valid': self.file_model.is_valid,
            'exists': self.file_model.exists
        }
    
    def add_observer(self, observer) -> None:
        """
        Add an observer for file events.
        
        Args:
            observer: Object with methods to handle file events
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
            method_name = f'on_file_{event_type}'
            if hasattr(observer, method_name):
                try:
                    method = getattr(observer, method_name)
                    method(*args)
                except Exception as e:
                    logger.error(f"Error notifying observer {observer}: {e}")
    
    @property
    def has_file(self) -> bool:
        """Check if a file is currently loaded."""
        return self.file_model.filepath is not None
    
    @property
    def current_filepath(self) -> Optional[str]:
        """Get the current file path."""
        return self.file_model.filepath
