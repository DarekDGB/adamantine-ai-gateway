from typing import Any

from ai_gateway.errors import AdapterError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.types import Manifest
from ai_gateway.validation import validate_manifest_v1


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, Any] = {}
        self._manifests: dict[str, Manifest] = {}

    def register(self, name: str, adapter: Any, manifest: Manifest | None = None) -> None:
        if not name or not isinstance(name, str):
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

        if name in self._adapters:
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

        resolved_manifest = self._resolve_manifest(adapter, manifest)

        if resolved_manifest is not None and resolved_manifest["adapter_id"] != name:
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

        self._adapters[name] = adapter

        if resolved_manifest is not None:
            # store a copy to prevent external mutation
            self._manifests[name] = dict(resolved_manifest)

    def get(self, name: str) -> Any:
        if name not in self._adapters:
            raise AdapterError(ReasonID.ADAPTER_NOT_REGISTERED.value)
        return self._adapters[name]

    def get_manifest(self, name: str) -> Manifest:
        if name not in self._adapters:
            raise AdapterError(ReasonID.ADAPTER_NOT_REGISTERED.value)

        if name not in self._manifests:
            raise AdapterError(ReasonID.ADAPTER_VALIDATION_FAILED.value)

        return self._manifests[name]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters.keys()))

    @staticmethod
    def _resolve_manifest(adapter: Any, manifest: Manifest | None) -> Manifest | None:
        if manifest is not None:
            return validate_manifest_v1(manifest)

        # support both "manifest" and "MANIFEST"
        for attr in ("manifest", "MANIFEST"):
            candidate = getattr(adapter, attr, None)
            if candidate is not None:
                if isinstance(candidate, dict):
                    return validate_manifest_v1(candidate)
                return validate_manifest_v1(candidate)

        return None
