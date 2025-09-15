import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QDialog, QDialogButtonBox

from ..models.theme import ThemeType
from ..services.config_service import ConfigService
from ..services.theme_service import ThemeService
from .settings_dialog_ui import Ui_SettingsDialog

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    theme_changed = Signal(str)  # theme identifier
    settings_applied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)

        # Store references
        self._theme_service: Optional[ThemeService] = None
        self._config_service: Optional[ConfigService] = None
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
        # Theme mode changes
        self._theme_mode_group.buttonToggled.connect(self._on_theme_mode_changed)

        # Theme selection changes
        self.ui.themeComboBox.currentTextChanged.connect(
            self._on_specific_theme_changed
        )

        # Button box
        self.ui.buttonBox.clicked.connect(self._on_button_clicked)

    def _setup_ui(self):
        # Set initial state
        self.ui.autoThemeRadio.setChecked(True)
        self.ui.themeComboBox.setEnabled(False)

        # Set window properties
        self.setWindowTitle("MetaEditor SafeTensors - Settings")
        self.setModal(True)

    def set_services(self, theme_service: ThemeService, config_service: ConfigService):
        self._theme_service = theme_service
        self._config_service = config_service
        self._populate_theme_options()
        self._load_current_settings()

    def _populate_theme_options(self):
        if not self._theme_service:
            return

        self.ui.themeComboBox.clear()

        # Since PyQtDarkTheme only has 3 built-in themes (auto, dark, light),
        # and these are already covered by the radio buttons,
        # we'll disable the combo box for now or use it for future custom themes
        self.ui.themeComboBox.addItem("No additional themes available", None)
        self.ui.themeComboBox.setEnabled(False)

    def _load_current_settings(self):
        if not self._config_service:
            return

        # Get current preference from config service
        current_preference = self._config_service.get_theme_preference()

        # Store original settings
        self._original_settings = {"theme_preference": current_preference}

        # Set UI state based on current preference
        if current_preference == ThemeType.SYSTEM:
            self.ui.autoThemeRadio.setChecked(True)
        elif current_preference == ThemeType.LIGHT:
            self.ui.lightThemeRadio.setChecked(True)
        elif current_preference == ThemeType.DARK:
            self.ui.darkThemeRadio.setChecked(True)
        else:
            # Unknown theme - default to system
            self.ui.autoThemeRadio.setChecked(True)

        # Update theme info display
        self._update_theme_info()

    def _update_theme_info(self):
        """Update the current theme information display."""
        if not self._theme_service:
            return

        current_theme = self._theme_service.get_current_theme()
        system_theme = self._theme_service._detect_system_theme()

        if current_theme:
            self.ui.currentThemeValue.setText(current_theme.name)
        else:
            self.ui.currentThemeValue.setText("Unknown")

        self.ui.systemThemeValue.setText(system_theme.value.title())

    def _on_theme_mode_changed(self, button, checked):
        """Handle theme mode radio button changes."""
        if not checked:
            return

        # Since we only have 3 themes (auto, light, dark), always keep combo box disabled
        self.ui.themeComboBox.setEnabled(False)
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
            self._theme_service.apply_theme(
                theme_identifier.value
            )  # Use string value for ThemeService
            self._update_theme_info()

    def _get_selected_theme_identifier(self) -> Optional[ThemeType]:
        """Get the currently selected theme identifier."""
        if self.ui.autoThemeRadio.isChecked():
            return ThemeType.SYSTEM
        elif self.ui.lightThemeRadio.isChecked():
            return ThemeType.LIGHT
        elif self.ui.darkThemeRadio.isChecked():
            return ThemeType.DARK
        elif self.ui.customThemeRadio.isChecked():
            # For now, default to system since we don't have custom themes
            return ThemeType.SYSTEM
        return None

    def _on_button_clicked(self, button):
        """Handle button box clicks."""
        role = self.ui.buttonBox.buttonRole(button)

        if role == QDialogButtonBox.ButtonRole.AcceptRole:
            # OK button: Save current preview as permanent setting
            self._save_settings()
            self.accept()
        elif role == QDialogButtonBox.ButtonRole.RejectRole:
            # Cancel button: Revert to original theme
            self._revert_settings()
            self.reject()

    def _save_settings(self):
        """Save the current preview settings as permanent."""
        if not self._config_service:
            return

        theme_identifier = self._get_selected_theme_identifier()
        if theme_identifier:
            self.theme_changed.emit(
                theme_identifier.value
            )  # Emit string value for ThemeService
            self.settings_applied.emit()

            # Update original settings for future cancel operations
            self._original_settings["theme_preference"] = theme_identifier

            logger.info(f"Saved theme preference: {theme_identifier}")

    def _revert_settings(self):
        """Revert to original settings."""
        if not self._theme_service or not self._original_settings:
            return

        original_theme = self._original_settings.get("theme_preference")
        if original_theme:
            self._theme_service.apply_theme(
                original_theme
            )  # Apply theme by theme_id string
            logger.debug(f"Reverted to original theme: {original_theme}")

    def closeEvent(self, event):
        """Handle dialog close event."""
        self._revert_settings()
        super().closeEvent(event)
