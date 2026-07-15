from __future__ import annotations

import copy
from typing import Callable

import pytest

import ai_gateway.gateway as gateway_module
from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.errors import AdapterError, ContractError, PolicyError
from ai_gateway.gateway import AIGateway
from ai_gateway.handoff import build_handoff_v1
from ai_gateway.policy_binding import (
    _build_policy_binding_v1,
    _capture_policy_pack_v1,
)
from ai_gateway.reason_ids import ReasonID
from ai_gateway.receipt import build_receipt_v1
from ai_gateway.registry import AdapterRegistry


SOURCE_INPUT = {
    "task_type": "code_review",
    "model_family": "poi-v1",
    "input_payload": {
        "action": "evaluate_candidate",
        "prompt": "review this",
    },
}


def _policy_pack(*, allow_code_review: bool = True) -> dict:
    task_types = ["code_review", "documentation"] if allow_code_review else ["documentation"]
    return {
        "policypack_version": "policy_pack_v1",
        "policypack_id": "d2-policy",
        "policypack_version_id": "v1",
        "default_decision": "deny",
        "adapter_policies": {
            "poi": {
                "allowed_task_types": task_types,
                "allowed_model_families": ["poi-v1"],
                "allowed_actions": ["evaluate_candidate"],
            }
        },
        "notes": "D2 canonical policy snapshot",
    }


def _gateway(adapter: object | None = None, *, with_manifest: bool = True) -> AIGateway:
    resolved = adapter or PoIAdapter()
    registry = AdapterRegistry()
    manifest = PoIAdapter().manifest if with_manifest else None
    registry.register("poi", resolved, manifest=manifest)
    return AIGateway(registry)


def _assert_atomic_failure(result: dict, reason_id: ReasonID) -> None:
    assert set(result) == {"output", "receipt", "handoff", "policy_binding"}
    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == reason_id.value
    assert result["receipt"] is None
    assert result["handoff"] is None
    assert result["policy_binding"] is None


def _valid_components(source_input: dict | None = None) -> tuple[dict, dict, dict, dict]:
    source = source_input or SOURCE_INPUT
    adapter = PoIAdapter()
    envelope = adapter.build_envelope(source)
    output = adapter.build_output(envelope)
    receipt = build_receipt_v1(
        manifest=adapter.manifest,
        envelope=envelope,
        output=output,
    )
    handoff = build_handoff_v1(envelope=envelope, output=output, receipt=receipt)
    return envelope, output, receipt, handoff


def test_bound_governed_acceptance_is_complete_deterministic_and_kat_locked() -> None:
    gateway = _gateway()
    first = gateway.process_governed_with_policy_binding_v1(
        "poi", SOURCE_INPUT, _policy_pack()
    )
    second = gateway.process_governed_with_policy_binding_v1(
        "poi", SOURCE_INPUT, _policy_pack()
    )

    assert first == second
    assert set(first) == {"output", "receipt", "handoff", "policy_binding"}
    assert first["output"]["accepted"] is True
    assert first["policy_binding"] == {
        "policy_binding_version": "ai_gateway_policy_binding_v1",
        "policy_pack_contract_version": "policy_pack_v1",
        "policy_pack_id": "d2-policy",
        "policy_pack_version_id": "v1",
        "policy_pack_hash": "87d3c7f9fcfe8d7f84648c272b5793b0a15cf634f1a02536d606e88232f131fa",
        "receipt_hash": "ba04340d93e658eb243fef7f060c16b52aeecbc4a100806931f8b8463c0d41e6",
        "handoff_hash": "77f576ef98296e59e45f9bc104165a77def827ae7aa9a1368ca313321533462b",
    }


def test_valid_policy_denial_returns_complete_rejected_bound_chain() -> None:
    result = _gateway().process_governed_with_policy_binding_v1(
        "poi", SOURCE_INPUT, _policy_pack(allow_code_review=False)
    )

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert result["receipt"]["policy_decision"] == "rejected"
    assert result["handoff"]["policy_decision"] == "rejected"
    assert result["policy_binding"] is not None


