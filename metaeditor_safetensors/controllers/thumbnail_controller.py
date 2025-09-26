from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget

from ..models.metadata import ChangeSource, Metadata
from ..services.status_message_service import StatusMessageService
from ..services.utility import data_uri_to_pixmap, filepath_to_data_uri
from ..views.thumbnail_dialog import ThumbnailDialog

if TYPE_CHECKING:
    from ..views.main_view import MainView

DialogFactory = Callable[[QPixmap, QWidget], ThumbnailDialog]


class ThumbnailController(QObject):
    def __init__(
        self,
        metadata: Metadata,
        view: MainView,
        status_messages: StatusMessageService,
        *,
        file_dialog_getter: Callable[..., tuple[str, str]] | None = None,
        dialog_factory: DialogFactory = ThumbnailDialog,
    ) -> None:
        super().__init__()
        self._metadata = metadata
        self._view = view
        self._status_messages = status_messages
        self._get_open_file_name = file_dialog_getter or QFileDialog.getOpenFileName
        self._dialog_factory = dialog_factory

    @Slot()
    def on_set_thumbnail_requested(self) -> None:
        filepath, _ = self._get_open_file_name(
            self._view,
            "Select Thumbnail Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif *.webp *.svg *.ico);;All Files (*)",
        )
        if not filepath:
            return

        self._set_thumbnail_from_path(filepath)

    @Slot()
    def on_clear_thumbnail_requested(self) -> None:
        self._metadata.set_value(
            "modelspec.thumbnail", "", source=ChangeSource.PROGRAMMATIC
        )
        self._status_messages.info("Thumbnail cleared.")

    @Slot()
    def on_view_thumbnail_requested(self) -> None:
        data_uri = self._metadata.get_value("modelspec.thumbnail")
        if not data_uri:
            self._status_messages.info("No thumbnail to view.")
            return

        pixmap = data_uri_to_pixmap(data_uri)
        if pixmap is None or pixmap.isNull():
            self._status_messages.warning("Invalid or empty thumbnail image.")
            return

        dialog = self._dialog_factory(pixmap, self._view)
        self._center_dialog(dialog)
        dialog.exec()

    @Slot(str)
    def on_thumbnail_dropped(self, filepath: str) -> None:
        if not filepath:
            return
        self._set_thumbnail_from_path(filepath)

    def _set_thumbnail_from_path(self, filepath: str) -> None:
        try:
            data_uri = filepath_to_data_uri(filepath)
            self._metadata.set_value(
                "modelspec.thumbnail",
                data_uri,
                source=ChangeSource.PROGRAMMATIC,
            )
            self._status_messages.success("Thumbnail set.")
        except Exception as exc:  # pragma: no cover - defensive
            self._status_messages.error(f"Error setting thumbnail: {exc}")

    def _center_dialog(self, dialog: ThumbnailDialog) -> None:
        main_geometry = self._view.geometry()
        dialog_geometry = dialog.geometry()

        x = int(
            main_geometry.x() + (main_geometry.width() - dialog_geometry.width()) / 2
        )
        y = int(
            main_geometry.y() + (main_geometry.height() - dialog_geometry.height()) / 2
        )

        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            x = max(
                screen_geom.x(),
                min(x, screen_geom.right() - dialog_geometry.width()),
            )
            y = max(
                screen_geom.y(),
                min(y, screen_geom.bottom() - dialog_geometry.height()),
            )

        dialog.move(x, y)
