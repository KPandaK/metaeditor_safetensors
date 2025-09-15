import logging
import os
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional

import darkdetect
from PySide6.QtCore import QFileSystemWatcher, QObject, QThread, Signal

from ..models.settings import Settings
from ..models.theme import Theme, ThemeType
from .file_service import get_package_root

logger = logging.getLogger(__name__)


class SystemThemeMonitor(QObject):
    """Monitors system theme changes and emits Qt signals."""

    theme_changed = Signal(str)  # Emits the new theme name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitoring = False
        self._monitor_thread = None

    def start_monitoring(self):
        """Start monitoring system theme changes."""
        if self._monitoring:
            return

        logger.debug("Starting system theme monitoring")
        self._monitoring = True

        # Start monitoring in a separate thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_system_theme, daemon=True
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring system theme changes."""
        if not self._monitoring:
            return

        logger.debug("Stopping system theme monitoring")
        self._monitoring = False

        if self._monitor_thread and self._monitor_thread.is_alive():
            # Wait for thread to finish, but don't wait too long
            self._monitor_thread.join(timeout=1.0)

        self._monitor_thread = None

    def _monitor_system_theme(self):
        """Monitor system theme changes using darkdetect listener."""
        try:

            def on_theme_change(theme):
                if self._monitoring:
                    logger.debug(f"System theme changed to: {theme}")
                    self.theme_changed.emit(theme)

            # This will block until monitoring is stopped
            darkdetect.listener(on_theme_change)

        except Exception as e:
            logger.error(f"Error in system theme monitoring: {e}")


class ThemeService:
    def __init__(self, config_service=None):
        self._theme_changed_observers: List[Callable[[Theme], None]] = []
        self._current_theme: Optional[Theme] = None
        self._available_themes: Dict[str, Theme] = {}
        self._themes_root: Optional[Path] = None
        self._config_service = config_service

        # System theme monitoring
        self._system_theme_monitor: Optional[SystemThemeMonitor] = None
        self._is_monitoring_system_theme = False

        # Determine the themes directory
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

        # Setup system theme monitoring if config service is available
        if self._config_service:
            self._setup_system_theme_monitoring()

    def _initialize_themes(self):
        logger.debug("Searching for themes")

        # Scan for themes from package
        if not self._themes_root or not self._themes_root.exists():
            logger.warning(f"Themes directory not found: {self._themes_root}")
            return

        for theme_dir in self._themes_root.iterdir():
            if self.is_valid_theme_directory(theme_dir):
                try:
                    theme = Theme.from_directory(theme_dir)
                    self._available_themes[theme.config.theme_id] = theme
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
        if not self._enable_live_reload:
            return

        # Initialize file watcher but don't watch any files yet
        # Files will be watched when a theme is applied
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.fileChanged.connect(self._on_theme_file_changed)
        self._watched_files = []

        logger.info("Live theme reloading enabled")

    def _on_theme_file_changed(self, file_path: str):
        logger.debug(f"Theme file changed: {file_path}, reloading...")
        if self._current_theme:
            # Clear cached QSS and re-apply the current theme
            self._current_theme.clear_cache()
            self._apply_theme_internal(self._current_theme)

    def _update_file_watchers(self):
        if not self._enable_live_reload or not self._file_watcher:
            return

        # Remove all currently watched files
        if self._watched_files:
            try:
                self._file_watcher.removePaths(self._watched_files)
            except Exception as e:
                logger.warning(f"Failed to remove watched theme files: {e}")
            self._watched_files.clear()

        # Add files from the current theme
        if self._current_theme:
            qss_file_paths = self._current_theme.get_qss_file_paths()
            watch_files = [str(p) for p in qss_file_paths]

            if watch_files:
                self._file_watcher.addPaths(watch_files)
                self._watched_files = watch_files
                logger.debug(
                    f"Now watching {len(watch_files)} files for theme '{self._current_theme.config.name}'"
                )

    def add_theme_changed_observer(self, callback: Callable[[Theme], None]):
        self._theme_changed_observers.append(callback)

    def remove_theme_changed_observer(self, callback: Callable[[Theme], None]):
        if callback in self._theme_changed_observers:
            self._theme_changed_observers.remove(callback)

    def _notify_theme_changed(self, theme: Theme):
        for callback in self._theme_changed_observers:
            try:
                callback(theme)
            except Exception as e:
                logger.warning(f"Error calling theme changed observer: {e}")

    def get_current_theme(self) -> Optional[Theme]:
        return self._current_theme

    def has_theme(self, theme_id: str) -> bool:
        return theme_id in self._available_themes

    def apply_default_theme(self) -> bool:
        default_theme_id = "system"
        logger.debug(f"Applying default theme: {default_theme_id}")
        return self.apply_theme(default_theme_id)

    def apply_theme(self, theme_id: str) -> bool:
        logger.debug(f"Applying theme: {theme_id}")

        try:
            # Handle special "system" theme_id by detecting actual system theme
            if theme_id == "system":
                actual_theme_id = self._resolve_system_theme()
                logger.debug(f"System theme resolved to: {actual_theme_id}")
                theme = self._available_themes.get(actual_theme_id)
            else:
                # Direct theme lookup
                theme = self._available_themes.get(theme_id)

            if not theme:
                logger.error(f"No theme found for ID: {theme_id}")
                return False

            return self._apply_theme_internal(theme)

        except Exception as e:
            logger.error(f"Error applying theme {theme_id}: {e}")
            return False

    def _resolve_system_theme(self) -> str:
        system_theme_type = self._detect_system_theme()

        # Find the first theme matching the detected system theme category
        for theme_id, theme in self._available_themes.items():
            if theme.config.category == system_theme_type.value:
                return theme_id

        fallback_id = list(self._available_themes.keys())[0]
        logger.warning(
            f"No theme found for system category '{system_theme_type.value}', using fallback: {fallback_id}"
        )
        return fallback_id

    def _detect_system_theme(self) -> ThemeType:
        try:
            # Use darkdetect to detect system theme
            theme_str = darkdetect.theme()

            if theme_str is None:
                logger.warning("darkdetect returned None, theme detection failed")
                theme_type = ThemeType.LIGHT  # Default fallback
            elif theme_str.lower() == "dark":
                theme_type = ThemeType.DARK
            elif theme_str.lower() == "light":
                theme_type = ThemeType.LIGHT
            else:
                logger.warning(f"darkdetect returned unexpected value: {theme_str}")
                theme_type = ThemeType.LIGHT  # Default fallback

        except Exception as e:
            logger.error(f"Error detecting system theme: {e}")
            theme_type = ThemeType.LIGHT  # Default fallback

        logger.info(f"Detected system theme: {theme_type.value}")
        return theme_type

    def _apply_theme_internal(self, theme: Theme) -> bool:
        try:
            logger.debug(f"Applying theme: {theme}")

            self._current_theme = theme

            # Update file watchers to monitor the new theme's files
            self._update_file_watchers()

            # Notify observers with theme object
            self._notify_theme_changed(theme)

            logger.info(f"Successfully applied theme: {theme.config.name}")
            return True

        except Exception as e:
            logger.error(f"Error applying theme {theme}: {e}")
            return False

    def _setup_system_theme_monitoring(self):
        """Setup system theme monitoring if user preference is set to 'system'."""
        try:
            if (
                self._config_service
                and self._config_service.get_theme_preference() == "system"
            ):
                self._start_system_theme_monitoring()
        except Exception as e:
            logger.warning(f"Error setting up system theme monitoring: {e}")

    def _start_system_theme_monitoring(self):
        """Start monitoring system theme changes."""
        if self._is_monitoring_system_theme:
            return

        try:
            self._system_theme_monitor = SystemThemeMonitor()
            self._system_theme_monitor.theme_changed.connect(
                self._on_system_theme_changed
            )
            self._system_theme_monitor.start_monitoring()
            self._is_monitoring_system_theme = True
            logger.info("System theme monitoring started")
        except Exception as e:
            logger.error(f"Error starting system theme monitoring: {e}")

    def _stop_system_theme_monitoring(self):
        """Stop monitoring system theme changes."""
        if not self._is_monitoring_system_theme or not self._system_theme_monitor:
            return

        try:
            self._system_theme_monitor.stop_monitoring()
            self._system_theme_monitor = None
            self._is_monitoring_system_theme = False
            logger.info("System theme monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping system theme monitoring: {e}")

    def _on_system_theme_changed(self, system_theme: str):
        """Handle system theme change event."""
        try:
            # Only update if user preference is still set to "system"
            if (
                self._config_service
                and self._config_service.get_theme_preference() == "system"
            ):
                logger.info(f"System theme changed to: {system_theme}")
                # Apply the new system theme
                self.apply_theme("system")
            else:
                # User changed preference away from "system", stop monitoring
                self._stop_system_theme_monitoring()
        except Exception as e:
            logger.error(f"Error handling system theme change: {e}")

    def update_system_monitoring_for_preference(self, theme_preference: str):
        """Update system theme monitoring based on theme preference.

        Args:
            theme_preference: The new theme preference ("system", "dark", "light", etc.)
        """
        try:
            if theme_preference == "system":
                # Start monitoring if not already started
                if not self._is_monitoring_system_theme:
                    self._start_system_theme_monitoring()
            else:
                # Stop monitoring if currently monitoring
                if self._is_monitoring_system_theme:
                    self._stop_system_theme_monitoring()
        except Exception as e:
            logger.error(
                f"Error updating system monitoring for preference {theme_preference}: {e}"
            )

    def shutdown(self):
        """Cleanup and shutdown the theme service."""
        try:
            self._stop_system_theme_monitoring()
        except Exception as e:
            logger.error(f"Error during theme service shutdown: {e}")