def test_policy_denials_bind_the_actual_distinct_evaluated_envelopes() -> None:
    first = _gateway().process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(allow_code_review=False),
    )
    second_input = copy.deepcopy(SOURCE_INPUT)
    second_input["input_payload"]["prompt"] = "different denied operation"
    second = _gateway().process_governed_with_policy_binding_v1(
        "poi",
        second_input,
        _policy_pack(allow_code_review=False),
    )

    assert first["output"]["context_hash"] != second["output"]["context_hash"]
    assert first["receipt"]["envelope_hash"] != second["receipt"]["envelope_hash"]
    assert first["policy_binding"] != second["policy_binding"]


class _MutatingAdapter(PoIAdapter):
    def __init__(self, mutation: Callable[[], None]) -> None:
        self._mutation = mutation

    def build_envelope(self, source_input: dict) -> dict:
        self._mutation()
        return super().build_envelope(source_input)


@pytest.mark.parametrize(
    "initial_allow,mutated_allow,expected_accept",
    [(False, True, False), (True, False, True)],
)
def test_policy_is_captured_before_adapter_mutation(
    initial_allow: bool,
    mutated_allow: bool,
    expected_accept: bool,
) -> None:
    caller_policy = _policy_pack(allow_code_review=initial_allow)
    expected_hash = _capture_policy_pack_v1(copy.deepcopy(caller_policy)).policy_pack_hash

    def mutate() -> None:
        replacement = _policy_pack(allow_code_review=mutated_allow)
        caller_policy.clear()
        caller_policy.update(replacement)
        caller_policy["policypack_id"] = "mutated-after-capture"

    result = _gateway(_MutatingAdapter(mutate)).process_governed_with_policy_binding_v1(
        "poi", SOURCE_INPUT, caller_policy
    )

    assert result["output"]["accepted"] is expected_accept
    assert result["policy_binding"]["policy_pack_id"] == "d2-policy"
    assert result["policy_binding"]["policy_pack_hash"] == expected_hash


def test_caller_mutation_after_return_cannot_change_binding() -> None:
    caller_policy = _policy_pack()
    result = _gateway().process_governed_with_policy_binding_v1(
        "poi", SOURCE_INPUT, caller_policy
    )
    locked = copy.deepcopy(result["policy_binding"])

    caller_policy["policypack_id"] = "changed"
    caller_policy["adapter_policies"]["poi"]["allowed_task_types"].clear()
    caller_policy["notes"] = "changed"

    assert result["policy_binding"] == locked


class _RecordingAdapter(PoIAdapter):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def build_envelope(self, source_input: dict) -> dict:
        self.calls.append("envelope")
        return super().build_envelope(source_input)


@pytest.mark.parametrize(
    "bad_policy,reason_id",
    [
        ({}, ReasonID.SCHEMA_VIOLATION),
        ({"policypack_version": "policy_pack_v1"}, ReasonID.MISSING_REQUIRED_FIELD),
        ({**_policy_pack(), "default_decision": "allow"}, ReasonID.POLICY_DENIED),
    ],
)
def test_malformed_policy_fails_before_adapter_callback(
    bad_policy: dict,
    reason_id: ReasonID,
) -> None:
    adapter = _RecordingAdapter()
    result = _gateway(adapter).process_governed_with_policy_binding_v1(
        "poi", SOURCE_INPUT, bad_policy
    )

    _assert_atomic_failure(result, reason_id)
    assert adapter.calls == []


class _DictSubclass(dict):
    pass


class _ListSubclass(list):
    pass


class _EqualitySpoofingStr(str):
    def __eq__(self, _other: object) -> bool:
        return True

    def __ne__(self, _other: object) -> bool:
        return False

    __hash__ = str.__hash__


@pytest.mark.parametrize("bad_policy", [_DictSubclass(_policy_pack()), None])
def test_non_exact_policy_root_fails_atomically(bad_policy: object) -> None:
    result = _gateway().process_governed_with_policy_binding_v1(
        "poi", SOURCE_INPUT, bad_policy
    )
    _assert_atomic_failure(result, ReasonID.SCHEMA_VIOLATION)


def test_nested_list_subclass_and_excessive_adapter_count_fail_atomically() -> None:
    list_subclass = _policy_pack()
    list_subclass["adapter_policies"]["poi"]["allowed_actions"] = _ListSubclass(
        ["evaluate_candidate"]
    )
    _assert_atomic_failure(
        _gateway().process_governed_with_policy_binding_v1(
            "poi", SOURCE_INPUT, list_subclass
        ),
        ReasonID.SCHEMA_VIOLATION,
    )

    too_many = _policy_pack()
    template = too_many["adapter_policies"].pop("poi")
    too_many["adapter_policies"] = {
        f"adapter-{index}": copy.deepcopy(template) for index in range(1001)
    }
    _assert_atomic_failure(
        _gateway().process_governed_with_policy_binding_v1(
            "poi", SOURCE_INPUT, too_many
        ),
        ReasonID.SCHEMA_VIOLATION,
    )


