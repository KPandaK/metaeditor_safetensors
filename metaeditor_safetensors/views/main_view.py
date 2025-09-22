import functools
import logging
from typing import Any

logger = logging.getLogger(__name__)

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QPixmap,
)
from PySide6.QtWidgets import QMainWindow, QWidget

from ..layouts.main_ui_layout import Ui_EditorPanel
from ..models.modelspec import ModelSpec
from ..widgets.modelspec_status_widget import ModelSpecStatusWidget


class MainView(QMainWindow):
    # --- Action Signals ---
    open_file_requested = Signal()
    save_requested = Signal()
    settings_requested = Signal()
    about_requested = Signal()
    exit_requested = Signal()
    file_dropped = Signal(str)
    recent_file_triggered = Signal(str)
    clear_recent_requested = Signal()

    # --- Thumbnail Signals ---
    set_thumbnail_requested = Signal()
    clear_thumbnail_requested = Signal()
    view_thumbnail_requested = Signal()

    # --- Metadata Field Change Signals ---
    title_changed = Signal(str)
    description_changed = Signal(str)
    author_changed = Signal(str)
    datetime_changed = Signal(QDateTime)
    license_changed = Signal(str)
    usage_hint_changed = Signal(str)
    tags_changed = Signal(str)
    merged_from_changed = Signal(str)

    # --- ModelSpec Status Widget Signals ---
    modelspec_status_clicked = Signal()

    def __init__(self, config_service):
        super().__init__()

        # Store config service reference
        self._config_service = config_service

        # Set window size from config
        width, height = self._config_service.get_window_size()
        self.resize(width, height)

        # Set up window icon and title
        self._setup_window_properties()

        # Create the main window's menu bar
        self._create_menu_bar()

        self.editor_panel = QWidget()
        self.ui = Ui_EditorPanel()
        self.ui.setup_ui(self.editor_panel)
        self.setCentralWidget(self.editor_panel)

        self._widget_map = {
            ModelSpec.get_field_name("title"): {
                "widget": self.ui.title_edit,
                "setter": "setText",
            },
            ModelSpec.get_field_name("description"): {
                "widget": self.ui.description_edit,
                "setter": "setPlainText",
            },
            ModelSpec.get_field_name("author"): {
                "widget": self.ui.author_edit,
                "setter": "setText",
            },
            ModelSpec.get_field_name("date"): {
                "widget": self.ui.date_time_edit,
                "setter": "setDateTime",
                "supports_placeholder": False,
            },
            ModelSpec.get_field_name("license"): {
                "widget": self.ui.license_edit,
                "setter": "setText",
            },
            ModelSpec.get_field_name("usage_hint"): {
                "widget": self.ui.usage_hint_edit,
                "setter": "setText",
            },
            ModelSpec.get_field_name("tags"): {
                "widget": self.ui.tags_edit,
                "setter": "setText",
            },
            ModelSpec.get_field_name("merged_from"): {
                "widget": self.ui.merged_from_edit,
                "setter": "setText",
            },
        }

        self._setup_placeholder_texts()
        self._connect_signals()

        # TODO: Remove me - this should be added through Qt Designer
        # Create and add ModelSpec status widget to status bar
        self._modelspec_status_widget = ModelSpecStatusWidget()
        self._modelspec_status_widget.clicked.connect(self.modelspec_status_clicked)
        self.statusBar().addPermanentWidget(self._modelspec_status_widget)

    def _setup_window_properties(self):
        # Set window icon from Qt resources
        icon = QIcon(":/assets/icon.ico")
        if not icon.isNull():
            self.setWindowIcon(icon)
        else:
            logger.warning("Could not load icon from resources")

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _create_menu_bar(self):
        """Creates the main menu bar and its actions."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file_requested)
        file_menu.addAction(open_action)

        # Open Recent submenu
        self.recent_files_menu = file_menu.addMenu("Open &Recent")
        self._update_recent_files_menu([])

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_requested)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Settings action in File menu
        settings_action = QAction("S&ettings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.settings_requested)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.exit_requested)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menu_bar.addMenu("&View")

        raw_view_action = QAction("View &Raw Metadata", self)
        raw_view_action.setShortcut("Ctrl+Shift+R")
        raw_view_action.setEnabled(False)  # Not implemented yet
        view_menu.addAction(raw_view_action)

        tensors_view_action = QAction("View &Tensors", self)
        tensors_view_action.setShortcut("Ctrl+Shift+T")
        tensors_view_action.setEnabled(False)  # Not implemented yet
        view_menu.addAction(tensors_view_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.about_requested)
        help_menu.addAction(about_action)

    def update_recent_files_menu(self, recent_files: list[str]):
        self._update_recent_files_menu(recent_files)

    def _update_recent_files_menu(self, recent_files: list[str]):
        # Clear existing actions
        self.recent_files_menu.clear()

        if not recent_files:
            # Show "No Recent Files" when list is empty
            no_files_action = QAction("No Recent Files", self)
            no_files_action.setEnabled(False)
            self.recent_files_menu.addAction(no_files_action)
        else:
            for file_path in recent_files:
                # Show just the filename in the menu for readability
                import os

                filename = os.path.basename(file_path)
                action = QAction(filename, self)
                action.setToolTip(file_path)  # Show full path in tooltip
                # Connect to signal with file path using functools.partial to avoid closure issues
                action.triggered.connect(
                    functools.partial(self.recent_file_triggered.emit, file_path)
                )
                self.recent_files_menu.addAction(action)

            # Add separator and Clear action
            self.recent_files_menu.addSeparator()

        # Always show Clear action (enabled only when there are files)
        clear_action = QAction("Clear List", self)
        clear_action.setVisible(len(recent_files) > 0)
        clear_action.triggered.connect(self.clear_recent_requested)
        self.recent_files_menu.addAction(clear_action)

    def _connect_signals(self):
        self.ui.title_edit.textChanged.connect(self.title_changed)
        self.ui.description_edit.textChanged.connect(
            lambda: self.description_changed.emit(
                self.ui.description_edit.toPlainText()
            )
        )
        self.ui.author_edit.textChanged.connect(self.author_changed)
        self.ui.date_time_edit.dateTimeChanged.connect(self.datetime_changed)
        self.ui.license_edit.textChanged.connect(self.license_changed)
        self.ui.usage_hint_edit.textChanged.connect(
            lambda: self.usage_hint_changed.emit(self.ui.usage_hint_edit.toPlainText())
        )
        self.ui.tags_edit.textChanged.connect(self.tags_changed)
        self.ui.merged_from_edit.textChanged.connect(self.merged_from_changed)

        # Connect thumbnail button signals
        self.ui.set_thumbnail_btn.clicked.connect(self.set_thumbnail_requested)
        self.ui.clear_thumbnail_btn.clicked.connect(self.clear_thumbnail_requested)
        self.ui.view_thumbnail_btn.clicked.connect(self.view_thumbnail_requested)

    def _setup_placeholder_texts(self):
        placeholders = ModelSpec.get_all_field_placeholders()

        for field_name, widget_info in self._widget_map.items():
            raw_field_name = field_name.replace("modelspec.", "")

            supports_placeholder = widget_info.get("supports_placeholder", True)

            if (
                supports_placeholder
                and raw_field_name in placeholders
                and placeholders[raw_field_name]
            ):
                widget = widget_info["widget"]
                placeholder_text = placeholders[raw_field_name]

                if hasattr(widget, "setPlaceholderText"):
                    widget.setPlaceholderText(placeholder_text)
                elif hasattr(widget, "setPlainText") and not widget.toPlainText():
                    pass

    def set_window_title(self, title: str):
        """Sets the main window's title."""
        super().setWindowTitle(title)

    # --- Methods to update UI from Controller ---

    def set_thumbnail_pixmap(self, pixmap: QPixmap | None):
        if hasattr(self.ui, "thumbnail_display"):
            self.ui.thumbnail_display.setPixmap(pixmap)
        else:
            logger.warning("UI does not have a 'thumbnail_display' attribute.")

    def set_status_message(self, message: str, timeout: int = 0):
        """Displays a message in the status bar."""
        self.statusBar().showMessage(message, timeout)

    def show_progress_bar(self):
        self.ui.progress_bar.setValue(0)
        self.ui.progress_bar.setVisible(True)

    def hide_progress_bar(self):
        self.ui.progress_bar.setVisible(False)

    def set_progress_value(self, value: int):
        self.ui.progress_bar.setValue(value)

    def update_all_fields(self, data: dict):
        for field_name in self._widget_map.keys():
            value = data.get(field_name, "")
            self.set_field_value(field_name, value)

    def set_field_value(self, field_name: str, value: Any):
        if field_name in self._widget_map:
            widget_info = self._widget_map[field_name]
            widget = widget_info["widget"]
            setter_method_name = widget_info["setter"]
            setter_method = getattr(widget, setter_method_name)

            widget.blockSignals(True)

            if setter_method_name == "setDateTime":
                if isinstance(value, str):
                    # Attempt to parse ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)
                    dt = QDateTime.fromString(value, Qt.DateFormat.ISODateWithMs)
                    if not dt.isValid():
                        # Fallback for format without milliseconds
                        dt = QDateTime.fromString(value, Qt.DateFormat.ISODate)
                    setter_method(dt)
                elif isinstance(value, QDateTime):
                    setter_method(value)
            else:
                setter_method(str(value))

            widget.blockSignals(False)

    def set_all_fields_enabled(self, enabled: bool):
        self.ui.title_edit.setEnabled(enabled)
        self.ui.description_edit.setEnabled(enabled)
        self.ui.author_edit.setEnabled(enabled)
        self.ui.date_time_edit.setEnabled(enabled)
        self.ui.license_edit.setEnabled(enabled)
        self.ui.usage_hint_edit.setEnabled(enabled)
        self.ui.tags_edit.setEnabled(enabled)
        self.ui.merged_from_edit.setEnabled(enabled)
        self.ui.set_thumbnail_btn.setEnabled(enabled)
        self.ui.view_thumbnail_btn.setEnabled(enabled)
        self.ui.clear_thumbnail_btn.setEnabled(enabled)

    def update_modelspec_status(self, compliance_result):
        """
        Update the ModelSpec status widget with compliance information.

        Args:
            compliance_result: ComplianceResult from ModelSpecService
        """
        self._modelspec_status_widget.set_compliance_result(compliance_result)

    def clear_modelspec_status(self):
        """Clear the ModelSpec status (no file loaded)."""
        self._modelspec_status_widget.clear_compliance()

    # --- Drag and Drop Support ---

    def _is_valid_safetensors_file(self, urls):
        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(".safetensors"):
                    return file_path
        return None

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            if self._is_valid_safetensors_file(event.mimeData().urls()):
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            if self._is_valid_safetensors_file(event.mimeData().urls()):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_path = self._is_valid_safetensors_file(event.mimeData().urls())
            if file_path:
                # Emit signal with the first valid .safetensors file
                self.file_dropped.emit(file_path)
                event.acceptProposedAction()
                return
        event.ignore()

    def closeEvent(self, event):
        # Save current window size
        geometry = self.geometry()
        self._config_service.set_window_size(geometry.width(), geometry.height())
        super().closeEvent(event)
