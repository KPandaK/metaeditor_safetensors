"""
Metadata View - View for editing metadata fields.
"""

import logging
from typing import Dict, Any, Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QScrollArea,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

logger = logging.getLogger(__name__)


class ThumbnailWidget(QWidget):
    """Custom widget for thumbnail display and management."""
    
    # Signals
    set_thumbnail_requested = Signal()
    view_thumbnail_requested = Signal()
    clear_thumbnail_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.thumbnail_data = None
        self._setup_ui()
    
    def _setup_ui(self):
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
        
        # Connect signals
        self.set_button.clicked.connect(self.set_thumbnail_requested.emit)
        self.view_button.clicked.connect(self.view_thumbnail_requested.emit)
        self.clear_button.clicked.connect(self._clear_thumbnail)
    
    def set_thumbnail_data(self, data: Optional[bytes]) -> None:
        """
        Set thumbnail data and update display.
        
        Args:
            data: Thumbnail image data
        """
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
    
    def get_thumbnail_data(self) -> Optional[bytes]:
        """Get current thumbnail data."""
        return self.thumbnail_data
    
    def _clear_thumbnail(self) -> None:
        """Clear the thumbnail."""
        self.set_thumbnail_data(None)
        self.clear_thumbnail_requested.emit()


class MetadataView(QWidget):
    """
    View for editing metadata fields.
    
    This view creates form fields dynamically based on field configuration
    and provides signals for change notifications.
    """
    
    # Signals
    field_changed = Signal(str, str)  # field_name, new_value
    
    def __init__(self, field_config=None):
        super().__init__()
        
        self.field_config = field_config
        self.field_widgets: Dict[str, QWidget] = {}
        
        self._setup_ui()
        
        logger.info("Metadata view initialized")
    
    def _setup_ui(self) -> None:
        """Set up the metadata editing UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for fields
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        self.form_layout = QFormLayout(scroll_widget)
        self.form_layout.setSpacing(5)
        
        # Create metadata fields if configuration is available
        if self.field_config:
            self._create_metadata_fields()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
    
    def _create_metadata_fields(self) -> None:
        """Create metadata form fields based on configuration."""
        self.field_widgets = {}
        
        for field_name in self.field_config.get_field_names():
            config = self.field_config.get_field_config(field_name)
            
            # Create label
            label = QLabel(f"{field_name}:")
            
            # Create widget based on configuration
            widget = self._create_widget_from_config(config)
            
            # Set tooltip from configuration
            tooltip = self.field_config.get_tooltip(field_name)
            if tooltip:
                widget.setToolTip(tooltip)
            
            # Connect change signals
            self._connect_widget_signals(field_name, widget)
            
            # Store reference to the widget
            self.field_widgets[field_name] = widget
            
            # Add to form layout
            self.form_layout.addRow(label, widget)
    
    def _create_widget_from_config(self, config: Dict[str, Any]) -> QWidget:
        """
        Create a widget based on field configuration.
        
        Args:
            config: Field configuration dictionary
            
        Returns:
            Appropriate widget for the field type
        """
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
    
    def _connect_widget_signals(self, field_name: str, widget: QWidget) -> None:
        """
        Connect widget signals to emit field change notifications.
        
        Args:
            field_name: Name of the field
            widget: Widget to connect
        """
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(
                lambda text: self.field_changed.emit(field_name, text)
            )
        elif isinstance(widget, QTextEdit):
            widget.textChanged.connect(
                lambda: self.field_changed.emit(field_name, widget.toPlainText())
            )
        elif isinstance(widget, ThumbnailWidget):
            # Thumbnail widgets will be handled separately
            pass
    
    def set_field_value(self, field_name: str, value: str) -> None:
        """
        Set the value of a field.
        
        Args:
            field_name: Name of the field
            value: Value to set
        """
        if field_name not in self.field_widgets:
            return
        
        widget = self.field_widgets[field_name]
        
        # Temporarily disconnect signals to avoid triggering change events
        self._disconnect_widget_signals(field_name, widget)
        
        try:
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(str(value))
            elif isinstance(widget, ThumbnailWidget):
                # Handle thumbnail data specially
                if value and isinstance(value, (str, bytes)):
                    if isinstance(value, str):
                        # Assume base64 encoded data
                        import base64
                        try:
                            data = base64.b64decode(value)
                            widget.set_thumbnail_data(data)
                        except Exception:
                            widget.set_thumbnail_data(None)
                    else:
                        widget.set_thumbnail_data(value)
                else:
                    widget.set_thumbnail_data(None)
        finally:
            # Reconnect signals
            self._connect_widget_signals(field_name, widget)
    
    def get_field_value(self, field_name: str) -> str:
        """
        Get the current value of a field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Current field value as string
        """
        if field_name not in self.field_widgets:
            return ""
        
        widget = self.field_widgets[field_name]
        
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QTextEdit):
            return widget.toPlainText()
        elif isinstance(widget, ThumbnailWidget):
            # Return thumbnail data as base64 string
            data = widget.get_thumbnail_data()
            if data:
                import base64
                return base64.b64encode(data).decode('utf-8')
            return ""
        
        return ""
    
    def _disconnect_widget_signals(self, field_name: str, widget: QWidget) -> None:
        """
        Disconnect widget signals temporarily.
        
        Args:
            field_name: Name of the field
            widget: Widget to disconnect
        """
        if isinstance(widget, QLineEdit):
            widget.textChanged.disconnect()
        elif isinstance(widget, QTextEdit):
            widget.textChanged.disconnect()
    
    def clear_all_fields(self) -> None:
        """Clear all field values."""
        for field_name in self.field_widgets:
            self.set_field_value(field_name, "")
    
    def set_field_enabled(self, field_name: str, enabled: bool) -> None:
        """
        Enable or disable a field.
        
        Args:
            field_name: Name of the field
            enabled: Whether to enable the field
        """
        if field_name in self.field_widgets:
            self.field_widgets[field_name].setEnabled(enabled)
    
    def set_all_fields_enabled(self, enabled: bool) -> None:
        """
        Enable or disable all fields.
        
        Args:
            enabled: Whether to enable all fields
        """
        for widget in self.field_widgets.values():
            widget.setEnabled(enabled)
    
    def get_thumbnail_widget(self) -> Optional[ThumbnailWidget]:
        """
        Get the thumbnail widget if it exists.
        
        Returns:
            ThumbnailWidget instance or None
        """
        for widget in self.field_widgets.values():
            if isinstance(widget, ThumbnailWidget):
                return widget
        return None
    
    def highlight_field_error(self, field_name: str, has_error: bool = True) -> None:
        """
        Highlight a field to indicate validation error.
        
        Args:
            field_name: Name of the field
            has_error: Whether to show error highlight
        """
        if field_name not in self.field_widgets:
            return
        
        widget = self.field_widgets[field_name]
        
        if has_error:
            widget.setStyleSheet("border: 2px solid red;")
        else:
            widget.setStyleSheet("")
