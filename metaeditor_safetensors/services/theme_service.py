"""
Theme Management Service
========================

Service for managing application themes with custom QSS files,
system theme detection, user preferences, and runtime theme switching.
Supports QSS inheritance where themes can extend base styles.
"""

import logging
import os
import platform
from enum import Enum
from typing import Any, Dict, List, Optional

import darkdetect
from PySide6.QtCore import QFile, QFileSystemWatcher, QIODevice, QObject, Signal
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class SystemTheme(Enum):
    """System theme preference enumeration."""

    LIGHT = "light"
    DARK = "dark"
    UNKNOWN = "unknown"


class ThemeCategory(Enum):
    """Theme category enumeration."""

    AUTO = "auto"  # Use system theme
    LIGHT = "light"  # Light theme
    DARK = "dark"  # Dark theme


class CustomTheme:
    """Represents a custom QSS theme configuration."""

    def __init__(
        self,
        theme_id: str,
        display_name: str,
        category: ThemeCategory,
        qss_file: str,
    ):
        self.theme_id = theme_id
        self.display_name = display_name
        self.category = category
        self.qss_file = qss_file  # Path to QSS file in resources

    def __str__(self):
        return f"{self.display_name} ({self.theme_id})"

    def __repr__(self):
        return f"CustomTheme('{self.theme_id}', '{self.display_name}', {self.category})"


