import logging
from enum import Enum
from typing import Any, Callable, Iterable, List, Optional

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import QWidget

from ..models.metadata import ChangeSource, Metadata
from ..models.modelspec import ModelType

logger = logging.getLogger(__name__)


class BindingType(Enum):
    TWO_WAY = "two_way"
    ONE_WAY = "one_way"
    ONE_WAY_TO_SOURCE = "one_way_to_source"


class FieldBinding:
    def __init__(
        self,
        field_key: str,
        widget: QWidget,
        getter: str,
        setter: str,
        signal: str,
        binding_type: BindingType = BindingType.TWO_WAY,
        to_metadata_converter: Optional[Callable] = None,
        from_metadata_converter: Optional[Callable] = None,
    ):
        self.field_key = field_key
        self.widget = widget
        self.getter = getter
        self.setter = setter
        self.signal = signal
        self.binding_type = binding_type

        self.to_metadata_converter = to_metadata_converter or (lambda x: x)
        self.from_metadata_converter = from_metadata_converter or (lambda x: x)


class WidgetBindingService:
    def __init__(self, metadata_service: Metadata, bindings: Iterable[FieldBinding]):
        self._metadata_service = metadata_service
        self._bindings: list[FieldBinding] = []

        for binding in bindings:
            self.add_binding(binding)

        logger.debug("WidgetBindingService initialized")

    def add_binding(self, binding: FieldBinding) -> None:
        self._bindings.append(binding)

        if binding.binding_type in [BindingType.TWO_WAY, BindingType.ONE_WAY_TO_SOURCE]:
            signal = getattr(binding.widget, binding.signal)
            signal.connect(
                lambda *_, _binding=binding: self._on_widget_changed(_binding)
            )

        logger.debug(
            f"Added binding: {binding.field_key} -> {binding.widget.__class__.__name__} ({binding.binding_type.value})"
        )

    def initialize_widgets(self) -> None:
        for binding in self._bindings:
            self.update_widget_from_metadata(binding.field_key)

    def _on_widget_changed(self, binding: FieldBinding) -> None:
        try:
            getter = getattr(binding.widget, binding.getter)
            raw_value = getter()
            converted_value = binding.to_metadata_converter(raw_value)

            self._metadata_service.set_value(
                binding.field_key,
                converted_value,
                source=ChangeSource.USER,
                source_widget=binding.widget,
            )

            logger.debug("Widget changed %s = %s", binding.field_key, converted_value)
        except Exception as exc:
            logger.error(
                "Error updating metadata from widget %s: %s",
                binding.field_key,
                exc,
            )

    def update_widget_from_metadata(
        self, field_key: str, exclude_widget: Optional[QWidget] = None
    ) -> None:
        logger.debug("Updating widget for field: %s", field_key)

        for binding in self._bindings:
            if binding.field_key != field_key:
                continue

            if binding.binding_type == BindingType.ONE_WAY_TO_SOURCE:
                continue

            if exclude_widget is not None and binding.widget is exclude_widget:
                logger.debug("Skipping source widget for field: %s", field_key)
                continue

            try:
                binding.widget.blockSignals(True)
                raw_value = self._metadata_service.get_value(binding.field_key, "")
                converted_value = binding.from_metadata_converter(raw_value)
                setter = getattr(binding.widget, binding.setter)
                setter(converted_value)
                logger.debug(
                    "Updated widget %s = %s", binding.field_key, converted_value
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(
                    "Error updating widget %s: %s",
                    binding.field_key,
                    exc,
                )
            finally:
                binding.widget.blockSignals(False)

    def clear_bindings(self) -> None:
        self._bindings.clear()


# Converter functions for common data types
def datetime_to_iso_string(dt: QDateTime) -> str:
    if isinstance(dt, QDateTime):
        return dt.toString(Qt.DateFormat.ISODateWithMs)
    return str(dt)


def iso_string_to_datetime(value: Any) -> QDateTime:
    if isinstance(value, str) and value:
        dt = QDateTime.fromString(value, Qt.DateFormat.ISODateWithMs)
        if not dt.isValid():
            dt = QDateTime.fromString(value, Qt.DateFormat.ISODate)
        if dt.isValid():
            return dt
    return QDateTime.currentDateTime()


def model_type_to_string(model_type: ModelType) -> str:
    if isinstance(model_type, ModelType):
        return model_type.value
    return str(model_type)


def string_to_model_type(value: Any) -> ModelType:
    if isinstance(value, str):
        for model_type in ModelType:
            if model_type.value == value:
                return model_type
    return ModelType.UNKNOWN


def string_to_tags(value: Any) -> List[str]:
    if isinstance(value, str):
        return [tag.strip() for tag in value.split(",") if tag.strip()]
    if isinstance(value, list):
        return [str(tag).strip() for tag in value if str(tag).strip()]
    return []


def tags_to_string(tags: Any) -> str:
    if isinstance(tags, list):
        return ", ".join(tags) if tags else ""
    if isinstance(tags, str):
        return tags
    return ""