@pytest.mark.parametrize("artifact", ["envelope", "output"])
def test_adapter_artifact_string_subclasses_cannot_spoof_alignment(
    artifact: str,
) -> None:
    class _SpoofingAdapter(PoIAdapter):
        def build_envelope(self, source_input: dict) -> dict:
            envelope = super().build_envelope(source_input)
            if artifact == "envelope":
                envelope["adapter"] = _EqualitySpoofingStr("wallet")
            return envelope

        def build_output(self, envelope: dict) -> dict:
            output = super().build_output(envelope)
            if artifact == "output":
                output["adapter"] = _EqualitySpoofingStr("wallet")
            return output

    result = _gateway(_SpoofingAdapter()).process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(),
    )

    _assert_atomic_failure(result, ReasonID.SCHEMA_VIOLATION)


@pytest.mark.parametrize(
    "field,value",
    [
        ("reason_id", _EqualitySpoofingStr("INTERNAL_ERROR")),
        ("context_hash", _EqualitySpoofingStr("evil")),
    ],
)
def test_adapter_output_string_subclasses_cannot_spoof_semantics(
    field: str,
    value: str,
) -> None:
    class _SpoofingAdapter(PoIAdapter):
        def build_output(self, envelope: dict) -> dict:
            output = super().build_output(envelope)
            output[field] = value
            return output

    result = _gateway(_SpoofingAdapter()).process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(),
    )

    _assert_atomic_failure(result, ReasonID.SCHEMA_VIOLATION)


def test_capture_and_materialization_backend_failures_are_atomic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gateway_module,
        "_capture_policy_pack_v1",
        lambda _policy: (_ for _ in ()).throw(RuntimeError("capture failed")),
    )
    _assert_atomic_failure(
        _gateway().process_governed_with_policy_binding_v1(
            "poi", SOURCE_INPUT, _policy_pack()
        ),
        ReasonID.INTERNAL_ERROR,
    )

    monkeypatch.setattr(
        gateway_module,
        "_capture_policy_pack_v1",
        _capture_policy_pack_v1,
    )
    monkeypatch.setattr(
        gateway_module,
        "_materialize_policy_pack_v1",
        lambda _snapshot: (_ for _ in ()).throw(RuntimeError("materialize failed")),
    )
    _assert_atomic_failure(
        _gateway().process_governed_with_policy_binding_v1(
            "poi", SOURCE_INPUT, _policy_pack()
        ),
        ReasonID.INTERNAL_ERROR,
    )


def test_registry_and_binding_backend_failures_are_atomic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _gateway()
    monkeypatch.setattr(
        gateway._registry,
        "get_manifest",
        lambda _name: (_ for _ in ()).throw(RuntimeError("registry failed")),
    )
    _assert_atomic_failure(
        gateway.process_governed_with_policy_binding_v1("poi", SOURCE_INPUT, _policy_pack()),
        ReasonID.INTERNAL_ERROR,
    )

    gateway = _gateway()
    monkeypatch.setattr(
        gateway_module,
        "_build_policy_binding_v1",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("binding failed")),
    )
    _assert_atomic_failure(
        gateway.process_governed_with_policy_binding_v1("poi", SOURCE_INPUT, _policy_pack()),
        ReasonID.INTERNAL_ERROR,
    )


def test_missing_manifest_and_invalid_adapter_name_fail_atomically() -> None:
    class _NoManifestAdapter:
        def build_envelope(self, source_input: dict) -> dict:
            return PoIAdapter().build_envelope(source_input)

        def build_output(self, envelope: dict) -> dict:
            return PoIAdapter().build_output(envelope)

    result = _gateway(
        _NoManifestAdapter(), with_manifest=False
    ).process_governed_with_policy_binding_v1(
        "poi", SOURCE_INPUT, _policy_pack()
    )
    _assert_atomic_failure(result, ReasonID.ADAPTER_VALIDATION_FAILED)

    result = _gateway().process_governed_with_policy_binding_v1(
        object(), SOURCE_INPUT, _policy_pack()
    )
    _assert_atomic_failure(result, ReasonID.SCHEMA_VIOLATION)
    assert result["output"]["adapter"] == "unknown"


