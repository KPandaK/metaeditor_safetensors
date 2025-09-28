from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

import darkdetect
from PySide6.QtCore import QFileSystemWatcher
from PySide6.QtWidgets import QApplication

from .config_service import ConfigService
from .status_message_service import StatusMessageService
from .utility import get_package_root

logger = logging.getLogger(__name__)


class ThemeType(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass(slots=True)
class ThemeConfig:
    theme_id: str
    name: str
    category: ThemeType
    description: str
    file: str
    path: Optional[Path] = None


class ThemeManager:
    def __init__(
        self,
        config_service: ConfigService,
        status_messages: StatusMessageService,
        *,
        themes_root: Optional[Path] = None,
        enable_live_reload: Optional[bool] = None,
    ) -> None:
        self._config_service = config_service
        self._status_messages = status_messages
        self._app: Optional[QApplication] = None

        self._current_theme: Optional[ThemeConfig] = None
        self._qss_cache: Dict[str, str] = {}

        self._enable_live_reload = (
            enable_live_reload
            if enable_live_reload is not None
            else os.getenv("DEV_LIVE_STYLING", "false").lower() == "true"
        )
        self._file_watcher: Optional[QFileSystemWatcher] = None
        self._watched_files: list[str] = []

        self._themes_root = themes_root or (get_package_root() / "themes")
        self._available_themes: Dict[str, ThemeConfig] = self._load_built_in_themes()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def attach_app(self, app: QApplication) -> None:
        self._app = app
        if self._current_theme is not None:
            self._apply_theme(
                self._current_theme,
                announce=False,
                preference_id=None,
                persist=False,
            )

    def apply_startup_theme(self) -> None:
        preference = (
            self._config_service.get_theme_preference() or ThemeType.SYSTEM.value
        )
        if not self.apply_theme(preference):
            logger.warning(
                "Falling back to dark theme after failed startup preference: %s",
                preference,
            )
            self.apply_theme(ThemeType.DARK.value)

    def apply_theme(self, theme_id: str, *, announce: bool = False) -> bool:
        canonical_id, preference_id = self._resolve_theme_identifier(theme_id)

        if canonical_id is None:
            logger.error("Theme '%s' is not available", theme_id)
            self._status_messages.error(f"Theme '{theme_id}' is not available.")
            return False

        theme = self._available_themes.get(canonical_id)
        if not theme:
            logger.error("Theme '%s' is not available", theme_id)
            self._status_messages.error(f"Theme '{theme_id}' is not available.")
            return False

        success = self._apply_theme(
            theme, announce=announce, preference_id=preference_id, persist=True
        )
        if not success:
            self._status_messages.error(f"Failed to apply theme: {theme.name}")
        return success

    def toggle_theme(self, *, announce: bool = False) -> bool:
        target = ThemeType.LIGHT.value
        if (
            self._current_theme
            and self._current_theme.theme_id == ThemeType.LIGHT.value
        ):
            target = ThemeType.DARK.value
        return self.apply_theme(target, announce=announce)

    def get_available_themes(self) -> Iterable[ThemeConfig]:
        return self._available_themes.values()

    def get_current_theme(self) -> Optional[ThemeConfig]:
        return self._current_theme

    @property
    def current_theme_category(self) -> Optional[ThemeType]:
        if self._current_theme:
            return self._current_theme.category
        return None

    def has_theme(self, theme_id: str) -> bool:
        canonical_id, _ = self._resolve_theme_identifier(theme_id)
        return canonical_id in self._available_themes

    def detect_system_theme(self) -> ThemeType:
        try:
            system_theme = darkdetect.theme()
            if system_theme and system_theme.lower() == "dark":
                return ThemeType.DARK
            return ThemeType.LIGHT
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("darkdetect failed to determine system theme: %s", exc)
            return ThemeType.LIGHT

    # Backwards compatible alias for existing callers
    _detect_system_theme = detect_system_theme

    def shutdown(self) -> None:
        if self._file_watcher and self._watched_files:
            try:
                self._file_watcher.removePaths(self._watched_files)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Error removing theme file watchers: %s", exc)
        self._watched_files = []
        self._file_watcher = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_built_in_themes(self) -> Dict[str, ThemeConfig]:
        definitions = [
            ThemeConfig(
                theme_id="light",
                name="Light-Modern",
                category=ThemeType.LIGHT,
                description="Light appearance",
                file="light.qss",
            ),
            ThemeConfig(
                theme_id="dark",
                name="Dark-Modern",
                category=ThemeType.DARK,
                description="Dark appearance",
                file="dark.qss",
            ),
        ]

        themes: Dict[str, ThemeConfig] = {}
        for theme in definitions:
            qss_path = self._themes_root / theme.file
            if not qss_path.exists():
                logger.warning(
                    "Theme '%s' is missing file %s", theme.theme_id, qss_path
                )
                continue
            theme.path = qss_path
            themes[theme.theme_id] = theme

        if not themes:
            logger.error("No themes were loaded from %s", self._themes_root)
        return themes

    def _resolve_theme_identifier(
        self, requested_id: str
    ) -> tuple[Optional[str], Optional[str]]:
        request = (requested_id or ThemeType.SYSTEM.value).lower()

        alias_map = {
            "dark": ThemeType.DARK.value,
            "light": ThemeType.LIGHT.value,
        }

        request = alias_map.get(request, request)

        if request == ThemeType.SYSTEM.value:
            detected = self.detect_system_theme().value
            return detected, ThemeType.SYSTEM.value

        if request not in self._available_themes:
            return None, None

        return request, request

    def _apply_theme(
        self,
        theme: ThemeConfig,
        *,
        announce: bool,
        preference_id: Optional[str],
        persist: bool,
    ) -> bool:
        try:
            stylesheet = self._load_stylesheet(theme)
            if stylesheet is None:
                return False

            self._current_theme = theme

            if persist and preference_id is not None:
                self._config_service.set_theme_preference(preference_id)

            if self._enable_live_reload:
                self._ensure_file_watcher()
                self._install_file_watcher(theme)

            if self._app is not None:
                self._app.setProperty("metaeditor.theme_id", theme.theme_id)
                self._app.setProperty("metaeditor.theme_category", theme.category.value)
                self._app.setStyleSheet(stylesheet)

            if announce:
                self._status_messages.success(
                    f"Theme changed to: {theme.name}", timeout_ms=3000
                )

            return True
        except Exception as exc:
            logger.error("Error applying theme '%s': %s", theme.theme_id, exc)
            return False

    def _load_stylesheet(self, theme: ThemeConfig) -> Optional[str]:
        if theme.theme_id in self._qss_cache:
            return self._qss_cache[theme.theme_id]

        if not theme.path:
            logger.error("Theme '%s' has no stylesheet path configured", theme.theme_id)
            return None

        try:
            stylesheet = theme.path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error(
                "Failed reading stylesheet for theme '%s': %s", theme.theme_id, exc
            )
            return None

        self._qss_cache[theme.theme_id] = stylesheet
        return stylesheet

    def _ensure_file_watcher(self) -> None:
        if self._file_watcher is None:
            self._file_watcher = QFileSystemWatcher()
            self._file_watcher.fileChanged.connect(self._on_theme_file_changed)

    def _install_file_watcher(self, theme: ThemeConfig) -> None:
        if not self._file_watcher:
            return

        if self._watched_files:
            try:
                self._file_watcher.removePaths(self._watched_files)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Error clearing watched files: %s", exc)
            self._watched_files.clear()

        if theme.path and theme.path.exists():
            path_str = str(theme.path)
            self._file_watcher.addPath(path_str)
            self._watched_files = [path_str]

    def _on_theme_file_changed(self, file_path: str) -> None:
        if not self._current_theme:
            return

        logger.info("Theme asset changed (%s); reapplying current theme", file_path)
        self._qss_cache.pop(self._current_theme.theme_id, None)
        self._apply_theme(
            self._current_theme,
            announce=False,
            preference_id=None,
            persist=False,
        )
