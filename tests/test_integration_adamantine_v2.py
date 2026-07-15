from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.errors import ValidationError
from ai_gateway.gateway import AIGateway
from ai_gateway.hashing import sha256_hex
from ai_gateway.integration.adamantine import (
    ADAMANTINE_AI_GATEWAY_EVIDENCE_V2,
    build_adamantine_ai_gateway_evidence_from_gateway_result_v1,
    build_adamantine_ai_gateway_evidence_from_gateway_result_v2,
    build_adamantine_ai_gateway_evidence_v2,
)
from ai_gateway.registry import AdapterRegistry


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "adamantine"
    / "ai_gateway_adamantine_evidence_v2.json"
)
SOURCE_INPUT = {
    "task_type": "code_review",
    "model_family": "poi-v1",
    "input_payload": {
        "action": "evaluate_candidate",
        "prompt": "review this",
    },
}
POLICY_PACK = {
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


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text())


def _gateway_result(policy_pack: dict = POLICY_PACK) -> dict:
    adapter = PoIAdapter()
    registry = AdapterRegistry()
    registry.register("poi", adapter, manifest=adapter.manifest)
    return AIGateway(registry).process_governed_with_policy_binding_v1(
        "poi",
        SOURCE_INPUT,
        policy_pack,
    )


def test_direct_v2_export_matches_locked_fixture() -> None:
    expected = _fixture()

    evidence = build_adamantine_ai_gateway_evidence_v2(
        handoff=expected["handoff"],
        receipt=expected["receipt"],
        policy_binding=expected["policy_binding"],
        expected_context_hash=expected["expected_context_hash"],
    )

    assert evidence == expected
    assert evidence["evidence_version"] == ADAMANTINE_AI_GATEWAY_EVIDENCE_V2
    assert evidence["evidence_role"] == "evidence_only"
    assert set(evidence) == {
        "evidence_version",
        "source",
        "evidence_role",
        "expected_context_hash",
        "handoff",
        "receipt",
        "policy_binding",
    }
    assert "output" not in evidence


def test_from_result_v2_matches_locked_fixture_and_checks_output() -> None:
    result = _gateway_result()
    expected = _fixture()

    evidence = build_adamantine_ai_gateway_evidence_from_gateway_result_v2(
        gateway_result=result,
        expected_context_hash=result["handoff"]["context_hash"],
    )

    assert evidence == expected


def test_from_result_v2_accepts_coherent_rejected_policy_evidence() -> None:
    denied_policy = json.loads(json.dumps(POLICY_PACK))
    denied_policy["adapter_policies"]["poi"]["allowed_task_types"] = [
        "documentation"
    ]
    result = _gateway_result(denied_policy)

    evidence = build_adamantine_ai_gateway_evidence_from_gateway_result_v2(
        gateway_result=result,
        expected_context_hash=result["handoff"]["context_hash"],
    )

    assert evidence["handoff"]["policy_decision"] == "rejected"
    assert evidence["handoff"]["reason_id"] == "UNSUPPORTED_TASK"


def test_v1_exporter_rejects_policy_binding_even_when_none() -> None:
    fixture = _fixture()
    for value in (fixture["policy_binding"], None):
        with pytest.raises(
            ValueError,
            match="POLICY_BOUND_RESULT_REQUIRES_EVIDENCE_V2",
        ):
            build_adamantine_ai_gateway_evidence_from_gateway_result_v1(
                gateway_result={
                    "output": {},
                    "handoff": fixture["handoff"],
                    "receipt": fixture["receipt"],
                    "policy_binding": value,
                },
                expected_context_hash=fixture["expected_context_hash"],
            )


def test_v1_exporter_cannot_hide_binding_with_mapping_subclass() -> None:
    fixture = _fixture()

    class _HidingBindingDict(dict):
        def __contains__(self, key: object) -> bool:
            if key == "policy_binding":
                return False
            return super().__contains__(key)

    with pytest.raises(ValueError, match="GATEWAY_RESULT_SCHEMA_INVALID"):
        build_adamantine_ai_gateway_evidence_from_gateway_result_v1(
            gateway_result=_HidingBindingDict(
                {
                    "handoff": fixture["handoff"],
                    "receipt": fixture["receipt"],
                    "policy_binding": fixture["policy_binding"],
                }
            ),
            expected_context_hash=fixture["expected_context_hash"],
        )

    class _StringSubclass(str):
        pass

    result = {
        "handoff": fixture["handoff"],
        "receipt": fixture["receipt"],
        _StringSubclass("policy_binding"): fixture["policy_binding"],
    }
    with pytest.raises(ValidationError, match="SCHEMA_VIOLATION"):
        build_adamantine_ai_gateway_evidence_from_gateway_result_v1(
            gateway_result=result,
            expected_context_hash=fixture["expected_context_hash"],
        )