def test_wallet_failure_result_uses_safe_task_type_without_reading_subclasses() -> None:
    result = _gateway().process_governed_with_policy_binding_v1(
        "wallet", _DictSubclass(task_type="unsafe"), {}
    )
    _assert_atomic_failure(result, ReasonID.SCHEMA_VIOLATION)
    assert result["output"]["task_type"] == "wallet_operation"


@pytest.mark.parametrize("bad_label", ["   ", "x" * 10_001, "\ud800"])
def test_failure_output_sanitizes_invalid_adapter_and_task_labels(
    bad_label: str,
) -> None:
    result = _gateway().process_governed_with_policy_binding_v1(
        bad_label,
        {"task_type": bad_label},
        _policy_pack(),
    )

    _assert_atomic_failure(result, ReasonID.ADAPTER_NOT_REGISTERED)
    assert result["output"]["adapter"] == "unknown"
    assert result["output"]["task_type"] == "unknown"


def test_failure_output_does_not_invoke_hostile_source_key_equality() -> None:
    class _ExplodingKey(str):
        __hash__ = str.__hash__

        def __eq__(self, _other: object) -> bool:
            raise RuntimeError("key equality must not run")

    result = _gateway().process_governed_with_policy_binding_v1(
        "poi",
        {_ExplodingKey("task_type"): "unsafe"},
        {},
    )

    _assert_atomic_failure(result, ReasonID.SCHEMA_VIOLATION)
    assert result["output"]["task_type"] == "unknown"


def test_internal_processing_exception_never_returns_partial_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _gateway()
    monkeypatch.setattr(
        gateway,
        "_process_components_for_policy_binding_v1",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("processing failed")),
    )
    _assert_atomic_failure(
        gateway.process_governed_with_policy_binding_v1(
            "poi", SOURCE_INPUT, _policy_pack()
        ),
        ReasonID.INTERNAL_ERROR,
    )


@pytest.mark.parametrize(
    "error,reason_id",
    [
        (RuntimeError("backend failed"), ReasonID.INTERNAL_ERROR),
        (PolicyError("POLICY_DENIED"), ReasonID.INTERNAL_ERROR),
        (ContractError("INVALID_ENVELOPE"), ReasonID.INVALID_ENVELOPE),
        (
            AdapterError("ADAPTER_VALIDATION_FAILED"),
            ReasonID.ADAPTER_VALIDATION_FAILED,
        ),
    ],
)
def test_pre_policy_adapter_exceptions_never_receive_bound_evidence(
    error: Exception,
    reason_id: ReasonID,
) -> None:
    class _FailingAdapter(PoIAdapter):
        def build_envelope(self, source_input: dict) -> dict:
            raise error

    result = _gateway(_FailingAdapter()).process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(),
    )

    _assert_atomic_failure(result, reason_id)


@pytest.mark.parametrize(
    "error,reason_id",
    [
        (AdapterError("ADAPTER_NOT_REGISTERED"), ReasonID.ADAPTER_NOT_REGISTERED),
        (RuntimeError("registry backend failed"), ReasonID.INTERNAL_ERROR),
    ],
)
def test_bound_processing_registry_lookup_failures_are_atomic(
    error: Exception,
    reason_id: ReasonID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _gateway()
    monkeypatch.setattr(
        gateway._registry,
        "get",
        lambda _name: (_ for _ in ()).throw(error),
    )

    result = gateway.process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(),
    )

    _assert_atomic_failure(result, reason_id)


def test_error_reason_mapping_survives_broken_exception_stringification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BrokenAdapterError(AdapterError):
        def __str__(self) -> str:
            raise RuntimeError("broken exception string")

    gateway = _gateway()
    monkeypatch.setattr(
        gateway._registry,
        "get_manifest",
        lambda _name: (_ for _ in ()).throw(_BrokenAdapterError()),
    )
    result = gateway.process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(),
    )

    _assert_atomic_failure(result, ReasonID.ADAPTER_VALIDATION_FAILED)


