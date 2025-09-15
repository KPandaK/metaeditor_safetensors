"""
Theme Management Service
========================

Service for managing application themes with modular QSS files,
system theme detection, user preferences, and runtime theme switching.
"""

import logging
import os
import threading
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
    in development mode. Includes monitoring for system theme changes
    when using auto theme selection.
    """

    # Signals
    theme_changed = Signal(str)
    system_theme_changed = Signal(str)  # New signal for system theme changes

    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app
        self._cached_system_theme: Optional[SystemTheme] = None
        self._current_theme: Optional[Theme] = None
        self._available_themes: Dict[str, Theme] = {}
        self._themes_root: Optional[Path] = None
        self._current_theme_preference: Optional[str] = None  # Track if "auto" is selected

        # System theme monitoring
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self._monitor_lock = threading.Lock()

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
            self._setup_file_watchers()

        # Connect to system theme change signal to handle auto-reapplication
        self.system_theme_changed.connect(self._on_system_theme_changed)

    def _initialize_themes(self):
        """Find available themes from the package themes directory."""
        logger.debug("Searching for themes")

        # Scan for themes from package
        if not self._themes_root or not self._themes_root.exists():
            logger.warning(f"Themes directory not found: {self._themes_root}")
            return

        for theme_dir in self._themes_root.iterdir():
            if self.is_valid_theme_directory(theme_dir):
                try:
                    theme = Theme.from_directory(theme_dir)
                    self._available_themes[theme.theme_id] = theme
                    logger.debug(f"Found theme: {theme}")
                except Exception as e:
                    logger.warning(f"Failed to load theme from {theme_dir}: {e}")

        logger.info(
            f"Initialized {len(self._available_themes)} themes: {list(self._available_themes.keys())}"
        )

    def is_valid_theme_directory(self, theme_directory: Path) -> bool:
        if not theme_directory.exists() or not theme_directory.is_dir():
            return False

        # Check for YAML files
        yaml_files = list(theme_directory.glob("*.yaml"))
        return len(yaml_files) > 0

    def _setup_file_watchers(self):
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
            self._apply_theme_internal(self._current_theme)

    def _detect_system_theme(self, use_cache: bool = True) -> SystemTheme:
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

    def _resolve_auto_theme(self) -> str:
        system_theme = self._detect_system_theme()

        # Find the best matching theme for the detected system theme
        if system_theme == SystemTheme.DARK:
            # Look for the first theme matching the dark category
            for theme_id, theme in self._available_themes.items():
                if theme_id != "auto" and theme.category == SystemTheme.DARK.value:
                    return theme_id
        elif system_theme == SystemTheme.LIGHT:
            # Look for the first theme matching the light category
            for theme_id, theme in self._available_themes.items():
                if theme_id != "auto" and theme.category == SystemTheme.LIGHT.value:
                    return theme_id

        # Ultimate fallback (shouldn't happen if we have themes)
        logger.error("No themes available for auto resolution")
        return ""

    def get_current_theme(self) -> Optional[Theme]:
        """Get the currently applied theme."""
        return self._current_theme

    def get_current_theme_preference(self) -> Optional[str]:
        """Get the current theme preference (e.g., 'auto', 'dark', 'light')."""
        return self._current_theme_preference

    def is_monitoring_system_theme(self) -> bool:
        """Check if system theme monitoring is currently active."""
        with self._monitor_lock:
            return self._monitoring_active

    def has_theme(self, theme_id: str) -> bool:
        """Check if a theme ID exists (including 'auto')."""
        return theme_id == "auto" or theme_id in self._available_themes

    def apply_theme(self, theme_identifier: str) -> bool:
        logger.debug(f"Applying theme: {theme_identifier}")

        try:
            # Resolve auto theme to actual theme based on system detection
            if theme_identifier == "auto":
                resolved_theme_id = self._resolve_auto_theme()
                logger.debug(f"Auto theme resolved to: {resolved_theme_id}")
                if not resolved_theme_id:
                    logger.error("Auto theme resolution failed - no themes available")
                    return False
                theme = self._available_themes.get(resolved_theme_id)
            else:
                theme = self._available_themes.get(theme_identifier)

            if not theme:
                logger.error(f"Theme not found: {theme_identifier}")
                return False

            return self._apply_theme_internal(
                theme, original_preference=theme_identifier
            )

        except Exception as e:
            logger.error(f"Error applying theme {theme_identifier}: {e}")
            return False

    def _apply_theme_internal(
        self, theme: Theme, original_preference: Optional[str] = None
    ) -> bool:
        """Apply a theme configuration."""
        try:
            logger.debug(f"Applying theme: {theme}")

            # Load QSS content for the theme
            qss_content = theme.get_qss()

            # Apply the QSS to the application
            self._app.setStyleSheet(qss_content)

            self._current_theme = theme
            self._current_theme_preference = original_preference

            # Start or stop system theme monitoring based on preference
            if original_preference == "auto":
                self._start_system_theme_monitoring()
            else:
                self._stop_system_theme_monitoring()

            # Emit signal with original preference (so UI knows "auto" is selected)
            signal_theme_id = original_preference or theme.theme_id
            self.theme_changed.emit(signal_theme_id)

            logger.info(f"Successfully applied theme: {theme.name}")
            return True

        except Exception as e:
            logger.error(f"Error applying theme {theme}: {e}")
            return False

    def _start_system_theme_monitoring(self):
        """Start monitoring system theme changes in a background thread."""
        with self._monitor_lock:
            if self._monitoring_active:
                return  # Already monitoring

            self._monitoring_active = True
            self._monitoring_thread = threading.Thread(
                target=self._system_theme_monitor_loop,
                name="ThemeMonitor",
                daemon=True
            )
            self._monitoring_thread.start()
            logger.info("Started system theme monitoring")

    def _stop_system_theme_monitoring(self):
        """Stop monitoring system theme changes."""
        with self._monitor_lock:
            if not self._monitoring_active:
                return  # Not monitoring

            self._monitoring_active = False
            logger.info("Stopped system theme monitoring")
            
            # Note: We cannot forcefully terminate the monitoring thread
            # as darkdetect.listener() is a blocking call. The thread will
            # terminate naturally when the next system theme change occurs.

    def _system_theme_monitor_loop(self):
        """Background thread loop for monitoring system theme changes."""
        try:
            logger.debug("System theme monitoring thread started")
            
            def theme_change_callback(theme_name: str):
                """Callback for system theme changes from darkdetect."""
                with self._monitor_lock:
                    if not self._monitoring_active:
                        return  # Stop processing if monitoring was disabled
                
                logger.info(f"System theme changed to: {theme_name}")
                # Emit signal (thread-safe in Qt)
                self.system_theme_changed.emit(theme_name)
            
            # This is a blocking call that monitors system theme changes
            darkdetect.listener(theme_change_callback)
            
        except Exception as e:
            logger.error(f"Error in system theme monitoring: {e}")
        finally:
            with self._monitor_lock:
                self._monitoring_active = False
            logger.debug("System theme monitoring thread ended")

    def _on_system_theme_changed(self, theme_name: str):
        """Handle system theme change signal (called on main thread)."""
        try:
            # Only react if we're currently using auto theme
            if self._current_theme_preference != "auto":
                logger.debug("Ignoring system theme change - not using auto theme")
                return

            # Clear cached system theme to force re-detection
            self._cached_system_theme = None
            
            # Re-apply auto theme to pick up the new system theme
            logger.info("Re-applying auto theme due to system theme change")
            self.apply_theme("auto")
            
        except Exception as e:
            logger.error(f"Error handling system theme change: {e}")

    def cleanup(self):
        """Clean up resources including theme monitoring."""
        self._stop_system_theme_monitoring()
        
        if self._file_watcher:
            self._file_watcher.deleteLater()
            self._file_watcher = None
