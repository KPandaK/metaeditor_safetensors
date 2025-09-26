from __future__ import annotations

from typing import Any, List

from ..services.utility import data_uri_to_pixmap, pixmap_to_data_uri
from ..services.widget_binding_service import (
    BindingType,
    FieldBinding,
    datetime_to_iso_string,
    iso_string_to_datetime,
    string_to_tags,
    tags_to_string,
)


def build_main_view_bindings(ui: Any) -> List[FieldBinding]:
    return [
        FieldBinding(
            "modelspec.title",
            ui.title_edit,
            "text",
            "setText",
            "textChanged",
        ),
        FieldBinding(
            "metaeditor.model_type",
            ui.type_select,
            "currentText",
            "setCurrentText",
            "currentTextChanged",
        ),
        FieldBinding(
            "modelspec.description",
            ui.description_edit,
            "toPlainText",
            "setPlainText",
            "textChanged",
        ),
        FieldBinding(
            "modelspec.tags",
            ui.tags_edit,
            "text",
            "setText",
            "textChanged",
            to_metadata_converter=string_to_tags,
            from_metadata_converter=tags_to_string,
        ),
        FieldBinding(
            "modelspec.author",
            ui.author_edit,
            "text",
            "setText",
            "textChanged",
        ),
        FieldBinding(
            "modelspec.date",
            ui.date_time_edit,
            "dateTime",
            "setDateTime",
            "dateTimeChanged",
            to_metadata_converter=datetime_to_iso_string,
            from_metadata_converter=iso_string_to_datetime,
        ),
        FieldBinding(
            "modelspec.merged_from",
            ui.merged_from_edit,
            "text",
            "setText",
            "textChanged",
        ),
        FieldBinding(
            "modelspec.usage_hint",
            ui.usage_hint_edit,
            "toPlainText",
            "setPlainText",
            "textChanged",
        ),
        FieldBinding(
            "modelspec.license",
            ui.license_edit,
            "text",
            "setText",
            "textChanged",
        ),
        FieldBinding(
            "modelspec.thumbnail",
            ui.thumbnail_display,
            "pixmap",
            "setPixmap",
            "pixmapChanged",
            binding_type=BindingType.ONE_WAY,
            to_metadata_converter=pixmap_to_data_uri,
            from_metadata_converter=data_uri_to_pixmap,
        ),
    ]
