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

        # Converter functions for data transformation
        self.to_metadata_converter = to_metadata_converter or (lambda x: x)
        self.from_metadata_converter = from_metadata_converter or (lambda x: x)


class WidgetBindingService:
    def __init__(self, metadata_service: Metadata):
        self._metadata_service = metadata_service
        self._bindings: List[FieldBinding] = []
        logger.debug("WidgetBindingService initialized")

    def add_binding(self, binding: FieldBinding) -> None:
        self._bindings.append(binding)

        # Connect widget signal for bindings that push widget -> model updates
        if binding.binding_type in [BindingType.TWO_WAY, BindingType.ONE_WAY_TO_SOURCE]:
            signal = getattr(binding.widget, binding.signal)
            signal.connect(lambda *_, _binding=binding: self._on_widget_changed(_binding))

        logger.debug(
            f"Added binding: {binding.field_key} -> {binding.widget.__class__.__name__} ({binding.binding_type.value})"
        )

    def add_bindings(self, bindings: Iterable[FieldBinding]) -> None:
        for binding in bindings:
            self.add_binding(binding)

    def _on_widget_changed(self, binding: FieldBinding) -> None:
        try:
            # Get value from widget
            getter = getattr(binding.widget, binding.getter)
            raw_value = getter()

            # Convert value if needed
            converted_value = binding.to_metadata_converter(raw_value)

            # Update metadata with source tracking
            self._metadata_service.set_value(
                binding.field_key,
                converted_value,
                source=ChangeSource.USER,
                source_widget=binding.widget,
            )

            logger.debug(f"Widget changed: {binding.field_key} = {converted_value}")

        except Exception as e:
            logger.error(
                f"Error updating metadata from widget {binding.field_key}: {e}"
            )

    def initialize_widgets_from_metadata(self) -> None:
        logger.debug("Initializing all widgets from metadata")
        for binding in self._bindings:
            self.update_widget_from_metadata(binding.field_key)

    def update_widget_from_metadata(
        self, field_key: str, exclude_widget: Optional[QWidget] = None
    ) -> None:
        logger.debug(f"Updating widget for field: {field_key}")

        for binding in self._bindings:
            if binding.field_key == field_key:
                # Only update widgets that allow model -> widget updates
                if binding.binding_type == BindingType.ONE_WAY_TO_SOURCE:
                    continue

                # Skip if this is the widget that triggered the change
                if exclude_widget is not None and binding.widget is exclude_widget:
                    logger.debug(f"Skipping source widget for field: {field_key}")
                    continue

                try:
                    # Block signals to prevent feedback during update
                    binding.widget.blockSignals(True)

                    # Get value from metadata
                    raw_value = self._metadata_service.get_value(binding.field_key, "")

                    # Convert value if needed
                    converted_value = binding.from_metadata_converter(raw_value)

                    # Set value on widget
                    setter = getattr(binding.widget, binding.setter)
                    setter(converted_value)

                    logger.debug(
                        f"Updated widget: {binding.field_key} = {converted_value}"
                    )

                except Exception as e:
                    logger.error(f"Error updating widget {binding.field_key}: {e}")
                finally:
                    # Re-enable signals
                    binding.widget.blockSignals(False)

    def clear_all_widgets(self) -> None:
        logger.debug("Clearing all widgets")

        for binding in self._bindings:
            try:
                binding.widget.blockSignals(True)

                # Set appropriate empty/default value based on widget type
                if binding.setter == "setText" or binding.setter == "setPlainText":
                    getattr(binding.widget, binding.setter)("")
                elif binding.setter == "setDateTime":
                    getattr(binding.widget, binding.setter)(QDateTime.currentDateTime())
                elif binding.setter == "setCurrentIndex":
                    # For comboboxes, set to first item (usually "Unknown")
                    getattr(binding.widget, binding.setter)(0)
                else:
                    # Try to set empty string as fallback
                    getattr(binding.widget, binding.setter)("")

            except Exception as e:
                logger.error(f"Error clearing widget {binding.field_key}: {e}")
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
        # Attempt to parse ISO 8601 format
        dt = QDateTime.fromString(value, Qt.DateFormat.ISODateWithMs)
        if not dt.isValid():
            # Fallback for format without milliseconds
            dt = QDateTime.fromString(value, Qt.DateFormat.ISODate)
        if dt.isValid():
            return dt
    # Return current time as fallback
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
    elif isinstance(value, list):
        return [str(tag).strip() for tag in value if str(tag).strip()]
    return []


def tags_to_string(tags):
    if isinstance(tags, list):
        return ", ".join(tags) if tags else ""
    elif isinstance(tags, str):
        return tags
    return ""

