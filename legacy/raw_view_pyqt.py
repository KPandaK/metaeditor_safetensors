import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QAbstractItemView,
    QWidget, QLineEdit, QTextEdit, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QKeySequence, QShortcut

class RawMetadataEntryDialog(QDialog):
    """Dialog for adding/editing a single metadata entry."""
    
    def __init__(self, parent=None, title="Edit Entry", key="", value="", existing_keys=None, original_key=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 300)
        
        self.existing_keys = existing_keys or set()
        self.original_key = original_key
        self.result = None
        
        self.setup_ui(key, value)
    
    def setup_ui(self, key, value):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Form layout for key and value
        form_layout = QFormLayout()
        
        # Key field
        self.key_edit = QLineEdit(key)
        self.key_edit.setPlaceholderText("Enter key name...")
        form_layout.addRow("Key:", self.key_edit)
        
        # Value field
        self.value_edit = QTextEdit()
        self.value_edit.setPlainText(value)
        self.value_edit.setPlaceholderText("Enter value...")
        form_layout.addRow("Value:", self.value_edit)
        
        layout.addLayout(form_layout)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_entry)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus to key field
        self.key_edit.setFocus()
    
    def accept_entry(self):
        """Validate and accept the entry."""
        key = self.key_edit.text().strip()
        value = self.value_edit.toPlainText().strip()
        
        if not key:
            QMessageBox.warning(self, "Invalid Key", "Key cannot be empty.")
            return
        
        # Check for duplicate keys (unless it's the original key being edited)
        if key != self.original_key and key in self.existing_keys:
            QMessageBox.warning(self, "Duplicate Key", f"Key '{key}' already exists.")
            return
        
        self.result = (key, value)
        self.accept()


