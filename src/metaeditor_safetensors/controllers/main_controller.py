"""
Main Controller - coordinates the entire application.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import QMessageBox

from models import FileModel, MetadataModel, FieldConfiguration
from views import MainView, MetadataView
from .file_controller import FileController
from .metadata_controller import MetadataController
from commands import SaveCommand

logger = logging.getLogger(__name__)


class MainController:
    """
    Main application controller that coordinates all components.
    
    This controller:
    - Initializes all MVC components
    - Handles communication between components
    - Manages application lifecycle
    - Coordinates complex operations
    """
    
    def __init__(self, app):
        """Initialize the main controller and all MVC components."""
        self.app = app
        
        # Initialize models
        self.field_config = FieldConfiguration()
        self.file_model = FileModel()
        self.metadata_model = MetadataModel(self.field_config)
        
        # Initialize controllers
        self.file_controller = FileController(self.file_model, self.metadata_model)
        self.metadata_controller = MetadataController(self.metadata_model, self.field_config)
        
        # Views will be initialized when show() is called
        self.main_view = None
        self.metadata_view = None
        
        logger.info("Main controller initialized")
    
    def _setup_connections(self) -> None:
        """Set up connections between components."""
        # Connect main view signals to controller methods
        self.main_view.file_opened.connect(self._on_file_opened)
        self.main_view.metadata_load_requested.connect(self._on_load_metadata_requested)
        self.main_view.save_requested.connect(self._on_save_requested)
        self.main_view.thumbnail_set_requested.connect(self._on_set_thumbnail_requested)
        self.main_view.thumbnail_view_requested.connect(self._on_view_thumbnail_requested)
        self.main_view.raw_view_requested.connect(self._on_raw_view_requested)
        self.main_view.about_requested.connect(self._on_about_requested)
        self.main_view.exit_requested.connect(self._on_exit_requested)
        
        # Connect metadata view signals
        self.metadata_view.field_changed.connect(self._on_field_changed)
        
        # Connect thumbnail widget signals if it exists
        thumbnail_widget = self.metadata_view.get_thumbnail_widget()
        if thumbnail_widget:
            thumbnail_widget.set_thumbnail_requested.connect(self._on_set_thumbnail_requested)
            thumbnail_widget.view_thumbnail_requested.connect(self._on_view_thumbnail_requested)
            thumbnail_widget.clear_thumbnail_requested.connect(self._on_clear_thumbnail_requested)
        
        # Set up controller observers
        self.file_controller.add_observer(self)
        self.metadata_controller.add_observer(self)
    
    def show(self):
        """Initialize and show the application views."""
        # Initialize views (must be done after QApplication is created)
        self.main_view = MainView()
        self.metadata_view = MetadataView(self.field_config)
        
        # Connect views
        self.main_view.set_metadata_view(self.metadata_view)
        
        # Set up observers and connections
        self._setup_connections()
        
        # Show the main window
        self.main_view.show()
        self.main_view.add_status_message("Application started. Select a file to begin.")
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Application exit code
        """
        self.show()
        return self.app.exec()
    
    # File operation handlers
    def _on_file_opened(self, filepath: str) -> None:
        """Handle file opened signal from view."""
        logger.info(f"Opening file: {filepath}")
        self.main_view.add_status_message(f"Opening file: {filepath}")
        
        if self.file_controller.open_file(filepath):
            # Automatically load metadata when file is opened
            self.file_controller.load_metadata()
        
    def _on_load_metadata_requested(self) -> None:
        """Handle load metadata request from view."""
        if not self.file_controller.has_file:
            self.main_view.show_warning("Warning", "Please select a file first.")
            return
        
        self.main_view.add_status_message("Loading metadata...")
        self.file_controller.load_metadata()
    
    def _on_save_requested(self) -> None:
        """Handle save request from view."""
        if not self.file_controller.has_file:
            self.main_view.show_warning("Warning", "Please select a file first.")
            return
        
        # Validate all fields first
        is_valid, errors = self.metadata_controller.validate_all_fields()
        if not is_valid:
            error_msg = "Please fix the following issues:\\n\\n"
            for field, field_errors in errors.items():
                for error in field_errors:
                    error_msg += f"• {error}\\n"
            self.main_view.show_error("Validation Error", error_msg)
            return
        
        # Get metadata for saving
        metadata = self.metadata_controller.get_metadata_for_saving()
        filepath = self.file_controller.current_filepath
        
        try:
            self.main_view.add_status_message("Saving changes...")
            
            # Use existing SaveCommand but with callback
            command = SaveCommand(
                editor=None,  # We don't need the editor reference in the new architecture
                filepath=filepath,
                metadata=metadata,
                completion_callback=self._on_save_completed
            )
            command.execute()
            
        except Exception as e:
            error_msg = f"Error saving changes: {str(e)}"
            self.main_view.show_error("Save Error", error_msg)
            logger.error(error_msg)
    
    def _on_save_completed(self, success: bool, filepath_or_error) -> None:
        """Handle save completion."""
        if success:
            self.main_view.add_status_message("Changes saved successfully!")
            self.metadata_controller.mark_saved()
            logger.info("Changes saved successfully")
        else:
            error_msg = f"Error saving changes: {str(filepath_or_error)}"
            self.main_view.show_error("Save Error", error_msg)
            logger.error(error_msg)
    
    # Metadata operation handlers
    def _on_field_changed(self, field_name: str, value: str) -> None:
        """Handle field change from metadata view."""
        self.metadata_controller.update_field(field_name, value)
    
    def _on_clear_thumbnail_requested(self) -> None:
        """Handle clear thumbnail request."""
        self.metadata_controller.update_field('thumbnail', '')
        self.main_view.add_status_message("Thumbnail cleared")
    
    # UI operation handlers
    def _on_set_thumbnail_requested(self) -> None:
        """Handle set thumbnail request."""
        # TODO: Implement thumbnail setting functionality
        self.main_view.show_info("Info", "Set thumbnail functionality not implemented yet.")
    
    def _on_view_thumbnail_requested(self) -> None:
        """Handle view thumbnail request."""
        # TODO: Implement thumbnail viewer
        self.main_view.show_info("Info", "Thumbnail viewer not implemented yet.")
    
    def _on_raw_view_requested(self) -> None:
        """Handle raw view request."""
        # TODO: Implement raw metadata editor
        self.main_view.show_info("Info", "Raw metadata editor not implemented yet.")
    
    def _on_about_requested(self) -> None:
        """Handle about dialog request."""
        # TODO: Implement about dialog
        self.main_view.show_info("About", "Safetensors Metadata Editor\\nMVC Architecture Version")
    
    def _on_exit_requested(self) -> None:
        """Handle exit request."""
        # Check for unsaved changes
        if self.metadata_controller.is_dirty():
            if self.main_view.ask_question(
                "Unsaved Changes", 
                "You have unsaved changes. Are you sure you want to exit?"
            ):
                self.app.quit()
        else:
            self.app.quit()
    
    # Observer methods for FileController
    def on_file_opened(self, filepath: str) -> None:
        """Handle file opened event."""
        self.main_view.update_file_display(filepath)
        file_info = self.file_controller.get_file_info()
        self.main_view.add_status_message(
            f"File opened: {file_info['filename']} ({file_info['file_size_mb']:.1f} MB)"
        )
    
    def on_file_closed(self) -> None:
        """Handle file closed event."""
        self.main_view.update_file_display(None)
        self.main_view.set_modified(False)
        self.metadata_view.clear_all_fields()
        self.main_view.add_status_message("File closed")
    
    def on_file_invalid(self, filepath: str, error: str) -> None:
        """Handle invalid file event."""
        self.main_view.show_error("Invalid File", f"The selected file is not a valid safetensors file:\\n{error}")
    
    def on_file_error(self, filepath: str, error: str) -> None:
        """Handle file error event."""
        self.main_view.show_error("File Error", f"Error with file {filepath}:\\n{error}")
    
    def on_file_load_started(self) -> None:
        """Handle load started event."""
        self.main_view.add_status_message("Loading metadata...")
        self.metadata_view.set_all_fields_enabled(False)
    
    def on_file_load_completed(self, metadata: dict) -> None:
        """Handle load completed event."""
        self.main_view.add_status_message(f"Metadata loaded ({len(metadata)} fields)")
        self.metadata_view.set_all_fields_enabled(True)
        
        # Update view with loaded data
        self._update_view_from_metadata()
    
    def on_file_load_error(self, error: str) -> None:
        """Handle load error event."""
        self.main_view.show_error("Load Error", f"Error loading metadata:\\n{error}")
        self.metadata_view.set_all_fields_enabled(True)
    
    # Observer methods for MetadataController
    def on_metadata_field_updated(self, field_name: str, value: str) -> None:
        """Handle field updated event."""
        self.main_view.set_modified(self.metadata_controller.is_dirty())
    
    def on_metadata_field_validation_failed(self, field_name: str, errors: list[str]) -> None:
        """Handle field validation failed event."""
        self.metadata_view.highlight_field_error(field_name, True)
        error_msg = "\\n".join(errors)
        self.main_view.add_status_message(f"Validation error in {field_name}: {error_msg}")
    
    def on_metadata_saved(self) -> None:
        """Handle metadata saved event."""
        self.main_view.set_modified(False)
    
    def on_metadata_loaded(self) -> None:
        """Handle metadata loaded event."""
        self._update_view_from_metadata()
        self.main_view.set_modified(False)
    
    def on_metadata_reset(self) -> None:
        """Handle metadata reset event."""
        self._update_view_from_metadata()
        self.main_view.set_modified(False)
        self.main_view.add_status_message("Metadata reset to original values")
    
    def _update_view_from_metadata(self) -> None:
        """Update the metadata view with current model data."""
        field_values = self.metadata_controller.get_all_field_values()
        for field_name, value in field_values.items():
            self.metadata_view.set_field_value(field_name, value)
    
    def get_main_view(self) -> MainView:
        """Get the main view instance."""
        return self.main_view