def test_error_reason_mapping_rejects_hostile_string_subclass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _HostileString(str):
        def __hash__(self) -> int:
            raise RuntimeError("hostile string hash")

    class _HostileAdapterError(AdapterError):
        def __str__(self) -> str:
            return _HostileString("ADAPTER_NOT_REGISTERED")

    gateway = _gateway()
    monkeypatch.setattr(
        gateway._registry,
        "get_manifest",
        lambda _name: (_ for _ in ()).throw(_HostileAdapterError()),
    )
    result = gateway.process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(),
    )

    _assert_atomic_failure(result, ReasonID.ADAPTER_VALIDATION_FAILED)


def test_bound_processing_rejects_envelope_and_manifest_identity_mismatch() -> None:
    class _WrongEnvelopeAdapter(PoIAdapter):
        def build_envelope(self, source_input: dict) -> dict:
            envelope = super().build_envelope(source_input)
            envelope["adapter"] = "wallet"
            return envelope

    result = _gateway(
        _WrongEnvelopeAdapter()
    ).process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(),
    )
    _assert_atomic_failure(result, ReasonID.INVALID_ENVELOPE)

    gateway = _gateway()
    manifest = gateway._registry.get_manifest("poi")
    manifest["adapter_id"] = "wallet"
    envelope, output = gateway._process_components_for_policy_binding_v1(
        adapter_name="poi",
        source_input=SOURCE_INPUT,
        policy_pack=_policy_pack(),
        manifest=manifest,
    )
    assert envelope is None
    assert output["reason_id"] == ReasonID.INVALID_ENVELOPE.value


def test_manifest_capability_rejection_is_pre_policy_and_unbound() -> None:
    source_input = copy.deepcopy(SOURCE_INPUT)
    source_input["input_payload"]["action"] = "undeclared-action"
    result = _gateway().process_governed_with_policy_binding_v1(
        "poi",
        source_input,
        _policy_pack(),
    )

    _assert_atomic_failure(result, ReasonID.ADAPTER_VALIDATION_FAILED)


@pytest.mark.parametrize("action", [pytest.param(None, id="missing"), "", 7])
def test_missing_or_invalid_action_is_pre_policy_and_unbound(action: object) -> None:
    source_input = copy.deepcopy(SOURCE_INPUT)
    if action is None:
        del source_input["input_payload"]["action"]
    else:
        source_input["input_payload"]["action"] = action

    result = _gateway().process_governed_with_policy_binding_v1(
        "poi",
        source_input,
        _policy_pack(),
    )

    _assert_atomic_failure(result, ReasonID.ADAPTER_VALIDATION_FAILED)


def test_unexpected_policy_backend_failure_is_atomic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gateway_module,
        "enforce_policy_for_adapter",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("policy backend failed")),
    )
    result = _gateway().process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(),
    )

    _assert_atomic_failure(result, ReasonID.INTERNAL_ERROR)


@pytest.mark.parametrize(
    "error,reason_id",
    [
        (ContractError("INVALID_OUTPUT"), ReasonID.INVALID_OUTPUT),
        (PolicyError("POLICY_DENIED"), ReasonID.POLICY_DENIED),
        (
            AdapterError("ADAPTER_VALIDATION_FAILED"),
            ReasonID.ADAPTER_VALIDATION_FAILED,
        ),
        (RuntimeError("output backend failed"), ReasonID.INTERNAL_ERROR),
    ],
)
def test_output_stage_exceptions_never_receive_bound_evidence(
    error: Exception,
    reason_id: ReasonID,
) -> None:
    class _FailingOutputAdapter(PoIAdapter):
        def build_output(self, envelope: dict) -> dict:
            raise error

    result = _gateway(
        _FailingOutputAdapter()
    ).process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        _policy_pack(),
    )

    _assert_atomic_failure(result, reason_id)


