from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.gateway import AIGateway
from ai_gateway.handoff import build_handoff_v1
from ai_gateway.reason_ids import ReasonID
from ai_gateway.receipt import build_receipt_v1
from ai_gateway.registry import AdapterRegistry
from ai_gateway.validation import (
    validate_envelope_v1,
    validate_handoff_v1,
    validate_output_v1,
    validate_receipt_v1,
)


VALID_POLICY_PACK = {
    "policypack_version": "policy_pack_v1",
    "policypack_id": "artifact-chain-lock",
    "policypack_version_id": "v1.0.0-lock",
    "default_decision": "deny",
    "adapter_policies": {
        "poi": {
            "allowed_task_types": ["code_review"],
            "allowed_model_families": ["poi-v1"],
            "allowed_actions": ["evaluate_candidate"],
        }
    },
    "notes": "Artifact chain invariant lock tests",
}


INVALID_POLICY_PACK = {
    "policypack_version": "policy_pack_v1",
    "policypack_id": "artifact-chain-lock-deny",
    "policypack_version_id": "v1.0.0-lock",
    "default_decision": "deny",
    "adapter_policies": {
        "poi": {
            "allowed_task_types": ["other_task"],
            "allowed_model_families": ["poi-v1"],
            "allowed_actions": ["evaluate_candidate"],
        }
    },
    "notes": "Artifact chain invariant negative tests",
}


SOURCE_INPUT = {
    "task_type": "code_review",
    "model_family": "poi-v1",
    "input_payload": {"action": "evaluate_candidate", "prompt": "review this"},
}


MANIFEST = {
    "manifest_version": "adapter_manifest_v1",
    "adapter_id": "poi",
    "adapter_version": "0.5.0",
    "entrypoint": "tests.test_artifact_chain_invariants.PoIAdapter",
    "accepted_input_types": ["poi_candidate"],
    "supported_actions": ["evaluate_candidate"],
    "required_payload_fields": ["task_type", "model_family", "input_payload"],
    "optional_payload_fields": [],
    "output_contract": "ai_gateway_output_v1",
    "determinism_constraints": [
        "same_input_same_envelope",
        "same_envelope_same_output",
        "canonical_json_only",
    ],
    "failure_reason_ids": [
        "ACCEPTED",
        "UNSUPPORTED_TASK",
        "UNSUPPORTED_MODEL",
        "INVALID_ENVELOPE",
        "INVALID_OUTPUT",
        "MISSING_REQUIRED_FIELD",
        "SCHEMA_VIOLATION",
        "ADAPTER_VALIDATION_FAILED",
        "POLICY_DENIED",
        "INTERNAL_ERROR",
    ],
    "notes": "Artifact chain lock manifest",
}


def _gateway() -> AIGateway:
    registry = AdapterRegistry()
    registry.register("poi", PoIAdapter(), manifest=MANIFEST)
    return AIGateway(registry)


def _envelope() -> dict:
    return {
        "contract_version": "ai_gateway_envelope_v1",
        "adapter": "poi",
        "task_type": SOURCE_INPUT["task_type"],
        "model_family": SOURCE_INPUT["model_family"],
        "input_payload": SOURCE_INPUT["input_payload"],
    }


def test_governed_artifact_chain_is_consistent_for_valid_input() -> None:
    result = _gateway().process_governed("poi", SOURCE_INPUT, VALID_POLICY_PACK)

    output = validate_output_v1(result["output"])
    receipt = validate_receipt_v1(result["receipt"])
    handoff = validate_handoff_v1(result["handoff"])

    assert output["accepted"] is True
    assert output["reason_id"] == "ACCEPTED"
    assert output["adapter"] == "poi"
    assert output["task_type"] == SOURCE_INPUT["task_type"]

    assert receipt["adapter_id"] == MANIFEST["adapter_id"]
    assert receipt["adapter_version"] == MANIFEST["adapter_version"]
    assert receipt["reason_id"] == output["reason_id"]
    assert receipt["policy_decision"] == "accepted"
    assert receipt["created_from_contract"] == output["contract_version"]

    assert handoff["adapter"] == output["adapter"]
    assert handoff["task_type"] == output["task_type"]
    assert handoff["reason_id"] == output["reason_id"]
    assert handoff["policy_decision"] == receipt["policy_decision"]
    assert handoff["context_hash"] == output["context_hash"]
    assert handoff["envelope_hash"] == receipt["envelope_hash"]
    assert handoff["output_hash"] == receipt["output_hash"]


