"""
Main Controller
===============

This module defines the `MainController`, the central component of the application
that orchestrates the interactions between the Model and the View.
"""

from PySide6.QtCore import QObject, Slot, QDateTime, Qt, QThread
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog
from ..models.metadata_model import MetadataModel
from ..views.main_view import MainView
from ..services.safetensor_service import SafetensorService
from ..workers.save_worker import SaveWorker

class MainController(QObject):
    """
    The main controller for the application.

    It connects the user interface (View) with the data model (Model) and
    handles the application's logic.
    """
    def __init__(self, model: MetadataModel, view: MainView):
        super().__init__()
        self._model = model
        self._view = view
        self._safetensor_service = SafetensorService()
        self._current_file = None
        self.thread = None
        self.worker = None

        # Register the controller's update method as an observer of the model.
        self._model.add_observer(self.update_view)

        # Connect the view's signals to the controller's slots.
        self._connect_signals()

    def _connect_signals(self):
        """Connects signals from the view to the controller's slots."""
        self._view.open_file_requested.connect(self.on_open_file_requested)
        self._view.save_requested.connect(self.on_save_requested)
        self._view.exit_requested.connect(self.on_exit_requested)

        # Connect metadata field changes
        self._view.title_changed.connect(lambda t: self._model.set_value('modelspec.title', t))
        self._view.description_changed.connect(lambda d: self._model.set_value('modelspec.description', d))
        self._view.author_changed.connect(lambda a: self._model.set_value('modelspec.author', a))
        self._view.datetime_changed.connect(self.on_datetime_changed)
        self._view.license_changed.connect(lambda l: self._model.set_value('modelspec.license', l))
        self._view.usage_hint_changed.connect(lambda h: self._model.set_value('modelspec.usage_hint', h))
        self._view.tags_changed.connect(lambda t: self._model.set_value('modelspec.tags', t))
        self._view.merged_from_changed.connect(lambda m: self._model.set_value('modelspec.merged_from', m))

        # Connect thumbnail actions
        self._view.set_thumbnail_requested.connect(self.on_set_thumbnail_requested)
        self._view.clear_thumbnail_requested.connect(self.on_clear_thumbnail_requested)
        self._view.view_thumbnail_requested.connect(self.on_view_thumbnail_requested)

    def run(self):
        """Shows the main window and starts the application."""
        self._view.show()
        self.update_view() # Initial view update
        self._view.set_all_fields_enabled(False)
        self._view.set_status_message("Ready. Please open a safetensors file to begin.")

    @Slot()
    def on_open_file_requested(self):
        """Handles the open file request from the view."""
        filepath, _ = QFileDialog.getOpenFileName(
            self._view,
            "Open Safetensors File",
            "",
            "Safetensors Files (*.safetensors);;All Files (*)"
        )
        if filepath:
            self._current_file = filepath
            try:
                self._view.set_status_message(f"Reading metadata from {filepath}...")
                metadata = self._safetensor_service.read_metadata(filepath)
                self._model.load_data(metadata)
                self._view.set_status_message(f"Loaded file: {filepath}", 5000)
            except Exception as e:
                self._view.set_status_message(f"Error loading file: {e}")
                self._current_file = None
                self._model.load_data({}) # Clear model on error

    @Slot()
    def on_set_thumbnail_requested(self):
        """Handles the request to set a new thumbnail image."""
        filepath, _ = QFileDialog.getOpenFileName(
            self._view,
            "Select Thumbnail Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if filepath:
            try:
                data_uri = self._safetensor_service.image_to_data_uri(filepath)
                self._model.set_value('modelspec.thumbnail', data_uri)
                self._view.set_status_message("Thumbnail set.", 3000)
            except Exception as e:
                self._view.set_status_message(f"Error setting thumbnail: {e}")

    @Slot()
    def on_clear_thumbnail_requested(self):
        """Handles the request to clear the thumbnail."""
        self._model.set_value('modelspec.thumbnail', '')
        self._view.set_status_message("Thumbnail cleared.", 3000)

    @Slot()
    def on_view_thumbnail_requested(self):
        """Handles the request to view the thumbnail."""
        # TODO: Implement a proper image viewer window
        self._view.set_status_message("View thumbnail not implemented yet.")
        print("View thumbnail requested.")

    @Slot()
    def on_save_requested(self):
        """
        Handles the save request from the view by setting up and starting
        a background worker thread.
        """
        if not self._current_file:
            self._view.set_status_message("Please open a file first.")
            return

        if not self._model.is_dirty():
            self._view.set_status_message("No changes to save.")
            return

        # Disable UI elements during save
        self._view.set_all_fields_enabled(False)
        self._view.ui.progressBar.setValue(0)
        self._view.set_status_message(f"Saving {self._current_file}...")

        # --- Setup and run the background worker ---
        self.thread = QThread()
        self.worker = SaveWorker(
            service=self._safetensor_service,
            filepath=self._current_file,
            metadata=self._model.get_all_data()
        )
        self.worker.moveToThread(self.thread)

        # Connect worker signals to controller slots
        self.worker.progress.connect(self.on_save_progress)
        self.worker.finished.connect(self.on_save_finished)
        self.worker.error.connect(self.on_save_error)

        # Connect thread signals
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)

        # Start the thread
        self.thread.start()

    @Slot(int)
    def on_save_progress(self, value: int):
        """Updates the progress bar."""
        self._view.ui.progressBar.setValue(value)

    @Slot(str)
    def on_save_finished(self, filepath: str):
        """Handles successful save completion."""
        self._view.set_status_message(f"Successfully saved to {filepath}", 5000)
        self._model.mark_saved()
        self._view.set_all_fields_enabled(True)
        self.cleanup_thread()

    @Slot(str)
    def on_save_error(self, error_message: str):
        """Handles save errors."""
        self._view.set_status_message(f"Save failed: {error_message}")
        self._view.set_all_fields_enabled(True)
        self.cleanup_thread()

    def cleanup_thread(self):
        """Cleans up the thread and worker objects."""
        self.thread = None
        self.worker = None

    @Slot()
    def on_exit_requested(self):
        """Handles the exit request from the view."""
        # TODO: Check for unsaved changes before exiting
        self._view.close()

    @Slot(QDateTime)
    def on_datetime_changed(self, dt: QDateTime):
        """Handles the datetime change signal."""
        # Convert QDateTime to a string format for the model, e.g., ISO 8601
        self._model.set_value('modelspec.date', dt.toString(Qt.ISODateWithMs))

    def update_view(self):
        """
        Updates the view with the current state of the model.
        This method is called whenever the model changes.
        """
        is_dirty = self._model.is_dirty()
        title = "Metadata Editor"
        if self._current_file:
            title += f" - {self._current_file}"
        if is_dirty:
            title += " *" # Add an asterisk to indicate unsaved changes

        self._view.set_window_title(title)

        # Update the input fields by iterating through the view's widget map
        # and translating the keys for the model.
        for view_key, _ in self._view._widget_map.items():
            model_key = f"modelspec.{view_key}"
            if view_key == 'datetime': # Handle the key name change
                model_key = "modelspec.date"

            value = self._model.get_value(model_key)
            self._view.set_field_value(view_key, value)

        # Update the thumbnail
        thumbnail_data_uri = self._model.get_value('modelspec.thumbnail')
        pixmap = self._safetensor_service.data_uri_to_pixmap(thumbnail_data_uri)
        self._view.set_thumbnail_pixmap(pixmap)

        # Enable fields only if a file is loaded
        self._view.set_all_fields_enabled(self._current_file is not None)

