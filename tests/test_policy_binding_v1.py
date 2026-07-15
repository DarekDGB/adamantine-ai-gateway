from __future__ import annotations

import copy
from dataclasses import replace

import pytest

from ai_gateway.contracts.policy_binding_v1 import (
    AI_GATEWAY_POLICY_BINDING_V1,
    ALLOWED_POLICY_BINDING_FIELDS,
    REQUIRED_POLICY_BINDING_FIELDS,
)
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.policy_binding import (
    _PreflightBudget,
    _capture_policy_pack_v1,
    _materialize_policy_pack_v1,
    _preflight_exact_json,
    _snapshot_exact_json_artifact,
)
from ai_gateway.reason_ids import ReasonID
from ai_gateway.validation import validate_policy_binding_v1


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _policy_pack() -> dict:
    return {
        "policypack_version": "policy_pack_v1",
        "policypack_id": "d2-policy",
        "policypack_version_id": "v1",
        "default_decision": "deny",
        "adapter_policies": {
            "poi": {
                "allowed_task_types": ["code_review", "documentation"],
                "allowed_model_families": ["poi-v1"],
                "allowed_actions": ["evaluate_candidate"],
            }
        },
        "notes": "D2 canonical policy snapshot",
    }


def _binding() -> dict:
    return {
        "policy_binding_version": AI_GATEWAY_POLICY_BINDING_V1,
        "policy_pack_contract_version": "policy_pack_v1",
        "policy_pack_id": "d2-policy",
        "policy_pack_version_id": "v1",
        "policy_pack_hash": HASH_A,
        "receipt_hash": HASH_B,
        "handoff_hash": HASH_C,
    }


def _preflight(value: object) -> None:
    _preflight_exact_json(
        value,
        depth=0,
        active_containers=set(),
        budget=_PreflightBudget(),
    )


def test_policy_binding_contract_exact_field_lock() -> None:
    assert REQUIRED_POLICY_BINDING_FIELDS == (
        "policy_binding_version",
        "policy_pack_contract_version",
        "policy_pack_id",
        "policy_pack_version_id",
        "policy_pack_hash",
        "receipt_hash",
        "handoff_hash",
    )
    assert ALLOWED_POLICY_BINDING_FIELDS == frozenset(REQUIRED_POLICY_BINDING_FIELDS)


def test_capture_policy_pack_kat_and_plain_materialization() -> None:
    snapshot = _capture_policy_pack_v1(_policy_pack())

    assert snapshot.policy_pack_id == "d2-policy"
    assert snapshot.policy_pack_version_id == "v1"
    assert snapshot.policy_pack_hash == (
        "87d3c7f9fcfe8d7f84648c272b5793b0a15cf634f1a02536d606e88232f131fa"
    )
    materialized = _materialize_policy_pack_v1(snapshot)
    assert materialized == _policy_pack()
    assert type(materialized) is dict
    assert type(materialized["adapter_policies"]) is dict


def test_materialization_rejects_forged_snapshot_type_bytes_identity_and_hash() -> None:
    snapshot = _capture_policy_pack_v1(_policy_pack())

    class _SnapshotSubclass(type(snapshot)):
        pass

    subclassed = _SnapshotSubclass(
        canonical_bytes=snapshot.canonical_bytes,
        policy_pack_id=snapshot.policy_pack_id,
        policy_pack_version_id=snapshot.policy_pack_version_id,
        policy_pack_hash=snapshot.policy_pack_hash,
    )
    forged = (
        (subclassed, ContractError),
        (
            replace(snapshot, canonical_bytes=bytearray(snapshot.canonical_bytes)),
            ContractError,
        ),
        (replace(snapshot, canonical_bytes=b'{"invalid":true}'), ContractError),
        (replace(snapshot, canonical_bytes=b"not-json"), ValidationError),
        (
            replace(snapshot, canonical_bytes=b" " + snapshot.canonical_bytes),
            ContractError,
        ),
        (replace(snapshot, policy_pack_id="forged"), ContractError),
        (replace(snapshot, policy_pack_version_id="forged"), ContractError),
        (replace(snapshot, policy_pack_hash="0" * 64), ContractError),
    )
    for candidate, expected_error in forged:
        with pytest.raises(expected_error):
            _materialize_policy_pack_v1(candidate)


