from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from metaeditor_safetensors.services.status_message_service import StatusMessageService
from metaeditor_safetensors.services.theme_manager import (
    ThemeConfig,
    ThemeManager,
    ThemeType,
)


class DummyConfigService:
    def __init__(self, preference: str = ThemeType.SYSTEM.value) -> None:
        self._preference = preference
        self.saved: list[str] = []

    def get_theme_preference(self) -> str:
        return self._preference

    def set_theme_preference(self, value: str) -> None:
        self._preference = value
        self.saved.append(value)


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


@pytest.fixture
def status_messages():
    service = StatusMessageService()
    captured = []
    service.add_listener(captured.append)
    return service, captured


@pytest.fixture
def temp_theme_root(tmp_path: Path):
    (tmp_path / "light").mkdir()
    (tmp_path / "dark").mkdir()
    (tmp_path / "light.qss").write_text("QWidget { background: #fff; }")
    (tmp_path / "dark.qss").write_text("QWidget { background: #000; }")
    return tmp_path


def create_manager(temp_theme_root, status_messages, preference=ThemeType.SYSTEM.value):
    status, _ = status_messages
    config = DummyConfigService(preference)
    manager = ThemeManager(
        config,
        status,
        themes_root=temp_theme_root,
        enable_live_reload=False,
    )
    return manager, config


def test_apply_theme_updates_app_stylesheet(app, temp_theme_root, status_messages):
    manager, config = create_manager(temp_theme_root, status_messages)
    manager.attach_app(app)

    assert manager.apply_theme("dark", announce=True)
    assert "#000" in app.styleSheet()
    assert config.saved[-1] == "dark"


def test_apply_startup_theme_falls_back_to_dark(app, temp_theme_root, status_messages):
    manager, config = create_manager(
        temp_theme_root, status_messages, preference="missing"
    )
    manager.attach_app(app)

    manager.apply_startup_theme()

    assert manager.get_current_theme().theme_id == ThemeType.DARK.value
    assert config.saved[-1] == ThemeType.DARK.value


def test_toggle_theme(app, temp_theme_root, status_messages):
    manager, _ = create_manager(temp_theme_root, status_messages)
    manager.attach_app(app)

    manager.apply_theme("light")
    manager.toggle_theme()
    assert manager.get_current_theme().theme_id == ThemeType.DARK.value
    manager.toggle_theme()
    assert manager.get_current_theme().theme_id == ThemeType.LIGHT.value


def test_apply_theme_unknown_reports_error(app, temp_theme_root, status_messages):
    status, messages = status_messages
    manager, _ = create_manager(temp_theme_root, (status, messages))
    manager.attach_app(app)

    config_saved_before = len(manager._config_service.saved)
    messages.clear()

    assert manager.apply_theme("missing") is False
    assert len(messages) == 1
    assert messages[-1].level.name == "ERROR"
    assert len(manager.get_available_themes()) == 2
    assert len(manager._config_service.saved) == config_saved_before


def test_live_reload_reapplies_stylesheet(app, tmp_path, status_messages):
    status, _ = status_messages
    (tmp_path / "light").mkdir()
    light_qss = tmp_path / "light.qss"
    light_qss.write_text("QWidget { background: #111; }")
    (tmp_path / "dark.qss").write_text("QWidget { background: #222; }")

    manager = ThemeManager(
        DummyConfigService(),
        status,
        themes_root=tmp_path,
        enable_live_reload=True,
    )
    manager.attach_app(app)

    manager.apply_theme("light")
    assert "#111" in app.styleSheet()

    # mutate file and trigger reload
    light_qss.write_text("QWidget { background: #999; }")
    manager._on_theme_file_changed(str(light_qss))
    assert "#999" in app.styleSheet()


def test_detect_system_theme_failure(monkeypatch, temp_theme_root, status_messages):
    status, _ = status_messages
    manager = ThemeManager(
        DummyConfigService(),
        status,
        themes_root=temp_theme_root,
        enable_live_reload=False,
    )

    monkeypatch.setattr(
        "metaeditor_safetensors.services.theme_manager.darkdetect.theme", lambda: None
    )
    assert manager.detect_system_theme() == ThemeType.LIGHT


def test_has_theme_recognizes_known_ids(temp_theme_root, status_messages):
    manager, _ = create_manager(temp_theme_root, status_messages)

    assert manager.has_theme("light")
    assert manager.has_theme("dark")
    assert not manager.has_theme("light-modern")
    assert not manager.has_theme("missing")


def test_apply_before_attach_updates_preference(temp_theme_root, status_messages):
    manager, config = create_manager(temp_theme_root, status_messages)
    assert manager.apply_theme("light")
    assert config.saved[-1] == "light"


def test_shutdown_clears_watchers(app, tmp_path, status_messages):
    status, _ = status_messages
    (tmp_path / "light.qss").write_text("QWidget { background: #444; }")
    (tmp_path / "dark.qss").write_text("QWidget { background: #555; }")

    manager = ThemeManager(
        DummyConfigService(),
        status,
        themes_root=tmp_path,
        enable_live_reload=True,
    )
    manager.attach_app(app)
    manager.apply_theme("light")

    assert manager._watched_files
    manager.shutdown()
    assert manager._watched_files == []


