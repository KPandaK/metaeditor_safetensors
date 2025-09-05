"""
Configuration Service
=====================

This module provides a service for managing application configuration and settings,
including the recent files list.
"""

import json
import logging
import os
from pathlib import Path
from typing import List

from .._version import __version__

logger = logging.getLogger(__name__)


class ConfigService:
    """
    Service for managing application configuration and persistent settings.

    This service handles loading and saving application settings to a JSON file
    in the appropriate user data directory.
    """

    # Configuration schema version - increment when making breaking changes
    CONFIG_VERSION = "1.0"

    def __init__(self):
        """Initialize the configuration service."""
        self._settings_dir = self._get_settings_directory()
        self._settings_file = self._settings_dir / "settings.json"
        self._settings = self._load_settings()
        self._max_recent_files = 10

    def _get_settings_directory(self) -> Path:
        """Get the appropriate directory for storing application settings."""
        if os.name == "nt":  # Windows
            app_data = os.environ.get("APPDATA", "")
            if app_data:
                settings_dir = Path(app_data) / "SafetensorsMetadataEditor"
            else:
                settings_dir = Path.home() / ".safetensors_metadata_editor"
        else:  # macOS, Linux
            settings_dir = Path.home() / ".safetensors_metadata_editor"

        # Create directory if it doesn't exist
        settings_dir.mkdir(parents=True, exist_ok=True)
        return settings_dir

    def _load_settings(self) -> dict:
        """Load settings from the JSON file."""
        if self._settings_file.exists():
            try:
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Ensure we have the required structure
                if not isinstance(data, dict):
                    return self._get_default_settings()

                # Ensure we have recent_files array
                if "recent_files" not in data or not isinstance(
                    data["recent_files"], list
                ):
                    data["recent_files"] = []

                return data

            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load settings file: {e}")
                return self._get_default_settings()
        return self._get_default_settings()

    def _get_default_settings(self) -> dict:
        """Get default settings structure."""
        return {
            "config_version": self.CONFIG_VERSION,
            "app_version": __version__,
            "recent_files": [],
        }

    def _save_settings(self) -> None:
        """Save settings to the JSON file."""
        try:
            # Ensure version info is always saved
            self._settings["config_version"] = self.CONFIG_VERSION
            self._settings["app_version"] = __version__

            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.warning(f"Could not save settings file: {e}")

    def get_recent_files(self) -> List[str]:
        """
        Get the list of recent files.

        Returns:
            List of file paths in most recent first order
        """
        recent_files = self._settings.get("recent_files", [])
        return list(recent_files)

    def add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: The absolute path to the file to add
        """
        recent_files = self.get_recent_files()

        # Remove if already in list (to avoid duplicates)
        if file_path in recent_files:
            recent_files.remove(file_path)

        # Add to the beginning of the list
        recent_files.insert(0, file_path)

        # Limit to max number of files
        if len(recent_files) > self._max_recent_files:
            recent_files = recent_files[: self._max_recent_files]

        # Update settings and save
        self._settings["recent_files"] = recent_files
        self._save_settings()

    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self._settings["recent_files"] = []
        self._save_settings()

    def remove_recent_file(self, file_path: str) -> None:
        """
        Remove a specific file from the recent files list.

        Args:
            file_path: The file path to remove
        """
        recent_files = self.get_recent_files()
        if file_path in recent_files:
            recent_files.remove(file_path)
            self._settings["recent_files"] = recent_files
            self._save_settings()
