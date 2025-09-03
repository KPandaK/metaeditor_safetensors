"""
Main View
=========

This module defines the `MainView`, which is the main window of the application.
It is responsible for the overall UI structure, including the menu bar, and for
hosting the main editing panel designed in Qt Designer.

The `MainView` is a "dumb" component; it only displays data and emits signals
when the user interacts with it. It has no direct knowledge of the model.
"""

import base64
from PySide6.QtWidgets import QMainWindow, QWidget
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtCore import Signal, QDateTime, Qt, QSize

# This imports the class generated from the .ui file.
from ..ui.editor_panel_ui import Ui_EditorPanel
from ..models.metadata_keys import MetadataKeys
# Import custom widget so it can be found by the UI loader
from ..ui.image_widget import ImageWidget

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
    exit_requested = Signal()
    
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
            MetadataKeys.TITLE: (self.ui.titleEdit, 'setText'),
            MetadataKeys.DESCRIPTION: (self.ui.descriptionEdit, 'setPlainText'),
            MetadataKeys.AUTHOR: (self.ui.authorEdit, 'setText'),
            MetadataKeys.DATE: (self.ui.dateTimeEdit, 'setDateTime'),
            MetadataKeys.LICENSE: (self.ui.licenseEdit, 'setText'),
            MetadataKeys.USAGE_HINT: (self.ui.usageHintEdit, 'setText'),
            MetadataKeys.TAGS: (self.ui.tagsEdit, 'setText'),
            MetadataKeys.MERGED_FROM: (self.ui.mergedFromEdit, 'setText'),
        }
        # ---

        # Connect widget signals to this view's public signals.
        self._connect_signals()

        # Store original pixmap for proper resizing
        self._original_pixmap = None

    def _setup_window_properties(self):
        """Set up basic window properties like title and icon."""
        # Set window title
        self.setWindowTitle("Metadata Editor")
        
        # Set window icon
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icon.png")
        icon_path = os.path.abspath(icon_path)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.setWindowIcon(icon)
        else:
            # Optionally set a default icon or skip setting the icon
            pass

    def _create_menu_bar(self):
        """Creates the main menu bar and its actions."""
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        
        open_action = QAction("&Open...", self)
        open_action.triggered.connect(self.open_file_requested)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.triggered.connect(self.save_requested)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.exit_requested)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menu_bar.addMenu("&View")
        
        raw_view_action = QAction("View &Raw Metadata", self)
        raw_view_action.setEnabled(False) # Not implemented yet
        view_menu.addAction(raw_view_action)

        tensors_view_action = QAction("View &Tensors", self)
        tensors_view_action.setEnabled(False) # Not implemented yet
        view_menu.addAction(tensors_view_action)

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
        return self.editor_panel.findChild(QWidget, name)

    def set_window_title(self, title: str):
        """Sets the main window's title."""
        super().setWindowTitle(title)

    # --- Methods to update UI from Controller ---

    def set_thumbnail_from_data_uri(self, data_uri: str):
        """
        Converts a data URI string to a QPixmap and displays it.
        
        Args:
            data_uri: The base64-encoded data URI for the thumbnail image.
        """
        pixmap = None
        if data_uri and "base64," in data_uri:
            try:
                base64_data = data_uri.split("base64,")[1]
                pixmap_data = base64.b64decode(base64_data)
                pixmap = QPixmap()
                pixmap.loadFromData(pixmap_data)
                if pixmap.isNull():
                    pixmap = None # Ensure we have None for failed loads
            except Exception:
                pixmap = None # Ensure we have None on any error
        
        self.thumbnail_widget.setPixmap(pixmap)
        
        # Set property for CSS styling
        has_pixmap = pixmap is not None
        self.thumbnail_widget.setProperty("hasPixmap", "true" if has_pixmap else "false")
        
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

    def set_field_value(self, field_name: str, value: any):
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
            if setter_method_name == 'setDateTime':
                if isinstance(value, str):
                    # Attempt to parse ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)
                    dt = QDateTime.fromString(value, Qt.ISODateWithMs)
                    if not dt.isValid():
                        # Fallback for format without milliseconds
                        dt = QDateTime.fromString(value, Qt.ISODate)
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
