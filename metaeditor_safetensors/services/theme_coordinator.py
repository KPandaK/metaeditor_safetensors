from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QApplication

from ..models.theme import Theme, ThemeType
from .config_service import ConfigService
from .status_message_service import StatusMessageService
from .theme_service import ThemeService


class ThemeCoordinator:
    """Coordinates theme application and persistence."""

    def __init__(
        self,
        theme_service: ThemeService,
        config_service: ConfigService,
        status_messages: StatusMessageService,
    ) -> None:
        self._theme_service = theme_service
        self._config_service = config_service
        self._status_messages = status_messages
        self._app: Optional[QApplication] = None
        self._announce_next_change = False
        self._current_theme: Theme | None = None

        self._theme_service.add_theme_changed_observer(self._on_theme_changed)

    @property
    def theme_service(self) -> ThemeService:
        return self._theme_service

    def connect_app(self, app: QApplication) -> None:
        self._app = app

    @property
    def current_theme(self) -> Theme | None:
        return self._current_theme

    @property
    def current_theme_category(self) -> ThemeType | None:
        if self._current_theme:
            return self._current_theme.config.category
        return None

    def apply_startup_theme(self) -> None:
        preferred_theme = self._config_service.get_theme_preference() or "system"

        if not self.apply_theme(preferred_theme):
            # Fall back to default theme when preference fails
            self.apply_theme("system")

    def apply_theme(self, theme_id: str, *, announce: bool = False) -> bool:
        if announce:
            self._announce_next_change = True

        success = self._theme_service.apply_theme(theme_id)
        if not success:
            self._announce_next_change = False
            self._status_messages.error(f"Failed to apply theme: {theme_id}")
        return success

    def shutdown(self) -> None:
        self._theme_service.remove_theme_changed_observer(self._on_theme_changed)

    def _on_theme_changed(self, theme: Theme) -> None:
        self._current_theme = theme
        self._config_service.set_theme_preference(theme.config.theme_id)
        if self._app is not None:
            self._app.setProperty("metaeditor.theme_id", theme.config.theme_id)
            self._app.setProperty(
                "metaeditor.theme_category", theme.config.category.value
            )
            self._app.setStyleSheet(theme.get_qss())

        if self._announce_next_change:
            self._status_messages.success(f"Theme changed to: {theme.config.name}")
            self._announce_next_change = False