class RawMetadataEditorPyQt(QDialog):
    """PyQt-based raw metadata editor with proper table widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Raw Metadata Editor")
        self.setModal(True)
        self.resize(900, 600)
        
        self.metadata = {}
        self.metadata_change_callback = None
        
        self.setup_ui()
        self.setup_shortcuts()
    
    def setup_ui(self):
        """Set up the main UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Toolbar
        self.setup_toolbar(layout)
        
        # Table widget
        self.setup_table(layout)
        
        # Status bar
        self.setup_status_bar(layout)
    
    def setup_toolbar(self, parent_layout):
        """Set up the toolbar with action buttons."""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(5)
        
        # Action buttons
        add_button = QPushButton("Add Entry")
        add_button.clicked.connect(self.add_entry)
        toolbar_layout.addWidget(add_button)
        
        edit_button = QPushButton("Edit Entry")
        edit_button.clicked.connect(self.edit_entry)
        toolbar_layout.addWidget(edit_button)
        
        remove_button = QPushButton("Remove Entry")
        remove_button.clicked.connect(self.remove_entry)
        toolbar_layout.addWidget(remove_button)
        
        # Separator
        separator = QWidget()
        separator.setFixedWidth(20)
        toolbar_layout.addWidget(separator)
        
        # Help text
        help_label = QLabel("Double-click to edit • Del to remove • Ins/Ctrl+N to add")
        help_label.setStyleSheet("QLabel { color: gray; font-size: 9px; }")
        toolbar_layout.addWidget(help_label)
        
        # Stretch to push everything to the left
        toolbar_layout.addStretch()
        
        parent_layout.addLayout(toolbar_layout)
    
    def setup_table(self, parent_layout):
        """Set up the metadata table widget."""
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Key", "Value"])
        
        # Configure table behavior
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        # Configure column behavior
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Key column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Value column stretches
        
        # Enable word wrap in value column
        self.table.setWordWrap(True)
        
        # Connect double-click to edit
        self.table.cellDoubleClicked.connect(self.edit_entry)
        
        parent_layout.addWidget(self.table)
    
    def setup_status_bar(self, parent_layout):
        """Set up the status bar."""
        self.status_label = QLabel("Ready!")
        self.status_label.setStyleSheet("QLabel { padding: 5px; border: 1px solid gray; }")
        parent_layout.addWidget(self.status_label)
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Add entry shortcuts
        add_shortcut1 = QShortcut(QKeySequence("Ins"), self)
        add_shortcut1.activated.connect(self.add_entry)
        
        add_shortcut2 = QShortcut(QKeySequence("Ctrl+N"), self)
        add_shortcut2.activated.connect(self.add_entry)
        
        # Edit entry shortcut
        edit_shortcut = QShortcut(QKeySequence("F2"), self)
        edit_shortcut.activated.connect(self.edit_entry)
        
        # Remove entry shortcut
        remove_shortcut = QShortcut(QKeySequence("Del"), self)
        remove_shortcut.activated.connect(self.remove_entry)
    
    def open_with_metadata(self, metadata, change_callback=None):
        """Open the editor with the given metadata."""
        self.metadata = metadata.copy() if metadata else {}
        self.metadata_change_callback = change_callback
        
        self.populate_table()
        self.show()
    
    def populate_table(self):
        """Populate the table with metadata."""
        self.table.setRowCount(len(self.metadata))
        
        for row, (key, value) in enumerate(sorted(self.metadata.items())):
            # Key column
            key_item = QTableWidgetItem(str(key))
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
            self.table.setItem(row, 0, key_item)
            
            # Value column
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
            self.table.setItem(row, 1, value_item)
        
        # Resize rows to content
        self.table.resizeRowsToContents()
        
        # Update status
        self.set_status(f"Loaded {len(self.metadata)} metadata entries")
    
    def add_entry(self):
        """Add a new metadata entry."""
        dialog = RawMetadataEntryDialog(
            self, "Add New Entry", "", "", 
            existing_keys=set(self.metadata.keys())
        )
        
        if dialog.exec() and dialog.result:
            key, value = dialog.result
            self.metadata[key] = value
            self.populate_table()
            self.update_parent_metadata()
            self.set_status(f"Added '{key}'")
    
    def edit_entry(self):
        """Edit the selected metadata entry."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a metadata entry to edit.")
            return
        
        # Get current key and value
        key_item = self.table.item(current_row, 0)
        value_item = self.table.item(current_row, 1)
        
        if not key_item or not value_item:
            return
        
        current_key = key_item.text()
        current_value = value_item.text()
        
        dialog = RawMetadataEntryDialog(
            self, "Edit Entry", current_key, current_value,
            existing_keys=set(self.metadata.keys()),
            original_key=current_key
        )
        
        if dialog.exec() and dialog.result:
            new_key, new_value = dialog.result
            
            # Remove old key if changed
            if new_key != current_key:
                del self.metadata[current_key]
            
            # Set new value
            self.metadata[new_key] = new_value
            
            self.populate_table()
            self.update_parent_metadata()
            
            if new_key != current_key:
                self.set_status(f"Renamed '{current_key}' to '{new_key}' and updated value")
            else:
                self.set_status(f"Updated value for '{new_key}'")
    
    def remove_entry(self):
        """Remove the selected metadata entry."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a metadata entry to remove.")
            return
        
        key_item = self.table.item(current_row, 0)
        if not key_item:
            return
        
        key = key_item.text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to remove '{key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.metadata[key]
            self.populate_table()
            self.update_parent_metadata()
            self.set_status(f"Removed entry: {key}")
    
    def update_parent_metadata(self):
        """Update the parent's metadata via callback."""
        if self.metadata_change_callback:
            self.metadata_change_callback(self.metadata)
    
    def set_status(self, message):
        """Set the status message."""
        self.status_label.setText(message)


# Test the raw metadata editor standalone
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test data
    test_metadata = {
        "modelspec.architecture": "stable-diffusion-xl-v1-base",
        "modelspec.author": "Test Author",
        "modelspec.description": "This is a test model for demonstration purposes",
        "modelspec.license": "CreativeML Open RAIL++-M License"
    }
    
    editor = RawMetadataEditorPyQt()
    editor.open_with_metadata(test_metadata)
    
    sys.exit(app.exec())
