import logging
from importlib.metadata import PackageNotFoundError, version

from PySide6.QtCore import QEventLoop, QObject, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow

logger = logging.getLogger(__name__)


class ClipboardHelper(QObject):
    @Slot(str)
    def copyToClipboard(self, text):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)


def get_app_version():
    try:
        return version("metaeditor_safetensors")
    except PackageNotFoundError:
        return "dev"


class QmlAboutDialog:
    def __init__(self, engine=None, theme_service=None, parent=None):
        self._engine = engine
        self._parent = parent
        self._window = None
        self._event_loop = None
        self._clipboard_helper = None

    def exec(self):
        if self._engine is None:
            raise ValueError("QmlAboutDialog requires a QQmlApplicationEngine instance")

        context = self._engine.rootContext()
        app_version = get_app_version()
        context.setContextProperty("appVersion", app_version)

        self._clipboard_helper = ClipboardHelper()
        context.setContextProperty("clipboardHelper", self._clipboard_helper)

        qml_resource_url = "qrc:/qml/views/AboutDialog.qml"
        self._engine.load(qml_resource_url)

        root_objects = self._engine.rootObjects()
        if not root_objects:
            logger.error("Failed to load QML About dialog")
            return

        self._window = root_objects[0]
        if not isinstance(self._window, QQuickWindow):
            logger.error("Root object is not a QQuickWindow")
            return

        if self._parent:
            if hasattr(self._parent, "windowHandle") and self._parent.windowHandle():
                self._window.setTransientParent(self._parent.windowHandle())

        self._window.closing.connect(self._on_dialog_closing)

        self._window.raise_()
        self._window.requestActivate()

        logger.info("QML About dialog shown successfully")

        # Create event loop to keep dialog open until closed
        self._event_loop = QEventLoop()
        self._event_loop.exec()

    def _on_dialog_closing(self):
        if self._event_loop:
            self._event_loop.quit()
        logger.info("QML About dialog closed")
