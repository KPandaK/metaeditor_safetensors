import json
import logging
import os
from pathlib import Path
from typing import Callable, List, Optional

from ..models.settings import Settings

logger = logging.getLogger(__name__)


class ConfigService:
    MAX_RECENT_FILES = 10

    def __init__(self, config_path: Optional[Path] = None):
        self._recent_files_observers: List[Callable[[List[str]], None]] = []

        if config_path:
            self.config_path = config_path
        else:
            if os.name == "nt":  # Windows
                config_dir = Path(os.getenv("APPDATA", Path.home() / ".config"))
            else:  # macOS, Linux
                config_dir = Path(
                    os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config"
                )
            self.config_path = config_dir / "metaeditor_safetensors" / "settings.json"

        # Ensure the configuration directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.settings = self._load()

    def _load(self) -> Settings:
        if not self.config_path.exists():
            return Settings()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                json_data = f.read()
            return Settings.model_validate_json(json_data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Error loading config file: {e}. Using default settings.")
            return Settings()

    def _save(self):
        try:
            json_data = self.settings.model_dump_json(indent=2)
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(json_data)
        except (IOError, TypeError) as e:
            logger.warning(f"Error saving config file: {e}")

    def add_recent_files_observer(self, callback: Callable[[List[str]], None]):
        self._recent_files_observers.append(callback)

    def remove_recent_files_observer(self, callback: Callable[[List[str]], None]):
        if callback in self._recent_files_observers:
            self._recent_files_observers.remove(callback)

    def _notify_recent_files_changed(self):
        for callback in self._recent_files_observers:
            try:
                callback(self.settings.recent_files)
            except Exception as e:
                logger.warning(f"Error calling recent files observer: {e}")

    def get_recent_files(self) -> List[str]:
        return self.settings.recent_files

    def add_recent_file(self, file_path: str):
        recent_files = [p for p in self.settings.recent_files if p != file_path]

        recent_files.insert(0, file_path)

        self.settings.recent_files = recent_files[: self.MAX_RECENT_FILES]

        self._save()
        self._notify_recent_files_changed()

    def clear_recent_files(self):
        self.settings.recent_files = []
        self._save()
        self._notify_recent_files_changed()

    def remove_recent_file(self, file_path: str):
        self.settings.recent_files = [
            p for p in self.settings.recent_files if p != file_path
        ]
        self._save()
        self._notify_recent_files_changed()

    def get_theme_preference(self) -> str:
        return self.settings.theme

    def set_theme_preference(self, theme: str):
        self.settings.theme = theme
        self._save()

    def set_window_size(self, width: int, height: int):
        self.settings.window.width = width
        self.settings.window.height = height
        self._save()

    def get_window_size(self) -> tuple[int, int]:
        return (self.settings.window.width, self.settings.window.height)
