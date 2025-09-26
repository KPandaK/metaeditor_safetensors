import logging
import os
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional

import darkdetect
from PySide6.QtCore import QFileSystemWatcher

from ..models.settings import Settings
from ..models.theme import Theme, ThemeType
from .utility import get_package_root

logger = logging.getLogger(__name__)


class ThemeService:
    def __init__(self):
        self._theme_changed_observers: List[Callable[[Theme], None]] = []
        self._current_theme: Optional[Theme] = None
        self._available_themes: Dict[str, Theme] = {}
        self._themes_root: Optional[Path] = None

        # System theme monitoring
        self._system_theme_thread: Optional[threading.Thread] = None
        self._system_theme_callbacks: List[Callable[[str], None]] = []

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

        # Start system theme monitoring
        self._start_system_theme_monitoring()

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
                    logger.debug(f"Found theme: {theme.config.name}")
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

    def add_system_theme_changed_callback(self, callback: Callable[[str], None]):
        self._system_theme_callbacks.append(callback)

    def remove_system_theme_changed_callback(self, callback: Callable[[str], None]):
        if callback in self._system_theme_callbacks:
            self._system_theme_callbacks.remove(callback)

    def _notify_system_theme_changed(self, system_theme: str):
        for callback in self._system_theme_callbacks:
            try:
                callback(system_theme)
            except Exception as e:
                logger.warning(f"Error calling system theme changed callback: {e}")

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

    def _start_system_theme_monitoring(self):
        if self._system_theme_thread is not None:
            return

        try:
            logger.debug("Starting system theme monitoring")

            # Start monitoring in a separate daemon thread using darkdetect.listener
            self._system_theme_thread = threading.Thread(
                target=darkdetect.listener,
                args=(self._on_system_theme_changed,),
                daemon=True,
            )
            self._system_theme_thread.start()
            logger.info("System theme monitoring started")
        except Exception as e:
            logger.error(f"Error starting system theme monitoring: {e}")
            self._system_theme_thread = None

    def _stop_system_theme_monitoring(self):
        if self._system_theme_thread is None:
            return

        try:
            logger.debug("Stopping system theme monitoring")
            self._system_theme_thread = None
            # Note: darkdetect.listener doesn't provide a clean way to stop,
            # so we rely on the daemon thread
            logger.info("System theme monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping system theme monitoring: {e}")

    def _on_system_theme_changed(self, system_theme: str):
        try:
            logger.info(f"System theme changed to: {system_theme}")
            # Notify all registered callbacks
            self._notify_system_theme_changed(system_theme)
        except Exception as e:
            logger.error(f"Error handling system theme change: {e}")

    def shutdown(self):
        try:
            self._stop_system_theme_monitoring()
        except Exception as e:
            logger.error(f"Error during theme service shutdown: {e}")
