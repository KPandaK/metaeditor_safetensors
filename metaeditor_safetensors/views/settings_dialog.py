"""
Settings Dialog
===============

A dialog for configuring application settings including themes,
preferences, and other user options.
"""

import logging
from typing import Optional, Dict, Any
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QDialog, QButtonGroup

from .settings_dialog_ui import Ui_SettingsDialog
from ..services.theme_service import ThemeService, ThemeCategory, MaterialTheme

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """
    Settings dialog for configuring application preferences.
    
    Signals:
        theme_changed: Emitted when theme selection changes
        settings_applied: Emitted when settings are applied
    """
    
    theme_changed = Signal(str)  # theme identifier
    settings_applied = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)
        
        # Store references
        self._theme_service: Optional[ThemeService] = None
        self._original_settings = {}
        
        # Create button group for theme mode selection
        self._theme_mode_group = QButtonGroup(self)
        self._theme_mode_group.addButton(self.ui.autoThemeRadio, 0)
        self._theme_mode_group.addButton(self.ui.lightThemeRadio, 1) 
        self._theme_mode_group.addButton(self.ui.darkThemeRadio, 2)
        self._theme_mode_group.addButton(self.ui.customThemeRadio, 3)
        
        # Connect signals
        self._connect_signals()
        
        # Initialize UI state
        self._setup_ui()
    
    def _connect_signals(self):
        """Connect internal UI signals."""
        # Theme mode changes
        self._theme_mode_group.buttonToggled.connect(self._on_theme_mode_changed)
        
        # Theme selection changes
        self.ui.themeComboBox.currentTextChanged.connect(self._on_specific_theme_changed)
        
        # Button box
        self.ui.buttonBox.clicked.connect(self._on_button_clicked)
    
    def _setup_ui(self):
        """Initialize the UI state."""
        # Set initial state
        self.ui.autoThemeRadio.setChecked(True)
        self.ui.themeComboBox.setEnabled(False)
        
        # Set window properties
        self.setWindowTitle("MetaEditor SafeTensors - Settings")
        self.setModal(True)
    
    def set_theme_service(self, theme_service: ThemeService):
        """Set the theme service and populate theme options."""
        self._theme_service = theme_service
        self._populate_theme_options()
        self._load_current_settings()
    
    def _populate_theme_options(self):
        """Populate the theme combo box with available themes."""
        if not self._theme_service:
            return
            
        self.ui.themeComboBox.clear()
        
        # Get all themes organized by category
        all_themes = self._theme_service.get_available_themes()
        categories = [ThemeCategory.LIGHT, ThemeCategory.DARK]
        
        for category in categories:
            # Add category separator
            if self.ui.themeComboBox.count() > 0:
                self.ui.themeComboBox.insertSeparator(self.ui.themeComboBox.count())
                
            # Add themes in this category
            category_themes = [theme for theme in all_themes.values() 
                             if theme.category == category]
            category_themes.sort(key=lambda t: t.display_name)
            
            for theme in category_themes:
                self.ui.themeComboBox.addItem(theme.display_name, theme.filename)
    
    def _load_current_settings(self):
        """Load current settings from the theme service."""
        if not self._theme_service:
            return
            
        # Get current preference
        if hasattr(self._theme_service, '_config_service') and self._theme_service._config_service:
            current_preference = self._theme_service._config_service.get_theme_preference()
        else:
            current_preference = 'auto'
            
        # Store original settings
        self._original_settings = {
            'theme_preference': current_preference
        }
        
        # Set UI state based on current preference
        if current_preference == 'auto':
            self.ui.autoThemeRadio.setChecked(True)
        elif current_preference in ['system_light', 'light']:
            self.ui.lightThemeRadio.setChecked(True)
        elif current_preference in ['system_dark', 'dark']:
            self.ui.darkThemeRadio.setChecked(True)
        else:
            # Custom theme
            self.ui.customThemeRadio.setChecked(True)
            # Find and select the current theme in combo box
            for i in range(self.ui.themeComboBox.count()):
                if self.ui.themeComboBox.itemData(i) == current_preference:
                    self.ui.themeComboBox.setCurrentIndex(i)
                    break
        
        # Update theme info display
        self._update_theme_info()
    
    def _update_theme_info(self):
        """Update the current theme information display."""
        if not self._theme_service:
            return
            
        current_theme = self._theme_service.get_current_theme()
        system_theme = self._theme_service._detect_system_theme()
        
        if current_theme:
            self.ui.currentThemeValue.setText(current_theme.display_name)
        else:
            self.ui.currentThemeValue.setText("Unknown")
            
        self.ui.systemThemeValue.setText(system_theme.value.title())
    
    def _on_theme_mode_changed(self, button, checked):
        """Handle theme mode radio button changes."""
        if not checked:
            return
            
        button_id = self._theme_mode_group.id(button)
        
        if button_id == 0:  # Auto
            self.ui.themeComboBox.setEnabled(False)
        elif button_id == 1:  # Light
            self.ui.themeComboBox.setEnabled(False)
        elif button_id == 2:  # Dark
            self.ui.themeComboBox.setEnabled(False)
        elif button_id == 3:  # Custom
            self.ui.themeComboBox.setEnabled(True)
            
        # Update preview if we have a theme service
        self._preview_theme_selection()
    
    def _on_specific_theme_changed(self):
        """Handle specific theme selection changes."""
        if self.ui.customThemeRadio.isChecked():
            self._preview_theme_selection()
    
    def _preview_theme_selection(self):
        """Preview the selected theme immediately (not saved until OK is clicked)."""
        if not self._theme_service:
            return
            
        theme_identifier = self._get_selected_theme_identifier()
        if theme_identifier:
            # Apply theme without saving preference
            self._theme_service.apply_theme(theme_identifier, save_preference=False)
            self._update_theme_info()
    
    def _get_selected_theme_identifier(self) -> Optional[str]:
        """Get the currently selected theme identifier."""
        if self.ui.autoThemeRadio.isChecked():
            return 'auto'
        elif self.ui.lightThemeRadio.isChecked():
            return 'system_light'
        elif self.ui.darkThemeRadio.isChecked():
            return 'system_dark'
        elif self.ui.customThemeRadio.isChecked():
            current_index = self.ui.themeComboBox.currentIndex()
            if current_index >= 0:
                return self.ui.themeComboBox.itemData(current_index)
        return None
    
    def _on_button_clicked(self, button):
        """Handle button box clicks."""
        role = self.ui.buttonBox.buttonRole(button)
        
        if role == self.ui.buttonBox.AcceptRole:
            # OK button: Save current preview as permanent setting
            self._save_settings()
            self.accept()
        elif role == self.ui.buttonBox.RejectRole:
            # Cancel button: Revert to original theme
            self._revert_settings()
            self.reject()
    
    def _save_settings(self):
        """Save the current preview settings as permanent."""
        if not self._theme_service:
            return
            
        theme_identifier = self._get_selected_theme_identifier()
        if theme_identifier:
            # Save the theme preference (theme is already applied for preview)
            if hasattr(self._theme_service, '_config_service') and self._theme_service._config_service:
                self._theme_service._config_service.set_theme_preference(theme_identifier)
                
            self.theme_changed.emit(theme_identifier)
            self.settings_applied.emit()
            
            # Update original settings for future cancel operations
            self._original_settings['theme_preference'] = theme_identifier
            
            logger.info(f"Saved theme preference: {theme_identifier}")
    
    def _revert_settings(self):
        """Revert to original settings."""
        if not self._theme_service or not self._original_settings:
            return
            
        original_theme = self._original_settings.get('theme_preference')
        if original_theme:
            # Revert without saving
            self._theme_service.apply_theme(original_theme, save_preference=False)
            logger.debug(f"Reverted to original theme: {original_theme}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        self._revert_settings()
        super().closeEvent(event)