def test_internal_builder_rejects_each_cross_artifact_splice() -> None:
    envelope, output, receipt, handoff = _valid_components()
    snapshot = _capture_policy_pack_v1(_policy_pack())

    mutations = (
        ("receipt", "adapter_id", "wallet"),
        ("handoff", "adapter", "wallet"),
        ("handoff", "task_type", "documentation"),
        ("receipt", "envelope_hash", "a" * 64),
        ("handoff", "envelope_hash", "a" * 64),
        ("receipt", "output_hash", "b" * 64),
        ("handoff", "output_hash", "b" * 64),
        ("receipt", "policy_decision", "rejected"),
        ("handoff", "policy_decision", "rejected"),
        ("receipt", "reason_id", ReasonID.INTERNAL_ERROR.value),
        ("handoff", "reason_id", ReasonID.INTERNAL_ERROR.value),
        ("handoff", "context_hash", "c" * 64),
    )

    for artifact_name, field, value in mutations:
        changed_receipt = dict(receipt)
        changed_handoff = dict(handoff)
        target = changed_receipt if artifact_name == "receipt" else changed_handoff
        target[field] = value
        with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
            _build_policy_binding_v1(
                snapshot=snapshot,
                envelope=envelope,
                output=output,
                receipt=changed_receipt,
                handoff=changed_handoff,
            )


@pytest.mark.parametrize(
    "accepted,reason_id",
    [
        (True, ReasonID.INTERNAL_ERROR.value),
        (False, "ACCEPTED"),
        (False, "UNREGISTERED_REASON"),
    ],
)
def test_internal_builder_rejects_contradictory_reason_semantics(
    accepted: bool,
    reason_id: str,
) -> None:
    envelope, output, _, _ = _valid_components()
    output["accepted"] = accepted
    output["reason_id"] = reason_id
    receipt = build_receipt_v1(
        manifest=PoIAdapter().manifest,
        envelope=envelope,
        output=output,
    )
    handoff = build_handoff_v1(envelope=envelope, output=output, receipt=receipt)

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        _build_policy_binding_v1(
            snapshot=_capture_policy_pack_v1(_policy_pack()),
            envelope=envelope,
            output=output,
            receipt=receipt,
            handoff=handoff,
        )


def test_internal_builder_rejects_cross_operation_splice() -> None:
    envelope_a, output_a, receipt_a, _ = _valid_components()
    _, _, _, handoff_b = _valid_components(
        {
            **SOURCE_INPUT,
            "input_payload": {
                "action": "evaluate_candidate",
                "prompt": "different operation",
            },
        }
    )
    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        _build_policy_binding_v1(
            snapshot=_capture_policy_pack_v1(_policy_pack()),
            envelope=envelope_a,
            output=output_a,
            receipt=receipt_a,
            handoff=handoff_b,
        )


@pytest.mark.parametrize(
    "field,value",
    [("adapter", "wallet"), ("task_type", "documentation")],
)
def test_internal_builder_rejects_envelope_output_identity_mismatch(
    field: str,
    value: str,
) -> None:
    envelope, output, _, _ = _valid_components()
    envelope[field] = value
    receipt = build_receipt_v1(
        manifest=PoIAdapter().manifest,
        envelope=envelope,
        output=output,
    )
    handoff = build_handoff_v1(
        envelope=envelope,
        output=output,
        receipt=receipt,
    )

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        _build_policy_binding_v1(
            snapshot=_capture_policy_pack_v1(_policy_pack()),
            envelope=envelope,
            output=output,
            receipt=receipt,
            handoff=handoff,
        )


def test_internal_builder_rejects_caller_selected_receipt_profile() -> None:
    envelope, output, receipt, handoff = _valid_components()
    receipt["determinism_profile"] = "md5-caller-selected"

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        _build_policy_binding_v1(
            snapshot=_capture_policy_pack_v1(_policy_pack()),
            envelope=envelope,
            output=output,
            receipt=receipt,
            handoff=handoff,
        )


def test_internal_builder_requires_output_context_to_equal_envelope_hash() -> None:
    envelope, output, _, _ = _valid_components()
    output["context_hash"] = "d" * 64
    receipt = build_receipt_v1(
        manifest=PoIAdapter().manifest,
        envelope=envelope,
        output=output,
    )
    handoff = build_handoff_v1(
        envelope=envelope,
        output=output,
        receipt=receipt,
    )

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        _build_policy_binding_v1(
            snapshot=_capture_policy_pack_v1(_policy_pack()),
            envelope=envelope,
            output=output,
            receipt=receipt,
            handoff=handoff,
        )


def test_legacy_v1_governed_path_remains_exactly_unbound() -> None:
    result = _gateway().process_governed("poi", SOURCE_INPUT, _policy_pack())

    assert set(result) == {"output", "receipt", "handoff"}
    assert "policy_binding" not in result
