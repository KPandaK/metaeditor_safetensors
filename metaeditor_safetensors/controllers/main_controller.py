import logging
import os
from typing import List

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QFileDialog

from ..bindings.main_view_bindings import build_main_view_bindings
from ..models.metadata import ChangeSource, Metadata
from ..services.config_service import ConfigService
from ..services.file_workflow import FileWorkflow, LoadResult
from ..services.modelspec_service import ModelSpecService
from ..services.safetensors_service import SafetensorsService
from ..services.status_message_service import StatusMessageService
from ..services.theme_coordinator import ThemeCoordinator
from ..services.widget_binding_service import WidgetBindingService
from ..views.about_dialog import AboutDialog
from ..views.main_view import MainView
from .thumbnail_controller import ThumbnailController

logger = logging.getLogger(__name__)


class MainController(QObject):
    def __init__(
        self,
        model: Metadata,
        view: MainView,
        config_service: ConfigService,
        safetensors_service: SafetensorsService,
        theme_coordinator: ThemeCoordinator,
        modelspec_service: ModelSpecService,
        status_message_service: StatusMessageService,
    ):
        super().__init__()
        self._model = model
        self._view = view
        self._config_service = config_service
        self._safetensor_service = safetensors_service
        self._theme_coordinator = theme_coordinator
        self._modelspec_service = modelspec_service
        self._status_messages = status_message_service

        self._binding_service = WidgetBindingService(
            self._model, build_main_view_bindings(self._view.ui)
        )

        self._file_workflow = FileWorkflow(
            self._model,
            self._safetensor_service,
            self._config_service,
        )

        self._thumbnail_controller = ThumbnailController(
            self._model,
            self._view,
            self._status_messages,
        )

        # Register for recent files changes
        self._config_service.add_recent_files_observer(self._on_recent_files_changed)

        # Register for metadata changes to update UI
        self._model.add_observer(self._on_metadata_changed)

        # Register status widget as ModelSpec observer for automatic updates
        self._modelspec_service.add_observer(
            self._view.status_widget.on_compliance_changed
        )

        # Connect the view's signals to the controller's slots.
        self._connect_signals()

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
        self._view.set_thumbnail_requested.connect(
            self._thumbnail_controller.on_set_thumbnail_requested
        )
        self._view.clear_thumbnail_requested.connect(
            self._thumbnail_controller.on_clear_thumbnail_requested
        )
        self._view.view_thumbnail_requested.connect(
            self._thumbnail_controller.on_view_thumbnail_requested
        )
        self._view.thumbnail_dropped.connect(
            self._thumbnail_controller.on_thumbnail_dropped
        )

    def run(self):
        self._view.show()
        self._view.set_all_fields_enabled(False)
        self._status_messages.info(
            "Ready. Please open a safetensors file to begin.", timeout_ms=None
        )

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

    def _load_file(self, filepath: str) -> None:
        result = self._file_workflow.load_file(filepath)
        self._handle_load_result(result)

    def _handle_load_result(self, result: LoadResult) -> None:
        if result.success:
            self.update_view()
            self._status_messages.success(result.message)
            return

        if result.error:
            logger.error("Failed to load file: %s", result.error)

        self._file_workflow.clear_current_file()
        self.update_view()
        self._status_messages.error(result.message)

    @Slot(str)
    def on_recent_file_triggered(self, filepath: str):
        # Check if file still exists
        if not os.path.exists(filepath):
            self._status_messages.warning(f"File no longer exists: {filepath}")
            # Remove from recent files list
            self._config_service.remove_recent_file(filepath)
            return

        self._load_file(filepath)

    @Slot()
    def on_clear_recent_requested(self):
        self._config_service.clear_recent_files()
        self._status_messages.info("Recent files cleared.")

    # TODO: Rework settings, make it a real thing instead of a stub
    def on_settings_requested(self):
        self._status_messages.info(
            "Settings dialog is not available yet.", timeout_ms=3000
        )

    def on_about_requested(self):
        about_dialog = AboutDialog(parent=self._view)
        about_dialog.exec()

    def _on_recent_files_changed(self, recent_files: List[str]):
        self._view.update_recent_files_menu(recent_files)

    def _on_metadata_changed(
        self, field=None, source=ChangeSource.PROGRAMMATIC, source_widget=None
    ):
        self._update_window_title()

        # Update widgets based on change source and field
        if field is not None:
            if source == ChangeSource.USER and source_widget is not None:
                # User change - update other widgets for the same field, excluding source widget
                self._binding_service.update_widget_from_metadata(
                    field, exclude_widget=source_widget
                )
            else:
                # Programmatic or unspecified change - sync all widgets for this field
                self._binding_service.update_widget_from_metadata(field)

    def _update_window_title(self):
        is_dirty = self._model.is_dirty()
        title = ""

        if self._file_workflow.current_file:
            filename = os.path.basename(self._file_workflow.current_file)
            title += f"{filename}"

        # Show dirty indicator if there are unsaved changes
        if is_dirty:
            title += " *"  # Add an asterisk to indicate unsaved changes

        self._view.set_window_title(title)

    @Slot()
    def on_save_requested(self):
        if not self._file_workflow.current_file:
            self._status_messages.warning("Please open a file first.")
            return

        if not self._model.is_dirty():
            self._status_messages.info("No changes to save.")
            return

        dispatch = self._file_workflow.save(
            progress_callback=self._on_save_progress,
            success_callback=self._on_save_success,
            error_callback=self._on_save_error,
        )

        if not dispatch.started:
            self._status_messages.error(dispatch.message)
            return

        self._view.set_all_fields_enabled(False)
        self._view.show_progress_bar()
        self._status_messages.info(dispatch.message)

    @Slot()
    def on_save_as_requested(self):
        if not self._model.get_all_data():
            self._status_messages.warning("Please open a file first.")
            return

        initial_dir = ""
        if self._file_workflow.current_file:
            initial_dir = os.path.dirname(self._file_workflow.current_file)

        filepath, _ = QFileDialog.getSaveFileName(
            self._view,
            "Save As",
            initial_dir,
            "Safetensors Files (*.safetensors);;All Files (*)",
        )

        if not filepath:
            return

        if not filepath.lower().endswith(".safetensors"):
            filepath += ".safetensors"

        dispatch = self._file_workflow.save_as(
            filepath=filepath,
            progress_callback=self._on_save_progress,
            success_callback=self._on_save_success,
            error_callback=self._on_save_error,
        )

        if not dispatch.started:
            self._status_messages.error(dispatch.message)
            return

        self._view.set_all_fields_enabled(False)
        self._view.show_progress_bar()
        self._status_messages.info(dispatch.message)

    def _on_save_progress(self, progress: int):
        self._view.set_progress_value(progress)

    def _on_save_success(self, filepath: str):
        self._status_messages.success(f"Successfully saved to {filepath}")
        self._model.mark_saved()
        self.update_view()
        self._view.set_all_fields_enabled(True)
        self._view.hide_progress_bar()

    def _on_save_error(self, error_message: str):
        self._status_messages.error(f"Save failed: {error_message}")
        self._view.set_all_fields_enabled(True)
        self._view.hide_progress_bar()

    def shutdown(self):
        self._safetensor_service.shutdown()
        self._theme_coordinator.shutdown()
        self._config_service.remove_recent_files_observer(self._on_recent_files_changed)
        self._binding_service.clear_bindings()
        self._model.remove_observer(self._on_metadata_changed)

    @Slot()
    def on_exit_requested(self):
        # TODO: Check for unsaved changes before exiting
        self.shutdown()
        self._view.close()

    def update_view(self):
        is_dirty = self._model.is_dirty()
        title = ""

        if self._file_workflow.current_file:
            filename = os.path.basename(self._file_workflow.current_file)
            title += f"{filename}"

        # Show dirty indicator if there are unsaved changes
        if is_dirty:
            title += " *"  # Add an asterisk to indicate unsaved changes

        self._view.set_window_title(title)

        self._binding_service.initialize_widgets()

        # Enable fields only if a file is loaded
        self._view.set_all_fields_enabled(self._file_workflow.current_file is not None)
