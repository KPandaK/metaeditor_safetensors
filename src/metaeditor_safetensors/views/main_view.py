"""
Main View - The main application window view.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QMenuBar, QMenu, QSizePolicy, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont, QIcon

logger = logging.getLogger(__name__)


class MainView(QMainWindow):
    """
    Main application window view.
    
    This view is responsible only for UI layout and user interactions.
    It delegates all business logic to the controller through signals.
    """
    
    # Signals for controller communication
    file_browse_requested = Signal()
    file_opened = Signal(str)  # filepath
    metadata_load_requested = Signal()
    save_requested = Signal()
    thumbnail_set_requested = Signal()
    thumbnail_view_requested = Signal()
    raw_view_requested = Signal()
    about_requested = Signal()
    exit_requested = Signal()
    
    def __init__(self):
        super().__init__()
        
        # UI state
        self._current_file = None
        self._is_modified = False
        
        # Setup window
        self.setWindowTitle("Safetensors Metadata Editor")
        self.setMinimumSize(600, 400)
        self.resize(800, 600)
        
        # Load external stylesheet
        self._load_stylesheet()
        
        # Set up UI
        self._setup_ui()
        self._setup_menu()
        self._setup_icon()
        
        logger.info("Main view initialized")
    
    def _load_stylesheet(self) -> None:
        """Load external stylesheet."""
        try:
            style_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'main.qss')
            with open(style_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
            self.setStyleSheet(stylesheet)
            logger.info("Stylesheet loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load stylesheet: {e}")
    
    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # File selection section
        self._setup_file_header(main_layout)
        
        # Metadata section (will be populated by MetadataView)
        self.metadata_container = QGroupBox("Metadata")
        self.metadata_layout = QVBoxLayout(self.metadata_container)
        main_layout.addWidget(self.metadata_container)
        
        # Status section
        self._setup_status_section(main_layout)
    
    def _setup_file_header(self, parent_layout: QVBoxLayout) -> None:
        """Set up the file header section."""
        file_header = QWidget()
        file_header.setMaximumHeight(30)
        file_header.setProperty("class", "file-header")
        
        header_layout = QHBoxLayout(file_header)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # File icon
        file_icon = QLabel()
        standard_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)
        file_icon.setPixmap(standard_icon.pixmap(16, 16))
        file_icon.setMaximumWidth(20)
        header_layout.addWidget(file_icon)
        
        # Current file label
        self.current_file_label = QLabel("No file loaded")
        self.current_file_label.setProperty("class", "current-file")
        self.current_file_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(self.current_file_label)
        
        # Modified indicator
        self.modified_indicator = QLabel("")
        self.modified_indicator.setMaximumWidth(20)
        self.modified_indicator.setProperty("class", "modified-indicator")
        self.modified_indicator.setVisible(False)
        header_layout.addWidget(self.modified_indicator)
        
        parent_layout.addWidget(file_header)
    
    def _setup_status_section(self, parent_layout: QVBoxLayout) -> None:
        """Set up the status section."""
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(80)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("Ready! Select a file to begin.")
        parent_layout.addWidget(self.status_text)
    
    def _setup_menu(self) -> None:
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Open action
        open_action = QAction('Open File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self._on_browse_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Load metadata action
        load_action = QAction('Load Metadata', self)
        load_action.setShortcut('Ctrl+L')
        load_action.triggered.connect(self.metadata_load_requested.emit)
        file_menu.addAction(load_action)
        
        # Save changes action
        save_action = QAction('Save Changes', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_requested.emit)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.exit_requested.emit)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        # Set thumbnail action
        set_thumb_action = QAction('Set Thumbnail...', self)
        set_thumb_action.setShortcut('Ctrl+T')
        set_thumb_action.triggered.connect(self.thumbnail_set_requested.emit)
        edit_menu.addAction(set_thumb_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # View thumbnail action
        view_thumb_action = QAction('View Thumbnail', self)
        view_thumb_action.setShortcut('Ctrl+Shift+T')
        view_thumb_action.triggered.connect(self.thumbnail_view_requested.emit)
        view_menu.addAction(view_thumb_action)
        
        view_menu.addSeparator()
        
        # Raw metadata action
        raw_action = QAction('Raw Metadata Editor', self)
        raw_action.setShortcut('Ctrl+R')
        raw_action.triggered.connect(self.raw_view_requested.emit)
        view_menu.addAction(raw_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.about_requested.emit)
        help_menu.addAction(about_action)
    
    def _setup_icon(self) -> None:
        """Set up the application icon."""
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'safetensors.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def _on_browse_file(self) -> None:
        """Handle browse file button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Safetensors File",
            "",
            "Safetensors Files (*.safetensors);;All Files (*)"
        )
        
        if file_path:
            self.file_opened.emit(file_path)
    
    def set_metadata_view(self, metadata_view) -> None:
        """
        Set the metadata view widget.
        
        Args:
            metadata_view: MetadataView widget to embed
        """
        # Clear existing layout
        while self.metadata_layout.count():
            child = self.metadata_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new metadata view
        self.metadata_layout.addWidget(metadata_view)
    
    def update_file_display(self, filepath: Optional[str] = None) -> None:
        """
        Update the window title and file header to show current file.
        
        Args:
            filepath: Path to the current file, None to clear
        """
        if filepath:
            filename = os.path.basename(filepath)
            self.setWindowTitle(f"Safetensors Metadata Editor - {filename}")
            self.current_file_label.setText(filename)
            self._current_file = filepath
        else:
            self.setWindowTitle("Safetensors Metadata Editor")
            self.current_file_label.setText("No file loaded")
            self._current_file = None
    
    def set_modified(self, modified: bool = True) -> None:
        """
        Update the modified indicator.
        
        Args:
            modified: Whether the file has been modified
        """
        self._is_modified = modified
        
        if modified:
            self.modified_indicator.setText("●")
            self.modified_indicator.setVisible(True)
            # Add asterisk to window title if not already there
            title = self.windowTitle()
            if not title.endswith(" *"):
                self.setWindowTitle(title + " *")
        else:
            self.modified_indicator.setText("")
            self.modified_indicator.setVisible(False)
            # Remove asterisk from window title
            title = self.windowTitle()
            if title.endswith(" *"):
                self.setWindowTitle(title[:-2])
    
    def add_status_message(self, message: str) -> None:
        """
        Add a status message to the status area.
        
        Args:
            message: Status message to add
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.status_text.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_status(self) -> None:
        """Clear the status area."""
        self.status_text.clear()
    
    def show_error(self, title: str, message: str) -> None:
        """
        Show an error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        QMessageBox.critical(self, title, message)
    
    def show_warning(self, title: str, message: str) -> None:
        """
        Show a warning dialog.
        
        Args:
            title: Dialog title
            message: Warning message
        """
        QMessageBox.warning(self, title, message)
    
    def show_info(self, title: str, message: str) -> None:
        """
        Show an information dialog.
        
        Args:
            title: Dialog title
            message: Information message
        """
        QMessageBox.information(self, title, message)
    
    def ask_question(self, title: str, message: str) -> bool:
        """
        Ask a yes/no question.
        
        Args:
            title: Dialog title
            message: Question message
            
        Returns:
            True if user clicked Yes
        """
        result = QMessageBox.question(self, title, message)
        return result == QMessageBox.StandardButton.Yes
    
    @property
    def current_file(self) -> Optional[str]:
        """Get the current file path."""
        return self._current_file
    
    @property
    def is_modified(self) -> bool:
        """Check if the current file has been modified."""
        return self._is_modified
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.exit_requested.emit()
        event.accept()
