"""
Stylesheet Service
==================

Service for managing application stylesheets with optional live-reloading for development.
"""

import os
from typing import Optional

from PySide6.QtCore import QFile, QFileSystemWatcher, QIODevice, QObject
from PySide6.QtWidgets import QApplication


class StylesheetService(QObject):
    """
    Service for managing application stylesheets.

    Supports both production mode (Qt resources) and development mode (file watching).
    """

    def __init__(
        self,
        app: QApplication,
        resource_path: str,
        filesystem_path: Optional[str] = None,
    ):
        super().__init__()
        self._app = app
        self._resource_path = resource_path
        self._filesystem_path = filesystem_path
        self._watcher = None

        # Check environment variable for live-reload mode
        self._enable_live_reload = (
            os.getenv("DEV_LIVE_STYLING", "false").lower() == "true"
        )

    def apply_stylesheet(self):
        """Apply the stylesheet using the appropriate method."""
        if self._enable_live_reload and self._filesystem_path:
            self._apply_from_file()
            self._setup_file_watcher()
        else:
            self._apply_from_resources()

    def _apply_from_resources(self):
        """Load stylesheet from Qt resources (production mode)."""
        style_file = QFile(self._resource_path)
        if style_file.open(QIODevice.ReadOnly | QIODevice.Text):
            stylesheet = style_file.readAll().data().decode("utf-8")
            self._app.setStyleSheet(stylesheet)
            style_file.close()
        else:
            print(
                f"Warning: Could not load stylesheet from resources: {self._resource_path}"
            )

    def _apply_from_file(self):
        """Load stylesheet from filesystem (development mode)."""
        if not self._filesystem_path:
            print("[DEV] No filesystem path provided, falling back to resources")
            self._apply_from_resources()
            return

        try:
            with open(self._filesystem_path, "r", encoding="utf-8") as f:
                self._app.setStyleSheet(f.read())
                print(f"[DEV] Loaded stylesheet from {self._filesystem_path}")
        except FileNotFoundError:
            print(
                f"[DEV] Stylesheet not found at {self._filesystem_path}, falling back to resources"
            )
            self._apply_from_resources()

    def _setup_file_watcher(self):
        """Set up file watching for live reload in development mode."""
        if not self._filesystem_path or not os.path.exists(self._filesystem_path):
            print(
                f"[DEV] Warning: Stylesheet file not found for watching: {self._filesystem_path}"
            )
            return

        if self._watcher is None:
            self._watcher = QFileSystemWatcher([self._filesystem_path])
            self._watcher.fileChanged.connect(self._on_file_changed)
            print(
                f"[DEV] Live stylesheet reloading enabled, watching: {self._filesystem_path}"
            )

    def _on_file_changed(self):
        """Handle file change events for live reloading."""
        print("[DEV] Stylesheet changed, reloading...")
        self._apply_from_file()
