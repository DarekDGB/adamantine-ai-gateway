from typing import Any

from ai_gateway.errors import AdapterError, ValidationError
from ai_gateway.reason_ids import ReasonID


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, Any] = {}

    def register(self, name: str, adapter: Any) -> None:
        if not name:
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)
        if name in self._adapters:
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)
        self._adapters[name] = adapter

    def get(self, name: str) -> Any:
        if name not in self._adapters:
            raise AdapterError(ReasonID.ADAPTER_NOT_REGISTERED.value)
        return self._adapters[name]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters.keys()))