def test_attach_app_reapplies_current_theme(app, temp_theme_root, status_messages):
    manager, _ = create_manager(temp_theme_root, status_messages)
    assert manager.apply_theme("light")
    app.setStyleSheet("placeholder")
    manager.attach_app(app)
    assert "#fff" in app.styleSheet()
    assert app.property("metaeditor.theme_id") == "light"


def test_apply_theme_missing_after_resolution_reports_error(
    app, temp_theme_root, status_messages
):
    _service, messages = status_messages
    manager, _ = create_manager(temp_theme_root, status_messages)
    manager.attach_app(app)

    class BrokenThemes(dict):
        def __contains__(self, key):
            return True

        def get(self, key, default=None):
            return None

    manager._available_themes = BrokenThemes()
    messages.clear()

    assert manager.apply_theme("light") is False
    assert messages and messages[-1].level.name == "ERROR"
    assert "not available" in messages[-1].text


def test_current_theme_category_property(app, temp_theme_root, status_messages):
    manager, _ = create_manager(temp_theme_root, status_messages)
    assert manager.current_theme_category is None
    manager.attach_app(app)
    manager.apply_theme("dark")
    assert manager.current_theme_category == ThemeType.DARK


def test_apply_theme_system_uses_detected_theme(
    app, temp_theme_root, status_messages, monkeypatch
):
    manager, config = create_manager(temp_theme_root, status_messages)
    manager.attach_app(app)
    monkeypatch.setattr(manager, "detect_system_theme", lambda: ThemeType.DARK)

    assert manager.apply_theme(ThemeType.SYSTEM.value)
    assert config.saved[-1] == ThemeType.SYSTEM.value
    assert manager.get_current_theme().theme_id == ThemeType.DARK.value


def test_apply_theme_missing_stylesheet_reports_error(
    app, temp_theme_root, status_messages
):
    _service, messages = status_messages
    manager, config = create_manager(temp_theme_root, status_messages)
    manager.attach_app(app)

    broken_theme = ThemeConfig(
        theme_id="broken",
        name="Broken",
        category=ThemeType.DARK,
        description="Broken theme",
        file="broken.qss",
        path=None,
    )
    manager._available_themes["broken"] = broken_theme

    messages.clear()
    apply_result = manager.apply_theme("broken")

    assert apply_result is False
    assert messages and messages[-1].level.name == "ERROR"
    assert "Failed to apply theme" in messages[-1].text
    assert config.saved == []


def test_load_stylesheet_read_failure_returns_none(
    temp_theme_root, status_messages, monkeypatch
):
    manager, _ = create_manager(temp_theme_root, status_messages)
    theme = manager._available_themes["light"]
    path_cls = type(theme.path)
    original_read_text = path_cls.read_text

    def failing_read(self, encoding="utf-8", errors=None):
        if self == theme.path:
            raise OSError("boom")
        return original_read_text(self, encoding=encoding, errors=errors)

    monkeypatch.setattr(path_cls, "read_text", failing_read)
    assert manager._load_stylesheet(theme) is None


def test_apply_theme_handles_stylesheet_exception(
    app, temp_theme_root, status_messages, monkeypatch
):
    _service, messages = status_messages
    manager, _ = create_manager(temp_theme_root, status_messages)
    manager.attach_app(app)

    def raise_error(_theme):
        raise RuntimeError("boom")

    monkeypatch.setattr(manager, "_load_stylesheet", raise_error)
    messages.clear()
    assert manager.apply_theme("light") is False
    assert messages and messages[-1].level.name == "ERROR"
    assert "Failed to apply theme" in messages[-1].text


def test_install_file_watcher_without_watcher_is_noop(temp_theme_root, status_messages):
    manager, _ = create_manager(temp_theme_root, status_messages)
    theme = manager._available_themes["light"]
    manager._install_file_watcher(theme)
    assert manager._file_watcher is None
    assert manager._watched_files == []


def test_on_theme_file_changed_without_current_theme_is_noop(
    temp_theme_root, status_messages
):
    manager, _ = create_manager(temp_theme_root, status_messages)
    manager._qss_cache["light"] = "cached"
    manager._on_theme_file_changed("some/path.qss")
    assert manager._qss_cache["light"] == "cached"


def test_load_built_in_themes_handles_missing_files(tmp_path, status_messages):
    status_service, _ = status_messages
    manager = ThemeManager(
        DummyConfigService(),
        status_service,
        themes_root=tmp_path,
        enable_live_reload=False,
    )
    assert list(manager.get_available_themes()) == []


def test_detect_system_theme_dark_result(monkeypatch, temp_theme_root, status_messages):
    manager, _ = create_manager(temp_theme_root, status_messages)
    monkeypatch.setattr(
        "metaeditor_safetensors.services.theme_manager.darkdetect.theme",
        lambda: "Dark",
    )
    assert manager.detect_system_theme() == ThemeType.DARK
