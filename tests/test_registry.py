import pytest

from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.errors import AdapterError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


class DummyAdapter:
    pass


VALID_MANIFEST = {
    "manifest_version": "adapter_manifest_v1",
    "adapter_id": "poi",
    "adapter_version": "0.3.0",
    "entrypoint": "tests.test_registry.DummyAdapter",
    "accepted_input_types": ["poi_candidate"],
    "supported_actions": ["evaluate_candidate"],
    "required_payload_fields": ["task_type", "model_family", "input_payload"],
    "optional_payload_fields": [],
    "output_contract": "ai_gateway_output_v1",
    "determinism_constraints": ["canonical_json_only"],
    "failure_reason_ids": ["ACCEPTED", "POLICY_DENIED"],
    "notes": "Registry test manifest",
}


def test_registry_register_and_get_adapter() -> None:
    registry = AdapterRegistry()
    adapter = DummyAdapter()

    registry.register("poi", adapter)

    assert registry.get("poi") is adapter


def test_registry_rejects_empty_name() -> None:
    registry = AdapterRegistry()

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        registry.register("", DummyAdapter())


def test_registry_rejects_duplicate_registration() -> None:
    registry = AdapterRegistry()
    registry.register("poi", DummyAdapter())

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        registry.register("poi", DummyAdapter())


def test_registry_rejects_unknown_adapter_lookup() -> None:
    registry = AdapterRegistry()

    with pytest.raises(AdapterError, match=ReasonID.ADAPTER_NOT_REGISTERED.value):
        registry.get("poi")


def test_registry_names_are_sorted() -> None:
    registry = AdapterRegistry()
    registry.register("zeta", DummyAdapter())
    registry.register("alpha", DummyAdapter())

    assert registry.names() == ("alpha", "zeta")


def test_registry_stores_explicit_valid_manifest() -> None:
    registry = AdapterRegistry()
    adapter = DummyAdapter()

    registry.register("poi", adapter, VALID_MANIFEST)

    assert registry.get_manifest("poi") == VALID_MANIFEST


def test_registry_uses_adapter_manifest_when_present() -> None:
    registry = AdapterRegistry()
    adapter = PoIAdapter()

    registry.register("poi", adapter)

    manifest = registry.get_manifest("poi")
    assert manifest["adapter_id"] == "poi"
    assert manifest["entrypoint"] == "ai_gateway.adapters.poi.PoIAdapter"


def test_registry_rejects_manifest_name_mismatch() -> None:
    registry = AdapterRegistry()
    bad_manifest = dict(VALID_MANIFEST)
    bad_manifest["adapter_id"] = "wallet"

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        registry.register("poi", DummyAdapter(), bad_manifest)


def test_registry_rejects_manifest_lookup_when_adapter_has_no_manifest() -> None:
    registry = AdapterRegistry()
    registry.register("poi", DummyAdapter())

    with pytest.raises(AdapterError, match=ReasonID.ADAPTER_VALIDATION_FAILED.value):
        registry.get_manifest("poi")
