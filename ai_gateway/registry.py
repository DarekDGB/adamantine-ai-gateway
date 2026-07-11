import json
from typing import Any

from ai_gateway.canonical import canonical_json_bytes
from ai_gateway.errors import AdapterError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.types import Manifest
from ai_gateway.validation import validate_manifest_v1


def _snapshot_manifest(manifest: Manifest) -> Manifest:
    """Return a validated manifest containing only fresh JSON built-ins."""

    try:
        snapshot = json.loads(canonical_json_bytes(manifest))
        return validate_manifest_v1(snapshot)
    except Exception as exc:
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value) from exc


def _require_registry_name(name: Any) -> str:
    if type(name) is not str or not name:
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)
    return name


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, Any] = {}
        self._manifests: dict[str, Manifest] = {}

    def register(self, name: str, adapter: Any, manifest: Manifest | None = None) -> None:
        clean_name = _require_registry_name(name)

        if clean_name in self._adapters:
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

        resolved_manifest = self._resolve_manifest(adapter, manifest)
        normalized_manifest = (
            _snapshot_manifest(resolved_manifest)
            if resolved_manifest is not None
            else None
        )

        if normalized_manifest is not None and normalized_manifest["adapter_id"] != clean_name:
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

        self._adapters[clean_name] = adapter

        if normalized_manifest is not None:
            self._manifests[clean_name] = normalized_manifest

    def get(self, name: str) -> Any:
        clean_name = _require_registry_name(name)
        if clean_name not in self._adapters:
            raise AdapterError(ReasonID.ADAPTER_NOT_REGISTERED.value)
        return self._adapters[clean_name]

    def get_manifest(self, name: str) -> Manifest:
        clean_name = _require_registry_name(name)
        if clean_name not in self._adapters:
            raise AdapterError(ReasonID.ADAPTER_NOT_REGISTERED.value)

        if clean_name not in self._manifests:
            raise AdapterError(ReasonID.ADAPTER_VALIDATION_FAILED.value)

        # Return a fresh normalized snapshot so callers cannot mutate the
        # registered manifest, including through custom container subclasses.
        return _snapshot_manifest(self._manifests[clean_name])

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
