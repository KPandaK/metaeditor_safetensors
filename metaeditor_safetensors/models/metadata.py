import copy
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class ChangeSource(Enum):
    USER = "user"
    PROGRAMMATIC = "programmatic"


class Metadata:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._original_data: Dict[str, Any] = {}
        self._observers: List[Callable] = []

    def load_data(self, data: Dict[str, Any]):
        self._data = copy.deepcopy(data)
        self._original_data = copy.deepcopy(data)
        self._notify_observers(source=ChangeSource.PROGRAMMATIC)

    def get_all_data(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data)

    def get_value(self, key: str, default: Any = "") -> Any:
        return self._data.get(key, default)

    def set_value(
        self,
        key: str,
        value: Any,
        source: ChangeSource = ChangeSource.PROGRAMMATIC,
        source_widget: Any = None,
    ):
        # Equality testing to prevent unnecessary notifications
        current_value = self.get_value(key)
        if current_value == value:
            return

        if value == "":
            self._data.pop(key, None)
        else:
            self._data[key] = value

        # Notify with field-specific information
        self._notify_observers(field=key, source=source, source_widget=source_widget)

    def remove_key(self, key: str):
        if key in self._data:
            del self._data[key]
            self._notify_observers(field=key, source=ChangeSource.PROGRAMMATIC)

    def has_key(self, key: str) -> bool:
        return key in self._data

    def is_dirty(self) -> bool:
        return self._data != self._original_data

    def get_dirty_fields(self) -> Set[str]:
        original_keys = set(self._original_data.keys())
        current_keys = set(self._data.keys())

        changed_keys = set()

        # Check for modified and added keys
        for key in current_keys:
            if key not in original_keys or self._data[key] != self._original_data[key]:
                changed_keys.add(key)

        # Check for removed keys
        changed_keys.update(original_keys - current_keys)

        return changed_keys

    def mark_saved(self):
        self._original_data = copy.deepcopy(self._data)
        self._notify_observers(source=ChangeSource.PROGRAMMATIC)

    def add_observer(self, observer: Callable):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Callable):
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(
        self,
        field: Optional[str] = None,
        source: ChangeSource = ChangeSource.PROGRAMMATIC,
        source_widget: Any = None,
    ):
        for observer in self._observers:
            # Check if observer accepts the new parameters
            try:
                observer(field=field, source=source, source_widget=source_widget)
            except TypeError:
                # Fallback for old-style observers
                observer()
