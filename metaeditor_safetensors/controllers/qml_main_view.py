"""
QML Main View Controller
Bridges between the existing main controller and QML main view.
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtQml import QQmlApplicationEngine

from .. import resources_rc

logger = logging.getLogger(__name__)


class MainViewHelper(QObject):
    """QObject to provide data and functionality to QML MainView."""

    # Action signals
    setThumbnailRequested = Signal()
    viewThumbnailRequested = Signal()
    clearThumbnailRequested = Signal()

    def __init__(self):
        super().__init__()
        self._title = ""
        self._model_type = "Unknown"
        self._description = ""
        self._tags = ""
        self._author = ""
        self._date = ""
        self._merged_from = ""
        self._usage_hint = ""
        self._license = ""
        self._thumbnail_source = ""
        self._fields_enabled = False

    # Getter methods (properties accessed from QML)
    @Slot(result=str)
    def getTitle(self):
        return self._title

    @Slot(result=str)
    def getModelType(self):
        return self._model_type

    @Slot(result=str)
    def getDescription(self):
        return self._description

    @Slot(result=str)
    def getTags(self):
        return self._tags

    @Slot(result=str)
    def getAuthor(self):
        return self._author

    @Slot(result=str)
    def getDate(self):
        return self._date

    @Slot(result=str)
    def getMergedFrom(self):
        return self._merged_from

    @Slot(result=str)
    def getUsageHint(self):
        return self._usage_hint

    @Slot(result=str)
    def getLicense(self):
        return self._license

    @Slot(result=str)
    def getThumbnailSource(self):
        return self._thumbnail_source

    @Slot(result=bool)
    def getFieldsEnabled(self):
        return self._fields_enabled

    # Setter methods (called from QML)
    @Slot(str)
    def setTitle(self, value):
        self._title = value

    @Slot(str)
    def setModelType(self, value):
        self._model_type = value

    @Slot(str)
    def setDescription(self, value):
        self._description = value

    @Slot(str)
    def setTags(self, value):
        self._tags = value

    @Slot(str)
    def setAuthor(self, value):
        self._author = value

    @Slot(str)
    def setDate(self, value):
        self._date = value

    @Slot(str)
    def setMergedFrom(self, value):
        self._merged_from = value

    @Slot(str)
    def setUsageHint(self, value):
        self._usage_hint = value

    @Slot(str)
    def setLicense(self, value):
        self._license = value

    @Slot(str)
    def setThumbnailSource(self, value):
        self._thumbnail_source = value

    @Slot(bool)
    def setFieldsEnabled(self, enabled):
        self._fields_enabled = enabled

    # Action slots
    @Slot()
    def onSetThumbnailClicked(self):
        self.setThumbnailRequested.emit()

    @Slot()
    def onViewThumbnailClicked(self):
        self.viewThumbnailRequested.emit()

    @Slot()
    def onClearThumbnailClicked(self):
        self.clearThumbnailRequested.emit()


class QmlMainView(QObject):
    """QML Main View wrapper."""

    def __init__(self, engine: QQmlApplicationEngine):
        super().__init__()
        self._engine = engine
        self._helper = MainViewHelper()

        # Register the helper with QML
        self._engine.rootContext().setContextProperty("mainViewHelper", self._helper)

        # Load the QML file
        qml_file = "qrc:/qml/views/MainView.qml"
        self._engine.load(qml_file)

        if not self._engine.rootObjects():
            logger.error(f"Failed to load QML file: {qml_file}")
            raise RuntimeError(f"Failed to load QML file: {qml_file}")
        else:
            logger.info(f"Successfully loaded QML main view: {qml_file}")

        self._window = self._engine.rootObjects()[0]

    @property
    def helper(self) -> MainViewHelper:
        """Get the helper object for connecting to main controller."""
        return self._helper

    @property
    def window(self):
        """Get the QML window object."""
        return self._window

    def show(self):
        """Show the main view."""
        if hasattr(self._window, 'show'):
            self._window.show()

    def close(self):
        """Close the main view."""
        if hasattr(self._window, 'close'):
            self._window.close()