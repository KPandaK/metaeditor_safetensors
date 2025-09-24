import logging
import os
from typing import List, Optional

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog

from ..models.metadata import ChangeSource, Metadata
from ..models.modelspec import ModelSpec
from ..services.config_service import ConfigService
from ..services.modelspec_service import ModelSpecService
from ..services.safetensors_service import SafetensorsService
from ..services.theme_service import ThemeService
from ..services.utility import (
    data_uri_to_pixmap,
    filepath_to_data_uri,
)
from ..services.widget_binding_service import WidgetBindingService
from ..views.about_dialog import AboutDialog
from ..views.main_view import MainView
from ..views.settings_dialog import SettingsDialog
from ..views.thumbnail_dialog import ThumbnailDialog

logger = logging.getLogger(__name__)


class MainController(QObject):
    # Type annotations for instance attributes
    _current_file: Optional[str]

    def __init__(
        self,
        model: Metadata,
        view: MainView,
        config_service: ConfigService,
        safetensors_service: SafetensorsService,
        theme_service: ThemeService,
        modelspec_service: ModelSpecService,
    ):
        super().__init__()
        self._model = model
        self._view = view
        self._config_service = config_service
        self._safetensor_service = safetensors_service
        self._theme_service = theme_service
        self._modelspec_service = modelspec_service
        self._current_file = None

        # Register for recent files changes
        self._config_service.add_recent_files_observer(self._on_recent_files_changed)

        # Register for theme changes
        self._theme_service.add_theme_changed_observer(self._on_theme_changed)

        # Register for metadata changes to update UI
        self._model.add_observer(self._on_metadata_changed)

        # Connect the view's signals to the controller's slots.
        self._connect_signals()

        # Apply initial theme preference
        preferred_theme = config_service.get_theme_preference()
        self._theme_service.apply_theme(preferred_theme)

    def _connect_signals(self):
        self._view.open_file_requested.connect(self.on_open_file_requested)
        self._view.file_dropped.connect(self.on_file_dropped)
        self._view.save_requested.connect(self.on_save_requested)
        self._view.save_as_requested.connect(self.on_save_as_requested)
        self._view.settings_requested.connect(self.on_settings_requested)
        self._view.about_requested.connect(self.on_about_requested)
        self._view.exit_requested.connect(self.on_exit_requested)

        # Connect recent files signals
        self._view.recent_file_triggered.connect(self.on_recent_file_triggered)
        self._view.clear_recent_requested.connect(self.on_clear_recent_requested)

        # Connect thumbnail actions
        self._view.set_thumbnail_requested.connect(self.on_set_thumbnail_requested)
        self._view.clear_thumbnail_requested.connect(self.on_clear_thumbnail_requested)
        self._view.view_thumbnail_requested.connect(self.on_view_thumbnail_requested)

        # Connect ModelSpec status widget
        self._view.modelspec_status_clicked.connect(self.on_modelspec_status_clicked)

    def run(self):
        self._view.show()
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

            self.update_view()
            self._view.set_status_message(f"Loaded file: {filepath}", 5000)

            # Add to recent files
            self._config_service.add_recent_file(filepath)

        except Exception as e:
            self._view.set_status_message(f"Error loading file: {e}")
            self._current_file = None
            self._model.load_data({})
            self.update_view()

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

    def _on_metadata_changed(
        self, field=None, source=ChangeSource.PROGRAMMATIC, source_widget=None
    ):
        self._update_window_title()

        # Update widgets based on change source and field
        binding_service = WidgetBindingService()

        if field is not None:
            if source == ChangeSource.USER and source_widget is not None:
                # User change - update other widgets for the same field, excluding source widget
                binding_service.update_widget_from_metadata(
                    field, exclude_widget=source_widget
                )
            elif source == ChangeSource.PROGRAMMATIC:
                # Programmatic change - update all widgets for this field (no exclusion needed)
                binding_service.update_widget_from_metadata(field)

        # Update ModelSpec status whenever metadata changes
        self._update_modelspec_status()

    def _update_window_title(self):
        is_dirty = self._model.is_dirty()
        title = ""

        if self._current_file:
            filename = os.path.basename(self._current_file)
            title += f"{filename}"

        # Show dirty indicator if there are unsaved changes
        if is_dirty:
            title += " *"  # Add an asterisk to indicate unsaved changes

        self._view.set_window_title(title)

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
                self._model.set_value(
                    "modelspec.thumbnail",
                    filepath_to_data_uri(filepath),
                    source=ChangeSource.PROGRAMMATIC,
                )

                self._view.set_status_message("Thumbnail set.", 3000)
            except Exception as e:
                self._view.set_status_message(f"Error setting thumbnail: {e}")

    @Slot()
    def on_clear_thumbnail_requested(self):
        self._model.set_value(
            "modelspec.thumbnail", "", source=ChangeSource.PROGRAMMATIC
        )

        self._view.set_status_message("Thumbnail cleared.", 3000)

    @Slot()
    def on_view_thumbnail_requested(self):
        data_uri = self._model.get_value("modelspec.thumbnail")
        if data_uri:
            pixmap = data_uri_to_pixmap(data_uri)
            if pixmap and not pixmap.isNull():
                dialog = ThumbnailDialog(pixmap, self._view)

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
        if self._safetensor_service.is_saving():
            self._view.set_status_message("Save operation already in progress.")
            return

        # Disable UI elements during save
        self._view.set_all_fields_enabled(False)
        self._view.show_progress_bar()
        self._view.set_status_message(f"Saving {self._current_file}...")

        # Start async save operation
        success = self._safetensor_service.write_metadata_async(
            filepath=self._current_file,
            metadata=self._model.get_all_data(),
            progress_callback=self._on_save_progress,
            success_callback=self._on_save_success,
            error_callback=self._on_save_error,
        )

        if not success:
            self._view.set_status_message("Save operation already in progress.")
            self._view.set_all_fields_enabled(True)
            self._view.hide_progress_bar()

    @Slot()
    def on_save_as_requested(self):
        if not self._model.get_all_data():
            self._view.set_status_message("Please open a file first.")
            return

        # Get the directory of current file (if any) for initial dialog location
        initial_dir = ""
        if self._current_file:
            initial_dir = os.path.dirname(self._current_file)

        # Show save file dialog
        filepath, _ = QFileDialog.getSaveFileName(
            self._view,
            "Save As",
            initial_dir,
            "Safetensors Files (*.safetensors);;All Files (*)",
        )

        if not filepath:
            return  # User cancelled dialog

        # Ensure file has .safetensors extension
        if not filepath.lower().endswith(".safetensors"):
            filepath += ".safetensors"

        # Prevent multiple save operations
        if self._safetensor_service.is_saving():
            self._view.set_status_message("Save operation already in progress.")
            return

        # Store the original file path as source for Save As operation
        source_file = self._current_file

        # Update current file path to new location
        self._current_file = filepath

        # Disable UI elements during save
        self._view.set_all_fields_enabled(False)
        self._view.show_progress_bar()
        self._view.set_status_message(f"Saving to {filepath}...")

        # Start async save operation
        success = self._safetensor_service.write_metadata_async(
            filepath=filepath,
            metadata=self._model.get_all_data(),
            progress_callback=self._on_save_progress,
            success_callback=self._on_save_as_success,
            error_callback=self._on_save_error,
            source_filepath=source_file,
        )

        if not success:
            self._view.set_status_message("Save operation already in progress.")
            self._view.set_all_fields_enabled(True)
            self._view.hide_progress_bar()

    def _on_save_as_success(self, filepath: str):
        self._on_save_success(filepath)

        # Add new file to recent files
        self._config_service.add_recent_file(filepath)

    def _on_save_progress(self, progress: int):
        self._view.set_progress_value(progress)

    def _on_save_success(self, filepath: str):
        self._view.set_status_message(f"Successfully saved to {filepath}", 5000)
        self._model.mark_saved()
        self.update_view()
        self._view.set_all_fields_enabled(True)
        self._view.hide_progress_bar()

    def _on_save_error(self, error_message: str):
        self._view.set_status_message(f"Save failed: {error_message}")
        self._view.set_all_fields_enabled(True)
        self._view.hide_progress_bar()

    def shutdown(self):
        self._safetensor_service.shutdown()
        self._config_service.remove_recent_files_observer(self._on_recent_files_changed)
        self._theme_service.remove_theme_changed_observer(self._on_theme_changed)
        self._model.remove_observer(self._on_metadata_changed)

    @Slot()
    def on_exit_requested(self):
        # TODO: Check for unsaved changes before exiting
        self.shutdown()
        self._view.close()

    def update_view(self):
        is_dirty = self._model.is_dirty()
        title = ""

        if self._current_file:
            filename = os.path.basename(self._current_file)
            title += f"{filename}"

        # Show dirty indicator if there are unsaved changes
        if is_dirty:
            title += " *"  # Add an asterisk to indicate unsaved changes

        self._view.set_window_title(title)

        binding_service = WidgetBindingService()
        binding_service.initialize_widgets_from_metadata()

        # Enable fields only if a file is loaded
        self._view.set_all_fields_enabled(self._current_file is not None)

        # Update ModelSpec compliance status
        self._update_modelspec_status()

    def _update_modelspec_status(self):
        """Update the ModelSpec compliance status in the view."""
        if self._current_file is None:
            self._view.clear_modelspec_status()
        else:
            compliance_result = self._modelspec_service.get_compliance_result()
            self._view.update_modelspec_status(compliance_result)

    @Slot()
    def on_modelspec_status_clicked(self):
        """Handle clicks on the ModelSpec status widget."""
        if not self._current_file:
            self._view.set_status_message(
                "No file loaded. Open a safetensors file to check ModelSpec compliance.",
                5000,
            )
            return

        # For now, just show a status message
        # In the future, this could open a detailed compliance dialog
        compliance_result = self._modelspec_service.get_compliance_result()

        if compliance_result.missing_must_fields:
            missing_count = len(compliance_result.missing_must_fields)
            self._view.set_status_message(
                f"ModelSpec: Missing {missing_count} required field(s). See tooltip for details.",
                7000,
            )
        else:
            self._view.set_status_message(
                "ModelSpec: All required fields present! Model is compliant.", 5000
            )