class ThemeService(QObject):
    """
    Service for managing application themes.

    Integrates PyQtDarkTheme with system theme detection and provides
    runtime theme switching capabilities.
    """

    # Signals
    theme_changed = Signal(str)  # Emitted when theme changes, passes theme ID

    def __init__(self, app: QApplication, config_service=None):
        super().__init__()
        self._app = app
        self._config_service = config_service
        self._cached_system_theme: Optional[SystemTheme] = None
        self._current_theme: Optional[ModernTheme] = None
        self._available_themes: Dict[str, ModernTheme] = {}

        # Development mode settings
        self._enable_live_reload = (
            os.getenv("DEV_LIVE_STYLING", "false").lower() == "true"
        )
        self._file_watcher: Optional[QFileSystemWatcher] = None

        # Initialize available themes
        self._initialize_themes()

        # Setup file watching if in development mode
        if self._enable_live_reload:
            self._setup_file_watcher()

        logger.info("ThemeService initialized with PyQtDarkTheme")

    def _initialize_themes(self):
        """Initialize the available theme catalog."""
        logger.debug("Initializing modern theme catalog")

        # Define available themes - only the ones that actually come with PyQtDarkTheme
        themes = [
            # Auto theme (follows system)
            ModernTheme("auto", "Auto (Use System)", ThemeCategory.AUTO, "auto"),
            # Built-in PyQtDarkTheme themes
            ModernTheme("dark", "Dark", ThemeCategory.DARK, "dark"),
            ModernTheme("light", "Light", ThemeCategory.LIGHT, "light"),
        ]

        # Add themes to catalog
        for theme in themes:
            self._available_themes[theme.theme_id] = theme

        logger.info(f"Initialized {len(self._available_themes)} PyQtDarkTheme themes")

    def _load_theme_overrides(self) -> str:
        """Load the theme overrides QSS from resources or filesystem."""
        # In development mode, try to load from filesystem first for live reloading
        if self._enable_live_reload:
            try:
                filesystem_path = "assets/theme-overrides.qss"
                if os.path.exists(filesystem_path):
                    with open(filesystem_path, "r", encoding="utf-8") as f:
                        qss_content = f.read()
                        logger.debug(
                            "Loaded theme overrides from filesystem (dev mode)"
                        )
                        return qss_content
            except Exception as e:
                logger.debug(
                    f"Could not load from filesystem, falling back to resources: {e}"
                )

        # Load from compiled resources (production mode)
        try:
            qss_file = QFile(":/assets/theme-overrides.qss")
            if qss_file.open(
                QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text
            ):
                qss_content = bytes(qss_file.readAll().data()).decode("utf-8")
                qss_file.close()
                logger.debug("Loaded theme overrides from resources")
                return qss_content
            else:
                logger.warning("Could not load theme overrides from resources")
                return ""
        except Exception as e:
            logger.error(f"Error loading theme overrides: {e}")
            return ""

    def _setup_file_watcher(self):
        """Setup file watching for live reload in development mode."""
        filesystem_path = "assets/theme-overrides.qss"
        if not os.path.exists(filesystem_path):
            logger.debug(
                f"Theme overrides file not found for watching: {filesystem_path}"
            )
            return

        self._file_watcher = QFileSystemWatcher([filesystem_path])
        self._file_watcher.fileChanged.connect(self._on_theme_file_changed)
        logger.info(f"Live theme reloading enabled, watching: {filesystem_path}")

    def _on_theme_file_changed(self):
        """Handle theme file changes for live reloading."""
        logger.debug("Theme overrides file changed, reloading...")
        if self._current_theme:
            # Re-apply the current theme to pick up CSS changes
            self._apply_modern_theme(self._current_theme, save_preference=False)

    def _detect_system_theme(self, use_cache: bool = True) -> SystemTheme:
        """
        Detect the current system theme preference.

        Args:
            use_cache: If True, return cached result if available

        Returns:
            SystemTheme enum value (LIGHT, DARK, or UNKNOWN)
        """
        if use_cache and self._cached_system_theme is not None:
            return self._cached_system_theme

        try:
            # Use darkdetect to detect system theme
            theme_str = darkdetect.theme()

            if theme_str is None:
                logger.warning("darkdetect returned None, theme detection failed")
                theme = SystemTheme.UNKNOWN
            elif theme_str.lower() == "dark":
                theme = SystemTheme.DARK
            elif theme_str.lower() == "light":
                theme = SystemTheme.LIGHT
            else:
                logger.warning(f"darkdetect returned unexpected value: {theme_str}")
                theme = SystemTheme.UNKNOWN

        except Exception as e:
            logger.error(f"Error detecting system theme: {e}")
            theme = SystemTheme.UNKNOWN

        self._cached_system_theme = theme
        logger.info(f"Detected system theme: {theme.value}")
        return theme

    def _clear_system_theme_cache(self):
        """Clear the cached system theme detection result."""
        self._cached_system_theme = None
        logger.debug("System theme detection cache cleared")

    def _get_platform_info(self) -> dict:
        """
        Get platform information for debugging.

        Returns:
            Dictionary with platform information
        """
        return {
            "platform": platform.system().lower(),
            "platform_detailed": platform.platform(),
            "python_version": platform.python_version(),
            "darkdetect_available": True,  # We imported it successfully
            "qdarktheme_version": getattr(qdarktheme, "__version__", "unknown"),
        }

    def get_available_themes(self) -> Dict[str, ModernTheme]:
        """Get all available themes."""
        return self._available_themes.copy()

    def get_themes_by_category(self, category: ThemeCategory) -> List[ModernTheme]:
        """Get themes filtered by category."""
        return [
            theme
            for theme in self._available_themes.values()
            if theme.category == category
        ]

    def get_theme_categories(self) -> List[ThemeCategory]:
        """Get all available theme categories."""
        return list(ThemeCategory)

    def get_current_theme(self) -> Optional[ModernTheme]:
        """Get the currently applied theme."""
        return self._current_theme

    def apply_theme(self, theme_identifier: str, save_preference: bool = True) -> bool:
        """
        Apply a theme to the application.

        Args:
            theme_identifier: Theme ID from available themes
            save_preference: Whether to save this choice to config

        Returns:
            True if theme was applied successfully
        """
        logger.debug(f"Applying theme: {theme_identifier}")

        try:
            theme = self._available_themes.get(theme_identifier)
            if not theme:
                logger.error(f"Theme not found: {theme_identifier}")
                return False

            return self._apply_modern_theme(theme, save_preference)

        except Exception as e:
            logger.error(f"Error applying theme {theme_identifier}: {e}")
            return False

    def _apply_modern_theme(
        self, theme: ModernTheme, save_preference: bool = True
    ) -> bool:
        """Apply a PyQtDarkTheme configuration."""
        try:
            logger.debug(f"Applying modern theme: {theme}")

            # Load additional QSS from resources
            additional_qss = self._load_theme_overrides()

            # Apply the theme using qdarktheme with additional CSS
            qdarktheme.setup_theme(
                theme=theme.theme_mode,
                corner_shape=theme.corner_shape,
                custom_colors=theme.custom_colors if theme.custom_colors else None,
                additional_qss=additional_qss,
            )

            self._current_theme = theme

            # Save preference if requested
            if save_preference and self._config_service:
                self._config_service.set_theme_preference(theme.theme_id)

            # Emit signal
            self.theme_changed.emit(theme.theme_id)

            logger.info(f"Successfully applied theme: {theme.display_name}")
            return True

        except Exception as e:
            logger.error(f"Error applying modern theme {theme}: {e}")
            return False

    def apply_user_preference(self) -> bool:
        """
        Apply theme based on user preference from config.

        Returns:
            True if theme was applied successfully
        """
        if not self._config_service:
            logger.warning("No config service available, applying auto theme")
            return self.apply_theme("auto", False)

        try:
            preferred_theme = self._config_service.get_theme_preference()
            if preferred_theme and preferred_theme in self._available_themes:
                return self.apply_theme(preferred_theme, False)  # Don't re-save
            else:
                logger.debug("No valid theme preference found, applying auto theme")
                return self.apply_theme("auto", True)  # Save the auto preference

        except Exception as e:
            logger.error(f"Error applying user preference: {e}")
            return self.apply_theme("auto", True)

    def refresh_system_theme(self) -> bool:
        """
        Refresh system theme detection and re-apply auto theme if currently using it.

        Returns:
            True if refresh was successful
        """
        self._clear_system_theme_cache()

        # If current preference is auto, re-apply it
        if (
            self._config_service
            and self._config_service.get_theme_preference() == "auto"
        ):
            return self.apply_theme("auto", False)

        return True

    def get_theme_info(self) -> Dict[str, Any]:
        """
        Get comprehensive theme information for debugging.

        Returns:
            Dictionary with theme information
        """
        current_theme_info = None
        if self._current_theme:
            current_theme_info = {
                "theme_id": self._current_theme.theme_id,
                "display_name": self._current_theme.display_name,
                "category": self._current_theme.category.value,
                "theme_mode": self._current_theme.theme_mode,
                "custom_colors": self._current_theme.custom_colors,
                "corner_shape": self._current_theme.corner_shape,
            }

        return {
            "current_theme": current_theme_info,
            "available_themes": len(self._available_themes),
            "system_theme": self._detect_system_theme().value,
            "user_preference": (
                self._config_service.get_theme_preference()
                if self._config_service
                else None
            ),
            "categories": [cat.value for cat in self.get_theme_categories()],
            "platform_info": self._get_platform_info(),
        }
