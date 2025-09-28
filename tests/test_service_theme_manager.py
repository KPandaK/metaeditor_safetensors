from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from metaeditor_safetensors.services.status_message_service import StatusMessageService
from metaeditor_safetensors.services.theme_manager import ThemeManager, ThemeType


class DummyConfigService:
    def __init__(self, preference: str = ThemeType.SYSTEM.value) -> None:
        self._preference = preference

    def get_theme_preference(self) -> str:
        return self._preference

    def set_theme_preference(self, value: str) -> None:
        self._preference = value


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


@pytest.fixture
def status_service():
    service = StatusMessageService()
    messages = []
    service.add_listener(messages.append)
    return service, messages


def test_apply_theme_updates_stylesheet(app, status_service):
    status, messages = status_service
    config = DummyConfigService(ThemeType.SYSTEM.value)
    manager = ThemeManager(config, status, enable_live_reload=False)

    manager.attach_app(app)

    assert manager.apply_theme(ThemeType.DARK.value, announce=True) is True
    assert "background-color" in app.styleSheet()
    assert config.get_theme_preference() == ThemeType.DARK.value
    assert messages[-1].text.startswith("Theme changed to")


def test_apply_theme_system_detection(app, status_service, mocker):
    status, _ = status_service
    config = DummyConfigService(ThemeType.SYSTEM.value)
    manager = ThemeManager(config, status, enable_live_reload=False)
    manager.attach_app(app)

    mocker.patch(
        "metaeditor_safetensors.services.theme_manager.darkdetect.theme",
        return_value="Dark",
    )

    manager.apply_theme(ThemeType.SYSTEM.value)
    assert manager.get_current_theme() is not None
    assert manager.current_theme_category == ThemeType.DARK


def test_toggle_theme_switches_between_modes(app, status_service):
    status, _ = status_service
    config = DummyConfigService(ThemeType.LIGHT.value)
    manager = ThemeManager(config, status, enable_live_reload=False)
    manager.attach_app(app)

    manager.apply_theme(ThemeType.LIGHT.value)
    manager.toggle_theme()
    assert manager.get_current_theme().theme_id == ThemeType.DARK.value
    manager.toggle_theme()
    assert manager.get_current_theme().theme_id == ThemeType.LIGHT.value


def test_apply_theme_failure_reports_error(app, status_service):
    status, messages = status_service
    config = DummyConfigService()
    manager = ThemeManager(config, status, enable_live_reload=False)
    manager.attach_app(app)

    messages.clear()
    assert manager.apply_theme("not-a-theme") is False
    assert messages[-1].level.name == "ERROR"