def test_v2_expected_context_hash_rejects_string_subclass_spoofing() -> None:
    fixture = _fixture()

    class _SpoofingHash(str):
        def __len__(self) -> int:
            return 64

        def __iter__(self):
            return iter("a" * 64)

        def __eq__(self, _other: object) -> bool:
            return True

    with pytest.raises(ValueError, match="INVALID_CONTEXT_HASH"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=fixture["handoff"],
            receipt=fixture["receipt"],
            policy_binding=fixture["policy_binding"],
            expected_context_hash=_SpoofingHash("evil"),
        )


@pytest.mark.parametrize("bad_hash", ["", "short", "A" * 64])
def test_v2_invalid_expected_context_hash_rejects(bad_hash: str) -> None:
    fixture = _fixture()
    with pytest.raises(ValueError, match="INVALID_CONTEXT_HASH"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=fixture["handoff"],
            receipt=fixture["receipt"],
            policy_binding=fixture["policy_binding"],
            expected_context_hash=bad_hash,
        )


@pytest.mark.parametrize(
    "field,error",
    [
        ("handoff", "MISSING_HANDOFF"),
        ("receipt", "MISSING_RECEIPT"),
        ("policy_binding", "MISSING_POLICY_BINDING"),
    ],
)
def test_direct_v2_requires_exact_dict_artifacts(field: str, error: str) -> None:
    fixture = _fixture()
    values = {
        "handoff": fixture["handoff"],
        "receipt": fixture["receipt"],
        "policy_binding": fixture["policy_binding"],
    }

    class _DictSubclass(dict):
        pass

    for invalid in (None, _DictSubclass(values[field])):
        changed = dict(values)
        changed[field] = invalid
        with pytest.raises(ValueError, match=error):
            build_adamantine_ai_gateway_evidence_v2(
                **changed,
                expected_context_hash=fixture["expected_context_hash"],
            )


@pytest.mark.parametrize("artifact", ["handoff", "receipt", "policy_binding"])
def test_direct_v2_rejects_nested_string_subclasses(artifact: str) -> None:
    fixture = _fixture()

    class _StringSubclass(str):
        pass

    values = {
        "handoff": dict(fixture["handoff"]),
        "receipt": dict(fixture["receipt"]),
        "policy_binding": dict(fixture["policy_binding"]),
    }
    first_field = next(iter(values[artifact]))
    values[artifact][first_field] = _StringSubclass(values[artifact][first_field])

    with pytest.raises(ValidationError, match="SCHEMA_VIOLATION"):
        build_adamantine_ai_gateway_evidence_v2(
            **values,
            expected_context_hash=fixture["expected_context_hash"],
        )


def test_v2_context_receipt_and_binding_splices_reject() -> None:
    fixture = _fixture()
    with pytest.raises(ValueError, match="CONTEXT_HASH_MISMATCH"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=fixture["handoff"],
            receipt=fixture["receipt"],
            policy_binding=fixture["policy_binding"],
            expected_context_hash="d" * 64,
        )

    handoff = dict(fixture["handoff"])
    handoff["context_hash"] = "d" * 64
    binding = dict(fixture["policy_binding"])
    binding["handoff_hash"] = sha256_hex(handoff)
    with pytest.raises(ValueError, match="CONTEXT_ENVELOPE_HASH_MISMATCH"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=handoff,
            receipt=fixture["receipt"],
            policy_binding=binding,
            expected_context_hash="d" * 64,
        )

    receipt = dict(fixture["receipt"])
    receipt["adapter_id"] = "wallet"
    with pytest.raises(ValueError, match="RECEIPT_MISMATCH"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=fixture["handoff"],
            receipt=receipt,
            policy_binding=fixture["policy_binding"],
            expected_context_hash=fixture["expected_context_hash"],
        )

    binding = dict(fixture["policy_binding"])
    binding["receipt_hash"] = "d" * 64
    with pytest.raises(ValueError, match="POLICY_BINDING_RECEIPT_HASH_MISMATCH"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=fixture["handoff"],
            receipt=fixture["receipt"],
            policy_binding=binding,
            expected_context_hash=fixture["expected_context_hash"],
        )

    binding = dict(fixture["policy_binding"])
    binding["handoff_hash"] = "d" * 64
    with pytest.raises(ValueError, match="POLICY_BINDING_HANDOFF_HASH_MISMATCH"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=fixture["handoff"],
            receipt=fixture["receipt"],
            policy_binding=binding,
            expected_context_hash=fixture["expected_context_hash"],
        )


@pytest.mark.parametrize(
    "decision,reason_id",
    [
        ("accepted", "INTERNAL_ERROR"),
        ("rejected", "ACCEPTED"),
        ("rejected", "UNREGISTERED_REASON"),
    ],
)
def test_direct_v2_rejects_contradictory_reason_semantics(
    decision: str,
    reason_id: str,
) -> None:
    fixture = _fixture()
    handoff = dict(fixture["handoff"])
    receipt = dict(fixture["receipt"])
    handoff["policy_decision"] = decision
    receipt["policy_decision"] = decision
    handoff["reason_id"] = reason_id
    receipt["reason_id"] = reason_id

    with pytest.raises(ValueError, match="EVIDENCE_SEMANTICS_MISMATCH"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=handoff,
            receipt=receipt,
            policy_binding=fixture["policy_binding"],
            expected_context_hash=fixture["expected_context_hash"],
        )


