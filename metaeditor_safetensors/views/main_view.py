import functools
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
)
from PySide6.QtWidgets import QMainWindow, QWidget

from ..layouts.main_ui_layout import Ui_EditorPanel
from ..models.modelspec import ModelType
from ..widgets.status_widget import StatusWidget

logger = logging.getLogger(__name__)


class MainView(QMainWindow):
    # --- Action Signals ---
    open_file_requested = Signal()
    save_requested = Signal()
    save_as_requested = Signal()
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
    thumbnail_dropped = Signal(str)

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

        self._setup_type_combobox()
        self._setup_status_bar()
        self._connect_signals()

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

    def _setup_status_bar(self):
        self.status_widget = StatusWidget()
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().addPermanentWidget(self.status_widget)

    def _create_menu_bar(self):
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

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_as_requested)
        file_menu.addAction(save_as_action)

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
        # Connect thumbnail button signals
        self.ui.set_thumbnail_btn.clicked.connect(self.set_thumbnail_requested)
        self.ui.clear_thumbnail_btn.clicked.connect(self.clear_thumbnail_requested)
        self.ui.view_thumbnail_btn.clicked.connect(self.view_thumbnail_requested)
        self.ui.thumbnail_display.imageDropped.connect(self.thumbnail_dropped.emit)

    # TODO: Initial state isn't being set up correctly. Initial value is always UNKNOWN
    def _setup_type_combobox(self):
        self.ui.type_select.clear()

        # Add each ModelType value to the combobox
        for model_type in ModelType:
            self.ui.type_select.addItem(model_type.value, model_type)

        # Set default to UNKNOWN
        index = self.ui.type_select.findData(ModelType.UNKNOWN)
        if index >= 0:
            self.ui.type_select.setCurrentIndex(index)

    def set_window_title(self, title: str):
        super().setWindowTitle(title)

    def set_status_message(self, message: str, timeout: int = 0):
        self.statusBar().showMessage(message, timeout)

    def show_progress_bar(self):
        self.ui.progress_bar.setValue(0)
        self.ui.progress_bar.setVisible(True)

    def hide_progress_bar(self):
        self.ui.progress_bar.setVisible(False)

    def set_progress_value(self, value: int):
        self.ui.progress_bar.setValue(value)

    def set_all_fields_enabled(self, enabled: bool):
        self.ui.title_edit.setEnabled(enabled)
        self.ui.type_select.setEnabled(enabled)
        self.ui.description_edit.setEnabled(enabled)
        self.ui.author_edit.setEnabled(enabled)
        self.ui.date_time_edit.setEnabled(enabled)
        self.ui.license_edit.setEnabled(enabled)
        self.ui.usage_hint_edit.setEnabled(enabled)
        self.ui.tags_edit.setEnabled(enabled)
        self.ui.merged_from_edit.setEnabled(enabled)
        self.ui.thumbnail_display.setEnabled(enabled)
        self.ui.set_thumbnail_btn.setEnabled(enabled)
        self.ui.view_thumbnail_btn.setEnabled(enabled)
        self.ui.clear_thumbnail_btn.setEnabled(enabled)

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
