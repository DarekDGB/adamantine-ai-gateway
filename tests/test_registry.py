from copy import deepcopy

import pytest

from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.errors import AdapterError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


class DummyAdapter:
    pass


class BadManifestAdapter:
    @property
    def manifest(self) -> str:
        return "not-a-dict"


class StickyList(list):
    def __deepcopy__(self, memo):  # type: ignore[no-untyped-def]
        return self


class StickyDict(dict):
    def __deepcopy__(self, memo):  # type: ignore[no-untyped-def]
        return self


class FlipItemsDict(dict):
    def items(self):  # type: ignore[no-untyped-def]
        for key, value in super().items():
            yield key, "wallet" if key == "adapter_id" else value


class ExplodingItemsDict(dict):
    def items(self):  # type: ignore[no-untyped-def]
        raise RuntimeError("manifest serialization failed")


class HostileName(str):
    def __ne__(self, other):  # type: ignore[no-untyped-def]
        return False


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


def test_registry_rejects_string_subclass_names_for_all_operations() -> None:
    registry = AdapterRegistry()
    name = HostileName("poi")

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        registry.register(name, DummyAdapter(), deepcopy(VALID_MANIFEST))
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        registry.get(name)
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        registry.get_manifest(name)

    assert registry.names() == ()


def test_registry_rejects_duplicate_registration() -> None:
    registry = AdapterRegistry()
    registry.register("poi", DummyAdapter())

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        registry.register("poi", DummyAdapter())


def test_registry_rejects_unknown_adapter_lookup() -> None:
    registry = AdapterRegistry()

    with pytest.raises(AdapterError, match=ReasonID.ADAPTER_NOT_REGISTERED.value):
        registry.get("poi")


def test_registry_rejects_unknown_manifest_lookup() -> None:
    registry = AdapterRegistry()

    with pytest.raises(AdapterError, match=ReasonID.ADAPTER_NOT_REGISTERED.value):
        registry.get_manifest("poi")


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


def test_registry_deep_copies_nested_manifest_state_on_registration() -> None:
    registry = AdapterRegistry()
    manifest = deepcopy(VALID_MANIFEST)

    registry.register("poi", DummyAdapter(), manifest)
    manifest["supported_actions"].append("tampered_action")
    manifest["failure_reason_ids"].clear()

    stored = registry.get_manifest("poi")
    assert stored["supported_actions"] == VALID_MANIFEST["supported_actions"]
    assert stored["failure_reason_ids"] == VALID_MANIFEST["failure_reason_ids"]


def test_registry_returns_deep_copy_of_nested_manifest_state() -> None:
    registry = AdapterRegistry()
    registry.register("poi", DummyAdapter(), deepcopy(VALID_MANIFEST))

    returned = registry.get_manifest("poi")
    returned["supported_actions"].append("tampered_action")
    returned["failure_reason_ids"].clear()

    stored = registry.get_manifest("poi")
    assert stored["supported_actions"] == VALID_MANIFEST["supported_actions"]
    assert stored["failure_reason_ids"] == VALID_MANIFEST["failure_reason_ids"]


def test_registry_normalizes_hostile_container_copy_hooks() -> None:
    manifest = StickyDict(deepcopy(VALID_MANIFEST))
    supported_actions = StickyList(manifest["supported_actions"])
    manifest["supported_actions"] = supported_actions
    registry = AdapterRegistry()

    registry.register("poi", DummyAdapter(), manifest)
    supported_actions.append("caller_tamper")
    manifest["failure_reason_ids"].clear()

    returned = registry.get_manifest("poi")
    assert type(returned) is dict
    assert type(returned["supported_actions"]) is list
    assert returned["supported_actions"] == VALID_MANIFEST["supported_actions"]
    assert returned["failure_reason_ids"] == VALID_MANIFEST["failure_reason_ids"]

    returned["supported_actions"].append("returned_tamper")
    assert registry.get_manifest("poi")["supported_actions"] == VALID_MANIFEST["supported_actions"]


def test_registry_checks_normalized_manifest_identity_before_mutating_state() -> None:
    registry = AdapterRegistry()
    manifest = FlipItemsDict(deepcopy(VALID_MANIFEST))

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        registry.register("poi", DummyAdapter(), manifest)

    assert registry.names() == ()
    with pytest.raises(AdapterError, match=ReasonID.ADAPTER_NOT_REGISTERED.value):
        registry.get("poi")

    registry.register("poi", DummyAdapter(), deepcopy(VALID_MANIFEST))
    assert registry.get_manifest("poi")["adapter_id"] == "poi"


def test_registry_normalization_failure_leaves_registry_unchanged() -> None:
    registry = AdapterRegistry()
    manifest = ExplodingItemsDict(deepcopy(VALID_MANIFEST))

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value) as error:
        registry.register("poi", DummyAdapter(), manifest)

    assert isinstance(error.value.__cause__, RuntimeError)
    assert registry.names() == ()
    with pytest.raises(AdapterError, match=ReasonID.ADAPTER_NOT_REGISTERED.value):
        registry.get_manifest("poi")


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


def test_registry_rejects_non_dict_adapter_manifest_attribute() -> None:
    registry = AdapterRegistry()

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        registry.register("poi", BadManifestAdapter())
