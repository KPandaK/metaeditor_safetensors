import logging
import threading

import darkdetect
from PySide6.QtCore import Property, QObject, Signal

logger = logging.getLogger(__name__)


class QmlThemeService(QObject):
    # Signal emitted when theme changes
    themeChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_theme = self._detect_system_theme()
        self._system_theme_thread: threading.Thread | None = None

        # Start monitoring system theme changes
        self._start_system_theme_monitoring()

        logger.info(f"QML Theme Service initialized with theme: {self._current_theme}")

    @Property(str, notify=themeChanged)
    def currentTheme(self) -> str:
        return self._current_theme

    def _detect_system_theme(self) -> str:
        try:
            theme_str = darkdetect.theme()
            if theme_str and theme_str.lower() == "dark":
                return "dark"
            else:
                return "light"
        except Exception as e:
            logger.error(f"Error detecting system theme: {e}")
            return "dark"  # Default to dark for now since we only implement dark

    def _start_system_theme_monitoring(self):
        try:
            logger.debug("Starting QML system theme monitoring")
            self._system_theme_thread = threading.Thread(
                target=darkdetect.listener,
                args=(self._on_system_theme_changed,),
                daemon=True,
            )
            self._system_theme_thread.start()
            logger.info("QML system theme monitoring started")
        except Exception as e:
            logger.error(f"Error starting QML system theme monitoring: {e}")

    def _on_system_theme_changed(self, system_theme: str):
        try:
            new_theme = "dark" if system_theme.lower() == "dark" else "light"
            if new_theme != self._current_theme:
                logger.info(
                    f"System theme changed from {self._current_theme} to {new_theme}"
                )
                self._current_theme = new_theme
                self.themeChanged.emit(new_theme)
        except Exception as e:
            logger.error(f"Error handling system theme change: {e}")

    def shutdown(self):
        try:
            if self._system_theme_thread:
                self._system_theme_thread = None
                logger.info("QML theme service shutdown")
        except Exception as e:
            logger.error(f"Error during QML theme service shutdown: {e}")