def test_v2_gateway_result_shape_and_missing_artifacts_reject() -> None:
    result = _gateway_result()

    class _DictSubclass(dict):
        pass

    for invalid in (
        _DictSubclass(result),
        {key: value for key, value in result.items() if key != "output"},
        {**result, "unknown": True},
    ):
        with pytest.raises(ValueError, match="GATEWAY_RESULT_SCHEMA_INVALID"):
            build_adamantine_ai_gateway_evidence_from_gateway_result_v2(
                gateway_result=invalid,
                expected_context_hash=result["handoff"]["context_hash"],
            )

    errors = {
        "output": "MISSING_OUTPUT",
        "handoff": "MISSING_HANDOFF",
        "receipt": "MISSING_RECEIPT",
        "policy_binding": "MISSING_POLICY_BINDING",
    }
    for field, error in errors.items():
        changed = dict(result)
        changed[field] = None
        with pytest.raises(ValueError, match=error):
            build_adamantine_ai_gateway_evidence_from_gateway_result_v2(
                gateway_result=changed,
                expected_context_hash=result["handoff"]["context_hash"],
            )


def test_v2_gateway_result_rejects_string_subclass_key() -> None:
    result = _gateway_result()

    class _StringSubclass(str):
        pass

    output = result.pop("output")
    result[_StringSubclass("output")] = output
    with pytest.raises(ValidationError, match="SCHEMA_VIOLATION"):
        build_adamantine_ai_gateway_evidence_from_gateway_result_v2(
            gateway_result=result,
            expected_context_hash=result["handoff"]["context_hash"],
        )


def test_v2_rejects_caller_selected_receipt_profile_even_when_rehashed() -> None:
    fixture = _fixture()
    receipt = dict(fixture["receipt"])
    receipt["determinism_profile"] = "md5-caller-selected"
    binding = dict(fixture["policy_binding"])
    binding["receipt_hash"] = sha256_hex(receipt)

    with pytest.raises(ValueError, match="UNSUPPORTED_DETERMINISM_PROFILE"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=fixture["handoff"],
            receipt=receipt,
            policy_binding=binding,
            expected_context_hash=fixture["expected_context_hash"],
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("adapter", "wallet"),
        ("task_type", "documentation"),
        ("context_hash", "d" * 64),
        ("reason_id", "INTERNAL_ERROR"),
        ("output_payload", {"changed": True}),
    ],
)
def test_v2_from_result_rejects_output_splice(field: str, value: object) -> None:
    result = _gateway_result()
    result["output"] = dict(result["output"])
    result["output"][field] = value

    with pytest.raises(ValueError, match="OUTPUT_EVIDENCE_MISMATCH"):
        build_adamantine_ai_gateway_evidence_from_gateway_result_v2(
            gateway_result=result,
            expected_context_hash=result["handoff"]["context_hash"],
        )


@pytest.mark.parametrize("artifact", ["handoff", "receipt", "policy_binding"])
def test_v2_rejects_validated_hidden_authority_fields(
    artifact: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_gateway.integration import adamantine as module

    fixture = _fixture()
    validators = {
        "handoff": "validate_handoff_v1",
        "receipt": "validate_receipt_v1",
        "policy_binding": "validate_policy_binding_v1",
    }
    for name, validator in validators.items():
        returned = {"override": True} if name == artifact else fixture[name]
        monkeypatch.setattr(module, validator, lambda _value, result=returned: result)

    with pytest.raises(ValueError, match="AUTHORITY_FIELD_FORBIDDEN"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=fixture["handoff"],
            receipt=fixture["receipt"],
            policy_binding=fixture["policy_binding"],
            expected_context_hash=fixture["expected_context_hash"],
        )


def test_v2_export_returns_detached_artifact_copies() -> None:
    fixture = _fixture()
    handoff = dict(fixture["handoff"])
    receipt = dict(fixture["receipt"])
    binding = dict(fixture["policy_binding"])
    evidence = build_adamantine_ai_gateway_evidence_v2(
        handoff=handoff,
        receipt=receipt,
        policy_binding=binding,
        expected_context_hash=fixture["expected_context_hash"],
    )

    handoff["adapter"] = "mutated"
    receipt["adapter_id"] = "mutated"
    binding["policy_pack_id"] = "mutated"

    assert evidence == fixture


def test_v2_hash_backend_exception_never_returns_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ai_gateway.integration import adamantine as module

    fixture = _fixture()
    monkeypatch.setattr(
        module,
        "sha256_hex",
        lambda _value: (_ for _ in ()).throw(RuntimeError("hash failed")),
    )
    with pytest.raises(RuntimeError, match="hash failed"):
        build_adamantine_ai_gateway_evidence_v2(
            handoff=fixture["handoff"],
            receipt=fixture["receipt"],
            policy_binding=fixture["policy_binding"],
            expected_context_hash=fixture["expected_context_hash"],
        )