def test_object_key_order_normalizes_but_list_order_is_identity_bearing() -> None:
    original = _policy_pack()
    reordered = {
        "notes": original["notes"],
        "adapter_policies": {
            "poi": {
                "allowed_actions": ["evaluate_candidate"],
                "allowed_model_families": ["poi-v1"],
                "allowed_task_types": ["code_review", "documentation"],
            }
        },
        "default_decision": "deny",
        "policypack_version_id": "v1",
        "policypack_id": "d2-policy",
        "policypack_version": "policy_pack_v1",
    }
    list_reordered = copy.deepcopy(original)
    list_reordered["adapter_policies"]["poi"]["allowed_task_types"].reverse()

    assert _capture_policy_pack_v1(original).policy_pack_hash == _capture_policy_pack_v1(
        reordered
    ).policy_pack_hash
    assert _capture_policy_pack_v1(original).policy_pack_hash != _capture_policy_pack_v1(
        list_reordered
    ).policy_pack_hash


@pytest.mark.parametrize(
    "field,value",
    [
        ("policypack_id", "changed"),
        ("policypack_version_id", "v2"),
        ("notes", "changed"),
    ],
)
def test_every_identity_label_and_notes_changes_policy_hash(field: str, value: str) -> None:
    changed = _policy_pack()
    changed[field] = value
    assert _capture_policy_pack_v1(changed).policy_pack_hash != _capture_policy_pack_v1(
        _policy_pack()
    ).policy_pack_hash


class _DictSubclass(dict):
    pass


class _ListSubclass(list):
    pass


@pytest.mark.parametrize(
    "bad_value",
    [
        _DictSubclass(),
        _ListSubclass(),
        1.5,
        object(),
    ],
)
def test_preflight_rejects_subclasses_float_and_arbitrary_objects(bad_value: object) -> None:
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _preflight(bad_value)


@pytest.mark.parametrize("value", [None, True, 7, "safe"])
def test_preflight_accepts_exact_json_scalar_branches(value: object) -> None:
    _preflight(value)


def test_preflight_bounds_integer_size_and_counts_integer_text_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_gateway import policy_binding as module

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _preflight(1 << 4096)

    monkeypatch.setattr(module, "MAX_POLICY_SNAPSHOT_CANONICAL_BYTES", 2)
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _preflight(100)


def test_preflight_rejects_non_string_dict_key() -> None:
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _preflight({1: "bad"})


@pytest.mark.parametrize("container", [[], {}])
def test_preflight_rejects_cycles(container: list | dict) -> None:
    if type(container) is list:
        container.append(container)
    else:
        container["self"] = container
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _preflight(container)


def test_preflight_rejects_excessive_depth() -> None:
    value: list = []
    for _ in range(12):
        value = [value]
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _preflight(value)


def test_preflight_rejects_key_list_node_and_text_budgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_gateway import policy_binding as module

    monkeypatch.setattr(module, "MAX_KEYS", 1)
    with pytest.raises(ValidationError):
        _preflight({"a": 1, "b": 2})

    monkeypatch.setattr(module, "MAX_KEYS", 1000)
    monkeypatch.setattr(module, "MAX_LIST_ITEMS", 1)
    with pytest.raises(ValidationError):
        _preflight([1, 2])

    monkeypatch.setattr(module, "MAX_LIST_ITEMS", 1000)
    monkeypatch.setattr(module, "MAX_POLICY_SNAPSHOT_NODES", 2)
    with pytest.raises(ValidationError):
        _preflight([1, 2])

    monkeypatch.setattr(module, "MAX_POLICY_SNAPSHOT_NODES", 20_000)
    monkeypatch.setattr(module, "MAX_STRING_LENGTH", 1)
    with pytest.raises(ValidationError):
        _preflight("too long")

    monkeypatch.setattr(module, "MAX_STRING_LENGTH", 10_000)
    monkeypatch.setattr(module, "MAX_POLICY_SNAPSHOT_CANONICAL_BYTES", 3)
    with pytest.raises(ValidationError):
        _preflight("four")


def test_capture_rejects_lone_surrogate_and_overlong_binding_ids() -> None:
    surrogate = _policy_pack()
    surrogate["notes"] = "\ud800"
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _capture_policy_pack_v1(surrogate)

    for field in ("policypack_id", "policypack_version_id"):
        overlong = _policy_pack()
        overlong[field] = "x" * 257
        with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
            _capture_policy_pack_v1(overlong)


def test_capture_rejects_canonicalization_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_gateway import policy_binding as module

    monkeypatch.setattr(module, "canonical_json_bytes", lambda _value: (_ for _ in ()).throw(TypeError()))
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _capture_policy_pack_v1(_policy_pack())


