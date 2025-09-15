import os
from typing import List, Optional

from PySide6.QtCore import QDateTime, QObject, Qt, QThread, Slot
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog

from ..models.metadata_keys import MetadataKeys
from ..models.metadata_model import MetadataModel
from ..services.config_service import ConfigService
from ..services.image_service import ImageService
from ..services.safetensors_service import SafetensorsService
from ..services.save_worker import SaveWorker
from ..services.theme_service import ThemeService
from ..views.about_dialog import AboutDialog
from ..views.main_view import MainView
from ..views.settings_dialog import SettingsDialog
from ..views.thumbnail_dialog import ThumbnailDialog


class MainController(QObject):
    # Type annotations for instance attributes
    _thread: Optional[QThread]
    worker: Optional[SaveWorker]
    _current_file: Optional[str]

    def __init__(
        self,
        model: MetadataModel,
        view: MainView,
        config_service: ConfigService,
        safetensors_service: SafetensorsService,
        image_service: ImageService,
        theme_service: ThemeService,
    ):
        super().__init__()
        self._model = model
        self._view = view
        self._config_service = config_service
        self._safetensor_service = safetensors_service
        self._image_service = image_service
        self._theme_service = theme_service
        self._current_file = None
        self._thread = None
        self.worker = None

        # Register the controller's update method as an observer of the model.
        self._model.add_observer(self.update_view)

        # Register for recent files changes
        self._config_service.add_recent_files_observer(self._on_recent_files_changed)

        # Register for theme changes
        self._theme_service.add_theme_changed_observer(self._on_theme_changed)

        # Register for system theme changes
        self._theme_service.add_system_theme_changed_callback(
            self._on_system_theme_changed
        )

        # Connect the view's signals to the controller's slots.
        self._connect_signals()

        # Apply initial theme preference
        preferred_theme = config_service.get_theme_preference()
        self._theme_service.apply_theme(preferred_theme)

    def _connect_signals(self):
        self._view.open_file_requested.connect(self.on_open_file_requested)
        self._view.file_dropped.connect(self.on_file_dropped)
        self._view.save_requested.connect(self.on_save_requested)
        self._view.settings_requested.connect(self.on_settings_requested)
        self._view.about_requested.connect(self.on_about_requested)
        self._view.exit_requested.connect(self.on_exit_requested)

        # Connect recent files signals
        self._view.recent_file_triggered.connect(self.on_recent_file_triggered)
        self._view.clear_recent_requested.connect(self.on_clear_recent_requested)

        # Connect metadata field changes
        self._view.title_changed.connect(
            lambda t: self._model.set_value(MetadataKeys.TITLE, t)
        )
        self._view.description_changed.connect(
            lambda d: self._model.set_value(MetadataKeys.DESCRIPTION, d)
        )
        self._view.author_changed.connect(
            lambda a: self._model.set_value(MetadataKeys.AUTHOR, a)
        )
        self._view.datetime_changed.connect(self.on_datetime_changed)
        self._view.license_changed.connect(
            lambda license_value: self._model.set_value(
                MetadataKeys.LICENSE, license_value
            )
        )
        self._view.usage_hint_changed.connect(
            lambda h: self._model.set_value(MetadataKeys.USAGE_HINT, h)
        )
        self._view.tags_changed.connect(
            lambda t: self._model.set_value(MetadataKeys.TAGS, t)
        )
        self._view.merged_from_changed.connect(
            lambda m: self._model.set_value(MetadataKeys.MERGED_FROM, m)
        )

        # Connect thumbnail actions
        self._view.set_thumbnail_requested.connect(self.on_set_thumbnail_requested)
        self._view.clear_thumbnail_requested.connect(self.on_clear_thumbnail_requested)
        self._view.view_thumbnail_requested.connect(self.on_view_thumbnail_requested)

    def run(self):
        self._view.show()
        self.update_view()
        self._view.set_all_fields_enabled(False)
        self._view.set_status_message("Ready. Please open a safetensors file to begin.")

        self._on_recent_files_changed(self._config_service.get_recent_files())

    @Slot()
    def on_open_file_requested(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self._view,
            "Open Safetensors File",
            "",
            "Safetensors Files (*.safetensors);;All Files (*)",
        )
        if filepath:
            self._load_file(filepath)

    @Slot(str)
    def on_file_dropped(self, filepath: str):
        if filepath:
            self._load_file(filepath)

    def _load_file(self, filepath: str):
        self._current_file = filepath
        try:
            self._view.set_status_message(f"Reading metadata from {filepath}...")
            metadata = self._safetensor_service.read_metadata(filepath)
            self._model.load_data(metadata)
            self._view.set_status_message(f"Loaded file: {filepath}", 5000)

            # Add to recent files
            self._config_service.add_recent_file(filepath)

        except Exception as e:
            self._view.set_status_message(f"Error loading file: {e}")
            self._current_file = None
            self._model.load_data({})

    @Slot(str)
    def on_recent_file_triggered(self, filepath: str):
        # Check if file still exists
        if not os.path.exists(filepath):
            self._view.set_status_message(f"File no longer exists: {filepath}")
            # Remove from recent files list
            self._config_service.remove_recent_file(filepath)
            return

        self._load_file(filepath)

    @Slot()
    def on_clear_recent_requested(self):
        self._config_service.clear_recent_files()
        self._view.set_status_message("Recent files cleared.", 3000)

    def on_settings_requested(self):
        if not self._theme_service:
            self._view.set_status_message("Theme service not available", 3000)
            return

        # Create and configure settings dialog
        settings_dialog = SettingsDialog(self._view)
        settings_dialog.set_services(self._theme_service, self._config_service)

        # Connect settings dialog signals
        settings_dialog.theme_changed.connect(self._on_settings_theme_changed)

        # Show dialog
        result = settings_dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            self._view.set_status_message("Settings saved successfully", 2000)

    def on_about_requested(self):
        if not self._theme_service:
            self._view.set_status_message("Theme service not available", 3000)
            return

        # Create and configure about dialog
        about_dialog = AboutDialog(self._theme_service, self._view)

        # Show dialog
        about_dialog.exec()

    def _on_settings_theme_changed(self, theme_id: str):
        success = self._theme_service.apply_theme(theme_id)
        if success:
            self._view.set_status_message(f"Theme changed to: {theme_id}", 2000)

    def _on_recent_files_changed(self, recent_files: List[str]):
        self._view.update_recent_files_menu(recent_files)

    def _on_theme_changed(self, theme):
        self._config_service.set_theme_preference(theme.config.theme_id)

    def _on_system_theme_changed(self, system_theme: str):
        """Handle system theme change events."""
        # Check if user preference is set to "system"
        current_preference = self._config_service.get_theme_preference()
        if current_preference == "system":
            # Apply the system theme
            success = self._theme_service.apply_theme("system")
            if success:
                self._view.set_status_message(
                    f"System theme changed to: {system_theme}", 2000
                )

    @Slot()
    def on_set_thumbnail_requested(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self._view,
            "Select Thumbnail Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif *.webp *.svg *.ico);;All Files (*)",
        )
        if filepath:
            try:
                data_uri = self._image_service.image_to_data_uri(filepath)
                self._model.set_value(MetadataKeys.THUMBNAIL, data_uri)
                self._view.set_status_message("Thumbnail set.", 3000)
            except Exception as e:
                self._view.set_status_message(f"Error setting thumbnail: {e}")

    @Slot()
    def on_clear_thumbnail_requested(self):
        self._model.set_value(MetadataKeys.THUMBNAIL, "")
        self._view.set_status_message("Thumbnail cleared.", 3000)

    @Slot()
    def on_view_thumbnail_requested(self):
        thumbnail_data_uri = self._model.get_value(MetadataKeys.THUMBNAIL)
        if thumbnail_data_uri:
            pixmap = self._image_service.data_uri_to_pixmap(thumbnail_data_uri)
            if pixmap and not pixmap.isNull():
                dialog = ThumbnailDialog(pixmap, self._view)

                # TODO: This feels like it should be part of a window positioning service
                # Center the dialog over the main window
                main_window_geometry = self._view.geometry()
                dialog_geometry = dialog.geometry()
                x = int(
                    main_window_geometry.x()
                    + (main_window_geometry.width() - dialog_geometry.width()) / 2
                )
                y = int(
                    main_window_geometry.y()
                    + (main_window_geometry.height() - dialog_geometry.height()) / 2
                )

                # Ensure the dialog is not off-screen
                screen_geometry = QApplication.primaryScreen().availableGeometry()
                if x < screen_geometry.x():
                    x = screen_geometry.x()
                if y < screen_geometry.y():
                    y = screen_geometry.y()
                if x + dialog_geometry.width() > screen_geometry.right():
                    x = screen_geometry.right() - dialog_geometry.width()
                if y + dialog_geometry.height() > screen_geometry.bottom():
                    y = screen_geometry.bottom() - dialog_geometry.height()

                dialog.move(int(x), int(y))
                dialog.exec()
            else:
                self._view.set_status_message("Invalid or empty thumbnail image.")
        else:
            self._view.set_status_message("No thumbnail to view.")

    @Slot()
    def on_save_requested(self):
        if not self._current_file:
            self._view.set_status_message("Please open a file first.")
            return

        if not self._model.is_dirty():
            self._view.set_status_message("No changes to save.")
            return

        # Prevent multiple save operations
        if self._thread and self._thread.isRunning():
            self._view.set_status_message("Save operation already in progress.")
            return

        # Disable UI elements during save
        self._view.set_all_fields_enabled(False)
        self._view.show_progress_bar()
        self._view.set_status_message(f"Saving {self._current_file}...")

        # --- Setup and run the background worker ---
        self._thread = QThread()
        self.worker = SaveWorker(
            service=self._safetensor_service,
            filepath=self._current_file,
            metadata=self._model.get_all_data(),
        )
        self.worker.moveToThread(self._thread)

        # Connect worker signals to controller slots
        self.worker.progress.connect(self.on_save_progress)
        self.worker.finished.connect(self.on_save_finished)
        self.worker.error.connect(self.on_save_error)

        # Connect thread signals
        self._thread.started.connect(self.worker.run)
        self._thread.finished.connect(self._thread.deleteLater)
        self.worker.finished.connect(self._thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self._thread.quit)
        self.worker.error.connect(self.worker.deleteLater)

        # Start the thread
        self._thread.start()

    @Slot(int)
    def on_save_progress(self, value: int):
        self._view.set_progress_value(value)

    @Slot(str)
    def on_save_finished(self, filepath: str):
        self._view.set_status_message(f"Successfully saved to {filepath}", 5000)
        self._model.mark_saved()
        self._view.set_all_fields_enabled(True)
        self._view.hide_progress_bar()
        self.cleanup_thread()

    @Slot(str)
    def on_save_error(self, error_message: str):
        self._view.set_status_message(f"Save failed: {error_message}")
        self._view.set_all_fields_enabled(True)
        self._view.hide_progress_bar()
        self.cleanup_thread()

    def cleanup_thread(self):
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            # Wait for thread to finish with a 5-second timeout
            if not self._thread.wait(5000):  # 5000ms = 5 seconds
                # Thread didn't finish gracefully, force terminate
                self._thread.terminate()
                # Give it a short time to terminate, then proceed
                self._thread.wait(1000)  # 1 second timeout for terminate
        self._thread = None
        self.worker = None

    def shutdown(self):
        self.cleanup_thread()
        self._config_service.remove_recent_files_observer(self._on_recent_files_changed)
        self._theme_service.remove_theme_changed_observer(self._on_theme_changed)

    @Slot()
    def on_exit_requested(self):
        # TODO: Check for unsaved changes before exiting
        self.shutdown()
        self._view.close()

    @Slot(QDateTime)
    def on_datetime_changed(self, dt: QDateTime):
        # Convert QDateTime to a string format for the model, e.g., ISO 8601
        self._model.set_value(
            MetadataKeys.DATE, dt.toString(Qt.DateFormat.ISODateWithMs)
        )

    def update_view(self):
        is_dirty = self._model.is_dirty()
        title = ""
        if self._current_file:
            filename = os.path.basename(self._current_file)
            title += f"{filename}"
        if is_dirty:
            title += " *"  # Add an asterisk to indicate unsaved changes

        self._view.set_window_title(title)

        # Get all data from the model and update the view
        all_data = self._model.get_all_data()
        self._view.update_all_fields(all_data)

        # Update the thumbnail
        thumbnail_data_uri = self._model.get_value(MetadataKeys.THUMBNAIL)
        thumbnail_pixmap = self._image_service.data_uri_to_pixmap(thumbnail_data_uri)
        self._view.set_thumbnail_pixmap(thumbnail_pixmap)

        # Enable fields only if a file is loaded
        self._view.set_all_fields_enabled(self._current_file is not None)
