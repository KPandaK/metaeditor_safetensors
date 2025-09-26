from typing import cast

import pytest

from metaeditor_safetensors.controllers.thumbnail_controller import ThumbnailController
from metaeditor_safetensors.models.metadata import ChangeSource, Metadata
from metaeditor_safetensors.views.thumbnail_dialog import ThumbnailDialog


class DummyGeometry:
    def __init__(self, x=0, y=0, width=640, height=480):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return self._width

    def height(self):
        return self._height

    def right(self):
        return self._x + self._width

    def bottom(self):
        return self._y + self._height


class DummyDialog:
    def __init__(self, pixmap, parent):
        self.pixmap = pixmap
        self.parent = parent
        self.moved_to = None
        self.exec_called = False

    def geometry(self):
        return DummyGeometry(0, 0, 320, 240)

    def move(self, x, y):
        self.moved_to = (x, y)

    def exec(self):
        self.exec_called = True


class DummyView:
    def __init__(self):
        self.messages: list[tuple[str, int]] = []
        self._geometry = DummyGeometry()

    def set_status_message(self, message: str, timeout: int = 0):
        self.messages.append((message, timeout))

    def geometry(self):
        return self._geometry


@pytest.fixture
def metadata():
    return Metadata()


@pytest.fixture
def view():
    return DummyView()


def test_set_thumbnail_uses_dialog_and_updates_metadata(metadata, view, mocker):
    mocker.patch(
        "metaeditor_safetensors.controllers.thumbnail_controller.filepath_to_data_uri",
        return_value="data-uri",
    )
    controller = ThumbnailController(
        metadata,
        view,
        file_dialog_getter=lambda *_, **__: ("image.png", ""),
    )

    controller.on_set_thumbnail_requested()

    assert metadata.get_value("modelspec.thumbnail") == "data-uri"
    assert view.messages[-1] == ("Thumbnail set.", 3000)


def test_set_thumbnail_handles_dialog_cancel(metadata, view):
    controller = ThumbnailController(
        metadata,
        view,
        file_dialog_getter=lambda *_, **__: ("", ""),
    )

    controller.on_set_thumbnail_requested()

    assert metadata.get_value("modelspec.thumbnail") in (None, "")
    assert view.messages == []


def test_set_thumbnail_reports_errors(metadata, view, mocker):
    mocker.patch(
        "metaeditor_safetensors.controllers.thumbnail_controller.filepath_to_data_uri",
        side_effect=ValueError("bad image"),
    )
    controller = ThumbnailController(
        metadata,
        view,
        file_dialog_getter=lambda *_, **__: ("broken.png", ""),
    )

    controller.on_set_thumbnail_requested()

    assert metadata.get_value("modelspec.thumbnail") in (None, "")
    assert view.messages[-1][0].startswith("Error setting thumbnail")


def test_clear_thumbnail(metadata, view):
    metadata.set_value("modelspec.thumbnail", "data", source=ChangeSource.PROGRAMMATIC)
    controller = ThumbnailController(metadata, view)

    controller.on_clear_thumbnail_requested()

    assert metadata.get_value("modelspec.thumbnail") == ""
    assert view.messages[-1] == ("Thumbnail cleared.", 3000)


def test_thumbnail_drop_delegates_to_set(metadata, view, mocker):
    mocker.patch(
        "metaeditor_safetensors.controllers.thumbnail_controller.filepath_to_data_uri",
        return_value="drop-uri",
    )
    controller = ThumbnailController(metadata, view)

    controller.on_thumbnail_dropped("drop.png")

    assert metadata.get_value("modelspec.thumbnail") == "drop-uri"
    assert view.messages[-1] == ("Thumbnail set.", 3000)


def test_view_thumbnail_without_data(metadata, view):
    controller = ThumbnailController(metadata, view)

    controller.on_view_thumbnail_requested()

    assert view.messages[-1] == ("No thumbnail to view.", 0)


def test_view_thumbnail_with_invalid_pixmap(metadata, view, mocker):
    metadata.set_value("modelspec.thumbnail", "data", source=ChangeSource.PROGRAMMATIC)
    mocker.patch(
        "metaeditor_safetensors.controllers.thumbnail_controller.data_uri_to_pixmap",
        return_value=None,
    )
    controller = ThumbnailController(metadata, view)

    controller.on_view_thumbnail_requested()

    assert view.messages[-1] == ("Invalid or empty thumbnail image.", 0)


def test_view_thumbnail_opens_dialog(metadata, view, mocker):
    metadata.set_value("modelspec.thumbnail", "data", source=ChangeSource.PROGRAMMATIC)
    pixmap = mocker.Mock()
    pixmap.isNull.return_value = False

    dummy_screen = mocker.Mock()
    dummy_screen.availableGeometry.return_value = DummyGeometry(0, 0, 1920, 1080)
    mocker.patch(
        "metaeditor_safetensors.controllers.thumbnail_controller.QApplication.primaryScreen",
        return_value=dummy_screen,
    )
    mocker.patch(
        "metaeditor_safetensors.controllers.thumbnail_controller.data_uri_to_pixmap",
        return_value=pixmap,
    )

    created_dialogs: list[DummyDialog] = []

    def dialog_factory(pix, parent):
        dlg = DummyDialog(pix, parent)
        created_dialogs.append(dlg)
        return cast(ThumbnailDialog, dlg)

    controller = ThumbnailController(
        metadata,
        view,
        dialog_factory=dialog_factory,
    )

    controller.on_view_thumbnail_requested()

    assert created_dialogs
    assert created_dialogs[-1].exec_called is True