def test_capture_post_canonical_size_guard_is_enforced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_gateway import policy_binding as module

    monkeypatch.setattr(module, "_preflight_exact_json", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(module, "canonical_json_bytes", lambda _value: b"x" * 101)
    monkeypatch.setattr(module, "MAX_POLICY_SNAPSHOT_CANONICAL_BYTES", 100)
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _capture_policy_pack_v1(_policy_pack())


def test_exact_artifact_snapshot_rejects_canonical_size_and_decode_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_gateway import policy_binding as module

    monkeypatch.setattr(
        module,
        "canonical_json_bytes",
        lambda _value: (_ for _ in ()).throw(TypeError("canonical failed")),
    )
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _snapshot_exact_json_artifact({"safe": True})

    monkeypatch.setattr(module, "canonical_json_bytes", lambda _value: b"x" * 101)
    monkeypatch.setattr(module, "MAX_POLICY_SNAPSHOT_CANONICAL_BYTES", 100)
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _snapshot_exact_json_artifact({"safe": True})

    monkeypatch.setattr(module, "MAX_POLICY_SNAPSHOT_CANONICAL_BYTES", 1_048_576)
    monkeypatch.setattr(module, "canonical_json_bytes", lambda _value: b"not-json")
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _snapshot_exact_json_artifact({"safe": True})

def test_validate_policy_binding_accepts_exact_contract() -> None:
    assert validate_policy_binding_v1(_binding()) == _binding()


@pytest.mark.parametrize("bad", [None, _DictSubclass(_binding())])
def test_validate_policy_binding_rejects_non_exact_dict(bad: object) -> None:
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_policy_binding_v1(bad)


def test_validate_policy_binding_rejects_non_string_and_unknown_keys() -> None:
    non_string_key = _binding()
    non_string_key[1] = "bad"
    with pytest.raises(ValidationError):
        validate_policy_binding_v1(non_string_key)

    unknown = _binding()
    unknown["hash_profile"] = "caller-selected"
    with pytest.raises(ValidationError):
        validate_policy_binding_v1(unknown)


@pytest.mark.parametrize("field", REQUIRED_POLICY_BINDING_FIELDS)
def test_validate_policy_binding_rejects_each_missing_field(field: str) -> None:
    binding = _binding()
    del binding[field]
    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_policy_binding_v1(binding)


def test_validate_policy_binding_rejects_none_non_string_and_empty_fields() -> None:
    binding = _binding()
    binding["policy_pack_id"] = None
    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_policy_binding_v1(binding)

    binding = _binding()
    binding["policy_pack_id"] = 1
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_policy_binding_v1(binding)

    binding = _binding()
    binding["policy_pack_id"] = ""
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_policy_binding_v1(binding)


@pytest.mark.parametrize(
    "field,value",
    [
        ("policy_binding_version", "wrong"),
        ("policy_pack_contract_version", "policy_pack_v2"),
    ],
)
def test_validate_policy_binding_rejects_wrong_versions(field: str, value: str) -> None:
    binding = _binding()
    binding[field] = value
    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_policy_binding_v1(binding)


@pytest.mark.parametrize("field", ["policy_pack_id", "policy_pack_version_id"])
def test_validate_policy_binding_rejects_overlong_and_invalid_utf8_ids(field: str) -> None:
    binding = _binding()
    binding[field] = "x" * 257
    with pytest.raises(ValidationError):
        validate_policy_binding_v1(binding)

    binding[field] = "\ud800"
    with pytest.raises(ValidationError):
        validate_policy_binding_v1(binding)


@pytest.mark.parametrize("bad_hash", ["short", "A" * 64, "g" * 64])
def test_validate_policy_binding_rejects_invalid_hashes(bad_hash: str) -> None:
    binding = _binding()
    binding["policy_pack_hash"] = bad_hash
    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_policy_binding_v1(binding)


def test_validate_policy_binding_rejects_canonical_backend_and_size_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ai_gateway.canonical as canonical
    import ai_gateway.validation as validation

    monkeypatch.setattr(canonical, "canonical_json_bytes", lambda _value: (_ for _ in ()).throw(TypeError()))
    with pytest.raises(ValidationError):
        validate_policy_binding_v1(_binding())

    monkeypatch.setattr(canonical, "canonical_json_bytes", lambda _value: b"x" * 5000)
    monkeypatch.setattr(validation, "MAX_POLICY_BINDING_ARTIFACT_BYTES", 4096)
    with pytest.raises(ValidationError):
        validate_policy_binding_v1(_binding())
