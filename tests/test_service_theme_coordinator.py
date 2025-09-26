from __future__ import annotations

from types import SimpleNamespace

import pytest

from metaeditor_safetensors.models.theme import ThemeType
from metaeditor_safetensors.services.status_message_service import StatusMessageService
from metaeditor_safetensors.services.theme_coordinator import ThemeCoordinator


class DummyTheme:
    def __init__(
        self,
        theme_id: str,
        *,
        name: str | None = None,
        category: ThemeType | None = None,
    ) -> None:
        self.config = SimpleNamespace(
            theme_id=theme_id,
            name=name or theme_id,
            category=category or ThemeType.LIGHT,
        )

    def get_qss(self) -> str:
        return f"/* {self.config.theme_id} */"


class DummyThemeService:
    def __init__(self) -> None:
        self._observers: list = []
        self.applied: list[str] = []
        self._current_theme: DummyTheme | None = None

    def add_theme_changed_observer(self, callback):
        self._observers.append(callback)

    def remove_theme_changed_observer(self, callback):
        if callback in self._observers:
            self._observers.remove(callback)

    def apply_theme(self, theme_id: str) -> bool:
        self.applied.append(theme_id)
        if theme_id == "fail":
            return False
        category = ThemeType.DARK if "dark" in theme_id else ThemeType.LIGHT
        theme = DummyTheme(theme_id, category=category)
        self._current_theme = theme
        for observer in list(self._observers):
            observer(theme)
        return True

    def get_current_theme(self):
        return self._current_theme


class DummyConfigService:
    def __init__(self, preference: str | None = None) -> None:
        self._preference = preference
        self.saved: list[str] = []

    def get_theme_preference(self) -> str | None:
        return self._preference

    def set_theme_preference(self, theme_id: str) -> None:
        self.saved.append(theme_id)
        self._preference = theme_id


@pytest.fixture
def status_messages():
    service = StatusMessageService()
    messages: list = []
    service.add_listener(messages.append)
    return service, messages


def test_apply_startup_theme_uses_config_preference(status_messages):
    status_service, messages = status_messages
    config = DummyConfigService("dark")
    theme_service = DummyThemeService()
    coordinator = ThemeCoordinator(theme_service, config, status_service)

    coordinator.apply_startup_theme()

    assert theme_service.applied == ["dark"]
    assert config.saved[-1] == "dark"
    assert coordinator.current_theme_category == ThemeType.DARK
    assert messages == []

    coordinator.shutdown()


def test_apply_startup_theme_falls_back_on_failure(status_messages):
    status_service, messages = status_messages
    config = DummyConfigService("fail")
    theme_service = DummyThemeService()
    coordinator = ThemeCoordinator(theme_service, config, status_service)

    coordinator.apply_startup_theme()

    assert theme_service.applied == ["fail", "system"]
    assert config.saved[-1] == "system"
    assert messages[-1].text == "Failed to apply theme: fail"

    coordinator.shutdown()


def test_apply_theme_announces_when_requested(mocker, status_messages):
    status_service, messages = status_messages
    config = DummyConfigService()
    theme_service = DummyThemeService()
    coordinator = ThemeCoordinator(theme_service, config, status_service)

    app = mocker.Mock()
    coordinator.connect_app(app)

    assert coordinator.apply_theme("light", announce=True) is True
    assert theme_service.applied == ["light"]
    assert messages[-1].text == "Theme changed to: light"
    app.setProperty.assert_any_call("metaeditor.theme_id", "light")
    app.setProperty.assert_any_call("metaeditor.theme_category", ThemeType.LIGHT.value)
    app.setStyleSheet.assert_called_once_with("/* light */")

    coordinator.shutdown()


def test_apply_theme_failure_reports_error(status_messages):
    status_service, messages = status_messages
    config = DummyConfigService()
    theme_service = DummyThemeService()
    coordinator = ThemeCoordinator(theme_service, config, status_service)

    assert coordinator.apply_theme("fail", announce=True) is False
    assert theme_service.applied == ["fail"]
    assert messages[-1].text == "Failed to apply theme: fail"

    coordinator.shutdown()
