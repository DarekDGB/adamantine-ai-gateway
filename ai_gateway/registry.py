from typing import Any


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, Any] = {}

    def register(self, name: str, adapter: Any) -> None:
        if not name:
            raise ValueError("adapter name must be non-empty")
        if name in self._adapters:
            raise ValueError(f"adapter already registered: {name}")
        self._adapters[name] = adapter

    def get(self, name: str) -> Any:
        if name not in self._adapters:
            raise ValueError(f"adapter not registered: {name}")
        return self._adapters[name]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters.keys()))
