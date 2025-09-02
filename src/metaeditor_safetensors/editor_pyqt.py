import os
import sys
import json
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QFormLayout, QScrollArea, QFrame, QMenuBar, QMenu, QSizePolicy, QGroupBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QFont, QIcon, QPixmap

from config import (
    MODELSPEC_KEY_MAP, GITHUB_URL,
    MAX_FIELD_LENGTH, MAX_DESCRIPTION_LENGTH, REQUIRED_FIELDS
)
from utils import compute_sha256, utc_to_local, local_to_utc
from commands import (
    BrowseFileCommand, LoadMetadataCommand, SaveCommand,
    SetThumbnailCommand
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThumbnailWidget(QWidget):
    """Custom widget for thumbnail display and management."""
    
    def __init__(self):
        super().__init__()
        self.thumbnail_data = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Image display area
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                background-color: #fafafa;
                color: #888888;
            }
        """)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("No thumbnail")
        self.image_label.setScaledContents(True)
        layout.addWidget(self.image_label)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(3)
        
        # Create small buttons
        self.set_button = QPushButton("Set")
        self.view_button = QPushButton("View")
        self.clear_button = QPushButton("Clear")
        
        # Make buttons small
        for button in [self.set_button, self.view_button, self.clear_button]:
            button.setMaximumHeight(24)
            button.setFont(QFont("Arial", 8))
        
        button_layout.addWidget(self.set_button)
        button_layout.addWidget(self.view_button)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        
        # Connect button signals (we'll implement these methods)
        self.set_button.clicked.connect(self.set_thumbnail)
        self.view_button.clicked.connect(self.view_thumbnail)
        self.clear_button.clicked.connect(self.clear_thumbnail)
    
    def set_thumbnail_data(self, data):
        """Set thumbnail data and update display."""
        self.thumbnail_data = data
        if data:
            # Create pixmap from data and display
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                # Scale to fit the label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setText("")
            else:
                self.image_label.setText("Invalid image")
        else:
            self.image_label.clear()
            self.image_label.setText("No thumbnail")
    
    def get_thumbnail_data(self):
        """Get current thumbnail data."""
        return self.thumbnail_data
    
    def set_thumbnail(self):
        """Handle set thumbnail button click."""
        # This will be connected to the main editor's set thumbnail functionality
        if hasattr(self.parent(), 'set_thumbnail'):
            self.parent().set_thumbnail()
    
    def view_thumbnail(self):
        """Handle view thumbnail button click."""
        # This will be connected to the main editor's view thumbnail functionality
        if hasattr(self.parent(), 'view_thumbnail'):
            self.parent().view_thumbnail()
    
    def clear_thumbnail(self):
        """Handle clear thumbnail button click."""
        self.set_thumbnail_data(None)

class SafetensorsEditorPyQt(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize state
        self.filepath = ""
        self.metadata = {}
        self.fields = {}
        self.field_config = {}
        
        # Load field configuration from JSON
        self._load_field_config()
        
        # Set up the main window
        self.setWindowTitle("Safetensors Metadata Editor")
        self.setMinimumSize(600, 400)
        self.resize(800, 600)
        
        # Load external stylesheet
        self.load_stylesheet()
        
        # Set up UI
        self.setup_ui()
        self.setup_menu()
        
        # Set up icon if available
        self.setup_icon()

        logger.info("Editor initialized!")

    def _load_field_config(self):
        """Load field configuration from JSON file."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'field_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.field_config = json.load(f)
            logger.info("Field configuration loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load field configuration: {e}")

    def load_stylesheet(self):
        try:
            import os
            style_path = os.path.join(os.path.dirname(__file__), 'styles', 'main.qss')
            with open(style_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
            self.setStyleSheet(stylesheet)
            logger.info("Stylesheet loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load stylesheet: {e}")

    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # File selection section
        self.setup_file_header(main_layout)
        
        # Metadata fields section
        self.setup_metadata_section(main_layout)
        
        # Status section
        self.setup_status_section(main_layout)

    def setup_file_header(self, parent_layout):
        # Create file header container
        file_header = QWidget()
        file_header.setMaximumHeight(30)
        file_header.setProperty("class", "file-header")
        
        header_layout = QHBoxLayout(file_header)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # File icon using Qt standard icon
        file_icon = QLabel()
        standard_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)
        file_icon.setPixmap(standard_icon.pixmap(16, 16))
        file_icon.setMaximumWidth(20)
        header_layout.addWidget(file_icon)
        
        # Current file label
        self.current_file_label = QLabel("No file loaded")
        self.current_file_label.setProperty("class", "current-file")
        # Make the file label expand to fill available space
        self.current_file_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(self.current_file_label)
        
        # Modified indicator
        self.modified_indicator = QLabel("")
        self.modified_indicator.setMaximumWidth(20)
        self.modified_indicator.setProperty("class", "modified-indicator")
        # Hide the indicator when it's empty
        self.modified_indicator.setVisible(False)
        header_layout.addWidget(self.modified_indicator)
        
        parent_layout.addWidget(file_header)

    def setup_metadata_section(self, parent_layout):
        # Create group box with title and border
        metadata_group = QGroupBox("General Data")
        metadata_group.setProperty("class", "metadata-group")
        
        # Create layout for the group box
        group_layout = QVBoxLayout(metadata_group)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        self.metadata_layout = QFormLayout(scroll_widget)
        self.metadata_layout.setSpacing(5)
        
        # Add metadata fields
        self.create_metadata_fields()
        
        scroll_area.setWidget(scroll_widget)
        group_layout.addWidget(scroll_area)
        parent_layout.addWidget(metadata_group)

    def create_metadata_fields(self):
        self.fields = {}
        
        # Use the field names from the JSON config instead of hardcoded list
        for field_name in self.field_config.keys():
            # Get field configuration from loaded JSON
            config = self.field_config[field_name]
            
            # Create label
            label = QLabel(f"{field_name}:")
            
            # Create widget based on configuration
            widget = self._create_widget_from_config(config)
              
            # Set tooltip from JSON configuration
            if 'tooltip' in config:
                widget.setToolTip(config['tooltip'])
            
            # Store reference to the widget
            self.fields[field_name] = widget
            
            # Add to layout
            self.metadata_layout.addRow(label, widget)
    
    def _create_widget_from_config(self, config):
        """Create a widget based on field configuration."""
        widget_type = config.get('widget_type', 'line_edit')
        
        if widget_type == 'text_edit':
            widget = QTextEdit()
            if 'max_height' in config:
                widget.setMaximumHeight(config['max_height'])
            if 'placeholder' in config:
                widget.setPlaceholderText(config['placeholder'])
                
        elif widget_type == 'line_edit':
            widget = QLineEdit()
            if 'placeholder' in config:
                widget.setPlaceholderText(config['placeholder'])
            if 'max_length' in config:
                widget.setMaxLength(config['max_length'])
            if config.get('read_only', False):
                widget.setReadOnly(True)
        
        elif widget_type == 'thumbnail':
            widget = ThumbnailWidget()
            
        else:
            # Fallback to line edit
            widget = QLineEdit()
        
        return widget





    def update_file_display(self, filepath=None):
        """Update the window title and file header to show current file."""
        if filepath:
            filename = os.path.basename(filepath)
            self.setWindowTitle(f"Safetensors Metadata Editor - {filename}")
            self.current_file_label.setText(filename)
            self.current_file = filepath
        else:
            self.setWindowTitle("Safetensors Metadata Editor")
            self.current_file_label.setText("No file loaded")
            self.current_file = None
            
    def set_modified(self, modified=True):
        """Update the modified indicator."""
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
    
  
    

    
    def setup_status_section(self, parent_layout):
        """Set up the status section."""
        # Status text area
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(80)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("Ready! Select a file to begin.")
        parent_layout.addWidget(self.status_text)
    
    def setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Open action
        open_action = QAction('Open File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.browse_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Load metadata action
        load_action = QAction('Load Metadata', self)
        load_action.setShortcut('Ctrl+L')
        load_action.triggered.connect(self.load_metadata)
        file_menu.addAction(load_action)
        
        # Save changes action
        save_action = QAction('Save Changes', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_changes)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        # Set thumbnail action
        set_thumb_action = QAction('Set Thumbnail...', self)
        set_thumb_action.setShortcut('Ctrl+T')
        set_thumb_action.triggered.connect(self.set_thumbnail)
        edit_menu.addAction(set_thumb_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # View thumbnail action
        view_thumb_action = QAction('View Thumbnail', self)
        view_thumb_action.setShortcut('Ctrl+Shift+T')
        view_thumb_action.triggered.connect(self.view_thumbnail)
        view_menu.addAction(view_thumb_action)
        
        view_menu.addSeparator()
        
        # Raw metadata action
        raw_action = QAction('Raw Metadata Editor', self)
        raw_action.setShortcut('Ctrl+R')
        raw_action.triggered.connect(self.toggle_raw_view)
        view_menu.addAction(raw_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_icon(self):
        """Set up the application icon."""
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'safetensors.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def browse_file(self):
        """Open file dialog to select a safetensors file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Safetensors File",
            "",
            "Safetensors Files (*.safetensors);;All Files (*)"
        )
        
        if file_path:
            self.filepath = file_path
            self.update_file_display(file_path)
            
            # Log file selection
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            self.add_status(f"Selected file: {os.path.basename(file_path)} ({file_size:.1f} MB)")
            logger.info(f"Selected file: {file_path} ({file_size:.1f} MB)")
    
    def load_metadata(self):
        """Load metadata from the selected file."""
        if not self.filepath:
            QMessageBox.warning(self, "Warning", "Please select a file first.")
            return
        
        try:
            # Use existing LoadMetadataCommand
            command = LoadMetadataCommand(self.filepath)
            self.metadata = command.execute()
            
            # Populate fields with loaded metadata
            self.populate_fields()
            
            self.add_status(f"Loaded metadata from: {os.path.basename(self.filepath)}")
            logger.info(f"Loaded metadata from: {self.filepath}")
            
        except Exception as e:
            error_msg = f"Error loading metadata: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)
    
    def populate_fields(self):
        """Populate the form fields with loaded metadata."""
        for field_name, widget in self.fields.items():
            mapped_key = MODELSPEC_KEY_MAP.get(field_name, field_name)
            value = self.metadata.get(mapped_key, "")
            
            if isinstance(widget, QTextEdit):
                widget.setPlainText(str(value))
            else:
                widget.setText(str(value))
    
    def save_changes(self):
        """Save changes to the metadata."""
        if not self.filepath:
            QMessageBox.warning(self, "Warning", "Please select a file first.")
            return
        
        try:
            # Collect data from fields
            updated_metadata = {}
            for field_name, widget in self.fields.items():
                if isinstance(widget, QTextEdit):
                    value = widget.toPlainText().strip()
                else:
                    value = widget.text().strip()
                
                if value:  # Only add non-empty values
                    mapped_key = MODELSPEC_KEY_MAP.get(field_name, field_name)
                    updated_metadata[mapped_key] = value
            
            # Use existing SaveCommand
            command = SaveCommand(self.filepath, updated_metadata)
            command.execute()
            
            self.add_status("Changes saved successfully!")
            logger.info("Changes saved successfully")
            
        except Exception as e:
            error_msg = f"Error saving changes: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)
    
    def set_thumbnail(self):
        """Set thumbnail for the model."""
        if not self.filepath:
            QMessageBox.warning(self, "Warning", "Please select a file first.")
            return
        
        try:
            # Use existing SetThumbnailCommand
            command = SetThumbnailCommand(self.filepath)
            command.execute()
            
            self.add_status("Thumbnail set successfully!")
            logger.info("Thumbnail set successfully")
            
        except Exception as e:
            error_msg = f"Error setting thumbnail: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)
    
    def view_thumbnail(self):
        """View the current thumbnail."""
        # TODO: Implement thumbnail viewer
        QMessageBox.information(self, "Info", "Thumbnail viewer not implemented yet.")
    
    def toggle_raw_view(self):
        """Toggle the raw metadata editor."""
        # TODO: Implement raw metadata editor
        QMessageBox.information(self, "Info", "Raw metadata editor not implemented yet.")
    
    def show_about(self):
        """Show about dialog."""
        # TODO: Implement about dialog
        QMessageBox.about(self, "About", "Safetensors Metadata Editor\nPyQt Version")
    
    def add_status(self, message):
        """Add a status message to the status area."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.status_text.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """Main entry point for the PyQt application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Safetensors Metadata Editor")
    app.setApplicationVersion("2.0")
    
    # Set application style
    app.setStyle('Fusion')  # Use Fusion style for consistent look across platforms
    
    editor = SafetensorsEditorPyQt()
    editor.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
