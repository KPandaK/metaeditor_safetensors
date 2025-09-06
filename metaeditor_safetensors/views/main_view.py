"""
Main View
=========

This module defines the `MainView`, which is the main window of the application.
It is responsible for the overall UI structure, including the menu bar, and for
hosting the main editing panel designed in Qt Designer.

The `MainView` is a "dumb" component; it only displays data and emits signals
when the user interacts with it. It has no direct knowledge of the model.
"""

import functools
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

from PySide6.QtCore import QDateTime, QSize, Qt, QUrl, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QPixmap,
)
from PySide6.QtWidgets import QMainWindow, QWidget

from ..models.metadata_keys import MetadataKeys

# Import custom widget so it can be found by the UI loader
from ..widgets.image_widget import ImageWidget
from .about_dialog import AboutDialog

# This imports the class generated from the .ui file.
from .main_view_ui import Ui_EditorPanel


class MainView(QMainWindow):
    """
    The main application window.

    This class creates the main window frame (menu bar, status bar) and
    embeds the editor panel from the Qt Designer file as its central widget.
    It emits signals for user actions that the controller will connect to.
    """

    # --- Action Signals ---
    open_file_requested = Signal()
    save_requested = Signal()
    settings_requested = Signal()
    exit_requested = Signal()
    file_dropped = Signal(str)
    recent_file_triggered = Signal(str)
    clear_recent_requested = Signal()

    # --- Theme Signals ---
    theme_requested = Signal(str)
    
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

    def __init__(self):
        super().__init__()

        # Set a default window size for a better initial appearance
        self.resize(900, 450)

        # Set up window icon and title
        self._setup_window_properties()

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Create the main window's menu bar
        self._create_menu_bar()

        # The 'ui' attribute will hold the instance of the generated UI class.
        # This class is a QWidget, which we will set as the central widget.
        self.editor_panel = QWidget()
        self.ui = Ui_EditorPanel()
        self.ui.setupUi(self.editor_panel)
        self.setCentralWidget(self.editor_panel)

        # The thumbnail widget is now created directly by Qt Designer promotion
        # Store reference to the custom widget for easy access
        self.thumbnail_widget = self.ui.thumbnailDisplay

        # --- Widget Mapping for Data Binding ---
        self._widget_map = {
            MetadataKeys.TITLE: (self.ui.titleEdit, "setText"),
            MetadataKeys.DESCRIPTION: (self.ui.descriptionEdit, "setPlainText"),
            MetadataKeys.AUTHOR: (self.ui.authorEdit, "setText"),
            MetadataKeys.DATE: (self.ui.dateTimeEdit, "setDateTime"),
            MetadataKeys.LICENSE: (self.ui.licenseEdit, "setText"),
            MetadataKeys.USAGE_HINT: (self.ui.usageHintEdit, "setText"),
            MetadataKeys.TAGS: (self.ui.tagsEdit, "setText"),
            MetadataKeys.MERGED_FROM: (self.ui.mergedFromEdit, "setText"),
        }
        # ---

        # Connect widget signals to this view's public signals.
        self._connect_signals()

        # Store original pixmap for proper resizing
        self._original_pixmap = None

    def _setup_window_properties(self):
        """Set up the window icon."""

        # Set window icon from Qt resources
        icon = QIcon(":/assets/icon.ico")
        if not icon.isNull():
            self.setWindowIcon(icon)
        else:
            logger.warning("Could not load icon from resources")

    def _create_menu_bar(self):
        """Creates the main menu bar and its actions."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        open_action = QAction("&Open...", self)
        open_action.triggered.connect(self.open_file_requested)
        file_menu.addAction(open_action)

        # Open Recent submenu
        self.recent_files_menu = file_menu.addMenu("Open &Recent")
        self._update_recent_files_menu([])  # Initialize with empty list

        save_action = QAction("&Save", self)
        save_action.triggered.connect(self.save_requested)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Settings action in File menu
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self.settings_requested)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.exit_requested)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menu_bar.addMenu("&View")

        raw_view_action = QAction("View &Raw Metadata", self)
        raw_view_action.setEnabled(False)  # Not implemented yet
        view_menu.addAction(raw_view_action)
        view_menu.addAction(raw_view_action)

        tensors_view_action = QAction("View &Tensors", self)
        tensors_view_action.setEnabled(False)  # Not implemented yet
        view_menu.addAction(tensors_view_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_window)
        help_menu.addAction(about_action)

    def show_about_window(self):
        """Shows the about window."""
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def update_recent_files_menu(self, recent_files: list[str]):
        """
        Updates the "Open Recent" submenu with the provided list of files.

        Args:
            recent_files: List of file paths to display in the menu
        """
        self._update_recent_files_menu(recent_files)

    def _update_recent_files_menu(self, recent_files: list[str]):
        """Internal method to rebuild the recent files menu."""
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
        """
        Connects the signals from the UI widgets to the view's own signals.
        """
        self.ui.titleEdit.textChanged.connect(self.title_changed)
        self.ui.descriptionEdit.textChanged.connect(
            lambda: self.description_changed.emit(self.ui.descriptionEdit.toPlainText())
        )
        self.ui.authorEdit.textChanged.connect(self.author_changed)
        self.ui.dateTimeEdit.dateTimeChanged.connect(self.datetime_changed)
        self.ui.licenseEdit.textChanged.connect(self.license_changed)
        self.ui.usageHintEdit.textChanged.connect(self.usage_hint_changed)
        self.ui.tagsEdit.textChanged.connect(self.tags_changed)
        self.ui.mergedFromEdit.textChanged.connect(self.merged_from_changed)

        # Connect thumbnail button signals
        self.ui.setThumbnailBtn.clicked.connect(self.set_thumbnail_requested)
        self.ui.clearThumbnailBtn.clicked.connect(self.clear_thumbnail_requested)
        self.ui.viewThumbnailBtn.clicked.connect(self.view_thumbnail_requested)

    def get_widget(self, name: str) -> QWidget:
        """
        Provides access to a widget by its object name from the .ui file.

        Args:
            name: The objectName of the widget set in Qt Designer.

        Returns:
            The QWidget instance, or None if not found.
        """
        widget = self.editor_panel.findChild(QWidget, name)
        return widget if widget is not None else QWidget()

    def set_window_title(self, title: str):
        """Sets the main window's title."""
        super().setWindowTitle(title)

    # --- Methods to update UI from Controller ---

    def set_thumbnail_pixmap(self, pixmap: QPixmap | None):
        """
        Displays the provided QPixmap as the thumbnail.

        Args:
            pixmap: The QPixmap to display, or None to clear the thumbnail.
        """
        self.thumbnail_widget.setPixmap(pixmap)

        # Set property for CSS styling
        has_pixmap = pixmap is not None
        self.thumbnail_widget.setProperty(
            "hasPixmap", "true" if has_pixmap else "false"
        )

        # Apply the updated styling
        self.thumbnail_widget.style().unpolish(self.thumbnail_widget)
        self.thumbnail_widget.style().polish(self.thumbnail_widget)

    def set_status_message(self, message: str, timeout: int = 0):
        """Displays a message in the status bar."""
        self.statusBar().showMessage(message, timeout)

    def show_progress_bar(self):
        """Shows the progress bar and resets it to 0."""
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setVisible(True)

    def hide_progress_bar(self):
        """Hides the progress bar."""
        self.ui.progressBar.setVisible(False)

    def set_progress_value(self, value: int):
        """Sets the progress bar value (0-100)."""
        self.ui.progressBar.setValue(value)

    def update_all_fields(self, data: dict):
        """
        Updates all UI fields based on the provided data dictionary.
        """
        for field_name in self._widget_map.keys():
            value = data.get(field_name, "")
            self.set_field_value(field_name, value)

    def set_field_value(self, field_name: str, value: Any):
        """
        Sets the value of a specific field in the UI using the widget map.
        The controller calls this when the model is updated.
        """
        if field_name in self._widget_map:
            widget, setter_method_name = self._widget_map[field_name]
            setter_method = getattr(widget, setter_method_name)

            # Block signals to prevent feedback loops
            widget.blockSignals(True)

            # --- Type-Specific Handling ---
            # Convert string to QDateTime for the datetime widget
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
            # For all other widgets, convert the value to a string
            else:
                setter_method(str(value))
            # ---

            widget.blockSignals(False)

    def set_all_fields_enabled(self, enabled: bool):
        """Enables or disables all input fields."""
        self.ui.titleEdit.setEnabled(enabled)
        self.ui.descriptionEdit.setEnabled(enabled)
        self.ui.authorEdit.setEnabled(enabled)
        self.ui.dateTimeEdit.setEnabled(enabled)
        self.ui.licenseEdit.setEnabled(enabled)
        self.ui.usageHintEdit.setEnabled(enabled)
        self.ui.tagsEdit.setEnabled(enabled)
        self.ui.mergedFromEdit.setEnabled(enabled)
        self.ui.setThumbnailBtn.setEnabled(enabled)
        self.ui.viewThumbnailBtn.setEnabled(enabled)
        self.ui.clearThumbnailBtn.setEnabled(enabled)

    # --- Drag and Drop Support ---

    def _is_valid_safetensors_file(self, urls):
        """
        Checks if any of the provided QUrls point to a local .safetensors file.
        Returns the first valid file path, or None if not found.
        """
        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(".safetensors"):
                    return file_path
        return None

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events - accept if dragging .safetensors files."""
        if event.mimeData().hasUrls():
            if self._is_valid_safetensors_file(event.mimeData().urls()):
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move events - accept if we accepted the drag enter."""
        if event.mimeData().hasUrls():
            if self._is_valid_safetensors_file(event.mimeData().urls()):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events - process the first .safetensors file that was dropped."""
        if event.mimeData().hasUrls():
            file_path = self._is_valid_safetensors_file(event.mimeData().urls())
            if file_path:
                # Emit signal with the first valid .safetensors file
                self.file_dropped.emit(file_path)
                event.acceptProposedAction()
                return
        event.ignore()