def test_same_input_produces_same_artifact_chain_hashes() -> None:
    gateway = _gateway()

    first = gateway.process_governed("poi", SOURCE_INPUT, VALID_POLICY_PACK)
    second = gateway.process_governed("poi", SOURCE_INPUT, VALID_POLICY_PACK)

    assert first["output"] == second["output"]
    assert first["receipt"] == second["receipt"]
    assert first["handoff"] == second["handoff"]


def test_policy_denial_produces_consistent_rejected_chain() -> None:
    result = _gateway().process_governed("poi", SOURCE_INPUT, INVALID_POLICY_PACK)

    output = validate_output_v1(result["output"])
    receipt = validate_receipt_v1(result["receipt"])
    handoff = validate_handoff_v1(result["handoff"])

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert receipt["policy_decision"] == "rejected"
    assert receipt["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert handoff["policy_decision"] == "rejected"
    assert handoff["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert handoff["envelope_hash"] == receipt["envelope_hash"]
    assert handoff["output_hash"] == receipt["output_hash"]


def test_manifest_mutation_after_registration_does_not_change_stored_chain_identity() -> None:
    registry = AdapterRegistry()
    manifest = dict(MANIFEST)
    registry.register("poi", PoIAdapter(), manifest=manifest)
    manifest["adapter_version"] = "tampered"
    manifest["notes"] = "tampered"

    gateway = AIGateway(registry)
    result = gateway.process_governed("poi", SOURCE_INPUT, VALID_POLICY_PACK)

    receipt = validate_receipt_v1(result["receipt"])
    assert receipt["adapter_version"] == MANIFEST["adapter_version"]
    assert receipt["adapter_id"] == MANIFEST["adapter_id"]


def test_receipt_must_match_output_and_envelope_hashes() -> None:
    adapter = PoIAdapter()
    envelope = validate_envelope_v1(adapter.build_envelope(SOURCE_INPUT))
    output = validate_output_v1(adapter.build_output(envelope))
    receipt = validate_receipt_v1(
        build_receipt_v1(manifest=MANIFEST, envelope=envelope, output=output)
    )

    assert receipt["reason_id"] == output["reason_id"]
    assert receipt["policy_decision"] == "accepted"

    tampered_output = dict(output)
    tampered_output["reason_id"] = ReasonID.INTERNAL_ERROR.value

    tampered_receipt = validate_receipt_v1(
        build_receipt_v1(manifest=MANIFEST, envelope=envelope, output=tampered_output)
    )

    assert tampered_receipt["output_hash"] != receipt["output_hash"]
    assert tampered_receipt["reason_id"] != receipt["reason_id"]


def test_handoff_rebuild_rejects_tampered_receipt_decision() -> None:
    result = _gateway().process_governed("poi", SOURCE_INPUT, VALID_POLICY_PACK)

    tampered_receipt = dict(result["receipt"])
    tampered_receipt["policy_decision"] = "rejected"

    try:
        build_handoff_v1(_envelope(), result["output"], tampered_receipt)
    except ValueError as exc:
        assert str(exc) == ReasonID.INVALID_OUTPUT.value
    else:
        raise AssertionError("tampered receipt decision must fail closed")


def test_handoff_rebuild_rejects_tampered_output_hash() -> None:
    result = _gateway().process_governed("poi", SOURCE_INPUT, VALID_POLICY_PACK)

    tampered_output = dict(result["output"])
    tampered_output["output_payload"] = {"status": "tampered"}

    try:
        build_handoff_v1(_envelope(), tampered_output, result["receipt"])
    except ValueError as exc:
        assert str(exc) == ReasonID.INVALID_OUTPUT.value
    else:
        raise AssertionError("tampered output must fail closed")
