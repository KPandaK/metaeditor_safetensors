import logging

from PySide6.QtCore import QEventLoop, QObject, Slot
from PySide6.QtQuick import QQuickWindow

logger = logging.getLogger(__name__)


class ThumbnailHelper(QObject):
    def __init__(self, data_uri, geometry=None):
        super().__init__()
        self._data_uri = data_uri
        self._geometry = geometry

    @Slot(result=str)
    def image_uri(self):
        return self._data_uri

    @Slot(result=int)
    def parentX(self):
        return self._geometry.x() if self._geometry else 0

    @Slot(result=int)
    def parentY(self):
        return self._geometry.y() if self._geometry else 0

    @Slot(result=int)
    def parentWidth(self):
        return self._geometry.width() if self._geometry else 0

    @Slot(result=int)
    def parentHeight(self):
        return self._geometry.height() if self._geometry else 0


class QmlThumbnailDialog:
    def __init__(self, engine=None, parent=None, data_uri=None):
        self._engine = engine
        self._parent = parent
        self._data_uri = data_uri
        self._window = None
        self._event_loop = None

    def exec(self):
        if self._engine is None:
            raise ValueError(
                "QmlThumbnailDialog requires a QQmlApplicationEngine instance"
            )

        if self._parent is None:
            raise ValueError("QmlThumbnailDialog requires a parent window")

        context = self._engine.rootContext()

        # Get parent geometry if available
        self._thumbnail_helper = ThumbnailHelper(
            self._data_uri, self._parent.geometry()
        )
        context.setContextProperty("thumbnailHelper", self._thumbnail_helper)

        qml_resource_url = "qrc:/qml/views/ThumbnailDialog.qml"
        self._engine.load(qml_resource_url)

        root_objects = self._engine.rootObjects()
        if not root_objects:
            logger.error("Failed to load QML Thumbnail dialog")
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

        logger.info("QML Thumbnail dialog shown successfully")

        # Create event loop to keep dialog open until closed
        self._event_loop = QEventLoop()
        self._event_loop.exec()

    def _on_dialog_closing(self):
        """Handle dialog closing."""
        if self._event_loop and self._event_loop.isRunning():
            self._event_loop.quit()
        logger.info("QML Thumbnail dialog closed")
