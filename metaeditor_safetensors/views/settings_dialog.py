import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..services.config_service import ConfigService
from ..services.theme_manager import ThemeManager, ThemeType

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    theme_changed = Signal(str)  # theme identifier
    settings_applied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Store references
        self._theme_service: Optional[ThemeManager] = None
        self._config_service: Optional[ConfigService] = None
        self._original_settings = {}

        # Set up UI
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the user interface programmatically."""
        # Set window properties
        self.setWindowTitle("MetaEditor SafeTensors - Settings")
        self.setModal(True)
        self.resize(500, 400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Theme tab
        self._setup_theme_tab()

        # General tab (placeholder)
        self._setup_general_tab()

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        main_layout.addWidget(self.button_box)

    def _setup_theme_tab(self):
        """Set up the theme configuration tab."""
        theme_tab = QWidget()
        theme_layout = QVBoxLayout(theme_tab)

        # Theme selection group
        theme_selection_group = QGroupBox("Theme Selection")
        theme_group_layout = QVBoxLayout(theme_selection_group)

        # Create radio buttons
        self.auto_theme_radio = QRadioButton("Auto (Follow System Theme)")
        self.auto_theme_radio.setChecked(True)
        self.light_theme_radio = QRadioButton("Light Theme")
        self.dark_theme_radio = QRadioButton("Dark Theme")
        self.custom_theme_radio = QRadioButton("Custom Theme")

        theme_group_layout.addWidget(self.auto_theme_radio)
        theme_group_layout.addWidget(self.light_theme_radio)
        theme_group_layout.addWidget(self.dark_theme_radio)
        theme_group_layout.addWidget(self.custom_theme_radio)

        theme_layout.addWidget(theme_selection_group)

        # Theme details group
        theme_details_group = QGroupBox("Theme Details")
        theme_details_layout = QVBoxLayout(theme_details_group)

        theme_selection_label = QLabel("Select specific theme:")
        theme_details_layout.addWidget(theme_selection_label)

        self.theme_combo_box = QComboBox()
        self.theme_combo_box.setEnabled(False)
        theme_details_layout.addWidget(self.theme_combo_box)

        theme_layout.addWidget(theme_details_group)

        # Theme info group
        theme_info_group = QGroupBox("Current Theme Information")
        theme_info_layout = QFormLayout(theme_info_group)

        self.current_theme_value = QLabel("Auto (System Default)")
        self.system_theme_value = QLabel("Light")

        theme_info_layout.addRow("Current Theme:", self.current_theme_value)
        theme_info_layout.addRow("System Theme:", self.system_theme_value)

        theme_layout.addWidget(theme_info_group)

        # Add spacer
        theme_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        theme_layout.addItem(theme_spacer)

        self.tab_widget.addTab(theme_tab, "Theme")

        # Create button group for theme mode selection
        self._theme_mode_group = QButtonGroup(self)
        self._theme_mode_group.addButton(self.auto_theme_radio, 0)
        self._theme_mode_group.addButton(self.light_theme_radio, 1)
        self._theme_mode_group.addButton(self.dark_theme_radio, 2)
        self._theme_mode_group.addButton(self.custom_theme_radio, 3)

    def _setup_general_tab(self):
        """Set up the general settings tab (placeholder)."""
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        general_placeholder = QLabel(
            "General settings will be added in future versions."
        )
        general_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        general_layout.addWidget(general_placeholder)

        # Add spacer
        general_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        general_layout.addItem(general_spacer)

        self.tab_widget.addTab(general_tab, "General")

    def _connect_signals(self):
        # Theme mode changes
        self._theme_mode_group.buttonToggled.connect(self._on_theme_mode_changed)

        # Theme selection changes
        self.theme_combo_box.currentTextChanged.connect(self._on_specific_theme_changed)

        # Button box
        self.button_box.clicked.connect(self._on_button_clicked)

    def set_services(self, theme_service: ThemeManager, config_service: ConfigService):
        self._theme_service = theme_service
        self._config_service = config_service
        self._populate_theme_options()
        self._load_current_settings()

    def _populate_theme_options(self):
        if not self._theme_service:
            return

        self.theme_combo_box.clear()

        # Since PyQtDarkTheme only has 3 built-in themes (auto, dark, light),
        # and these are already covered by the radio buttons,
        # we'll disable the combo box for now or use it for future custom themes
        self.theme_combo_box.addItem("No additional themes available", None)
        self.theme_combo_box.setEnabled(False)

    def _load_current_settings(self):
        if not self._config_service:
            return

        # Get current preference from config service
        current_preference = self._config_service.get_theme_preference()

        # Store original settings
        self._original_settings = {"theme_preference": current_preference}

        # Set UI state based on current preference
        if current_preference == ThemeType.SYSTEM:
            self.auto_theme_radio.setChecked(True)
        elif current_preference == ThemeType.LIGHT:
            self.light_theme_radio.setChecked(True)
        elif current_preference == ThemeType.DARK:
            self.dark_theme_radio.setChecked(True)
        else:
            # Unknown theme - default to system
            self.auto_theme_radio.setChecked(True)

        # Update theme info display
        self._update_theme_info()

    def _update_theme_info(self):
        """Update the current theme information display."""
        if not self._theme_service:
            return

        current_theme = self._theme_service.get_current_theme()
        system_theme = self._theme_service._detect_system_theme()

        if current_theme:
            self.current_theme_value.setText(current_theme.name)
        else:
            self.current_theme_value.setText("Unknown")

        self.system_theme_value.setText(system_theme.value.title())

    def _on_theme_mode_changed(self, button, checked):
        """Handle theme mode radio button changes."""
        if not checked:
            return

        # Since we only have 3 themes (auto, light, dark), always keep combo box disabled
        self.theme_combo_box.setEnabled(False)
        self._preview_theme_selection()

    def _on_specific_theme_changed(self):
        """Handle specific theme selection changes."""
        if self.custom_theme_radio.isChecked():
            self._preview_theme_selection()

    def _preview_theme_selection(self):
        """Preview the selected theme immediately (not saved until OK is clicked)."""
        if not self._theme_service:
            return

        theme_identifier = self._get_selected_theme_identifier()
        if theme_identifier:
            self._theme_service.apply_theme(
                theme_identifier.value
            )  # Use string value for ThemeManager
            self._update_theme_info()

    def _get_selected_theme_identifier(self) -> Optional[ThemeType]:
        """Get the currently selected theme identifier."""
        if self.auto_theme_radio.isChecked():
            return ThemeType.SYSTEM
        elif self.light_theme_radio.isChecked():
            return ThemeType.LIGHT
        elif self.dark_theme_radio.isChecked():
            return ThemeType.DARK
        elif self.custom_theme_radio.isChecked():
            # For now, default to system since we don't have custom themes
            return ThemeType.SYSTEM
        return None

    def _on_button_clicked(self, button):
        """Handle button box clicks."""
        role = self.button_box.buttonRole(button)

        if role == QDialogButtonBox.ButtonRole.AcceptRole:
            # OK button: Save current preview as permanent setting
            self._save_settings()
            self.accept()
        elif role == QDialogButtonBox.ButtonRole.RejectRole:
            # Cancel button: Revert to original theme
            self._revert_settings()
            self.reject()

    def _save_settings(self):
        if not self._config_service:
            return

        theme_identifier = self._get_selected_theme_identifier()
        if theme_identifier:
            self.theme_changed.emit(
                theme_identifier.value
            )  # Emit string value for ThemeManager
            self.settings_applied.emit()

            # Update original settings for future cancel operations
            self._original_settings["theme_preference"] = (
                theme_identifier.value if theme_identifier else None
            )

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
