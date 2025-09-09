"""
Theme Management Service
========================

Service for managing application themes with modular QSS files,
system theme detection, user preferences, and runtime theme switching.
"""

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import darkdetect
import yaml
from PySide6.QtCore import QFileSystemWatcher, QObject, Signal
from PySide6.QtWidgets import QApplication

from ..models.theme import Theme
from .file_service import get_package_root

logger = logging.getLogger(__name__)


class SystemTheme(Enum):
    """System theme preference enumeration."""

    LIGHT = "light"
    DARK = "dark"
    UNKNOWN = "unknown"


class ThemeService(QObject):
    """
    Service for managing application themes with modular QSS files.

    Supports theme directories containing multiple QSS files that are
    combined at runtime, with system theme detection and live reloading
    in development mode.
    """

    # Signals
    theme_changed = Signal(str)

    def __init__(self, app: QApplication, config_service=None):
        super().__init__()
        self._app = app
        self._config_service = config_service
        self._cached_system_theme: Optional[SystemTheme] = None
        self._current_theme: Optional[Theme] = None
        self._available_themes: Dict[str, Theme] = {}
        self._themes_root: Optional[Path] = None

        # Themes directory - always in the package
        try:
            package_root = get_package_root()
            self._themes_root = package_root / "themes"
        except Exception:
            logger.warning("Could not determine package root for themes directory")
            self._themes_root = None

        self._enable_live_reload = (
            os.getenv("DEV_LIVE_STYLING", "false").lower() == "true"
        )

        self._file_watcher: Optional[QFileSystemWatcher] = None
        self._watched_files: List[str] = []

        # Initialize available themes
        self._initialize_themes()

        # Setup file watching if in development mode
        if self._enable_live_reload:
            self._setup_file_watcher()

        mode = "dev" if self._enable_live_reload else "prod"
        logger.info(f"ThemeService initialized in {mode} mode")

    def _initialize_themes(self):
        """Find available themes from the package themes directory."""
        logger.debug("Searching for themes")

        # Auto theme (follows system)
        auto_theme = Theme("auto", "Auto (Use System)", "", None)
        self._available_themes["auto"] = auto_theme

        # Scan for themes from package
        if not self._themes_root or not self._themes_root.exists():
            logger.warning(f"Themes directory not found: {self._themes_root}")
            return

        for theme_dir in self._themes_root.iterdir():
            if theme_dir.is_dir() and not theme_dir.name.startswith("__"):
                try:
                    theme = Theme.from_directory(theme_dir)
                    self._available_themes[theme.theme_id] = theme
                    logger.debug(f"Found theme: {theme}")
                except Exception as e:
                    logger.warning(f"Failed to load theme from {theme_dir}: {e}")

        logger.info(
            f"Initialized {len(self._available_themes)} themes: {list(self._available_themes.keys())}"
        )

    def _setup_file_watcher(self):
        """Setup file watching for live reload in development mode."""
        if not self._enable_live_reload:
            return

        # Watch all QSS files in all theme directories
        watch_files = []

        for theme in self._available_themes.values():
            if theme.theme_directory:
                qss_file_paths = theme.get_qss_file_paths()
                watch_files.extend([str(p) for p in qss_file_paths])

        if watch_files:
            self._file_watcher = QFileSystemWatcher(watch_files)
            self._file_watcher.fileChanged.connect(self._on_theme_file_changed)
            self._watched_files = watch_files
            logger.info(
                f"Live theme reloading enabled, watching {len(watch_files)} files"
            )

    def _on_theme_file_changed(self, file_path: str):
        """Handle theme file changes for live reloading."""
        logger.debug(f"Theme file changed: {file_path}, reloading...")
        if self._current_theme:
            # Clear cached QSS and re-apply the current theme
            self._current_theme.clear_cache()
            self._apply_theme_internal(self._current_theme, save_preference=False)

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
        import platform

        return {
            "platform": platform.system().lower(),
            "platform_detailed": platform.platform(),
            "python_version": platform.python_version(),
            "darkdetect_available": True,  # We imported it successfully
            "theme_service_version": "2.0.0-modular",
        }

    def get_available_themes(self) -> Dict[str, Theme]:
        """Get all available themes."""
        return self._available_themes.copy()

    def get_themes_by_category(self, category: str) -> List[Theme]:
        """Get themes filtered by category."""
        return [
            theme
            for theme in self._available_themes.values()
            if theme.category == category
        ]

    def get_theme_categories(self) -> List[str]:
        """Get all available theme categories."""
        categories = set()
        for theme in self._available_themes.values():
            categories.add(theme.category)
        return sorted(list(categories))

    def get_current_theme(self) -> Optional[Theme]:
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

            return self._apply_theme_internal(theme, save_preference)

        except Exception as e:
            logger.error(f"Error applying theme {theme_identifier}: {e}")
            return False

    def _apply_theme_internal(self, theme: Theme, save_preference: bool = True) -> bool:
        """Apply a theme configuration."""
        try:
            logger.debug(f"Applying theme: {theme}")

            # Load QSS content for the theme
            qss_content = theme.get_qss()

            # Apply the QSS to the application
            self._app.setStyleSheet(qss_content)

            self._current_theme = theme

            # Save preference if requested
            if save_preference and self._config_service:
                self._config_service.set_theme_preference(theme.theme_id)

            # Emit signal
            self.theme_changed.emit(theme.theme_id)

            logger.info(f"Successfully applied theme: {theme.name}")
            return True

        except Exception as e:
            logger.error(f"Error applying theme {theme}: {e}")
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
