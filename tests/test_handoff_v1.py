import pytest

from ai_gateway.contracts.handoff_v1 import AI_GATEWAY_HANDOFF_V1
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.handoff import build_handoff_v1
from ai_gateway.reason_ids import ReasonID
from ai_gateway.validation import validate_handoff_v1
from ai_gateway.hashing import sha256_hex


def _envelope() -> dict:
    return {
        "contract_version": "ai_gateway_envelope_v1",
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"action": "evaluate_candidate"},
    }


def _output(accepted: bool = True) -> dict:
    return {
        "contract_version": "ai_gateway_output_v1",
        "adapter": "poi",
        "task_type": "code_review",
        "accepted": accepted,
        "reason_id": "ACCEPTED" if accepted else ReasonID.POLICY_DENIED.value,
        "output_payload": {},
        "context_hash": "",
    }


def _receipt(envelope: dict, output: dict) -> dict:
    return {
        "receipt_version": "ai_gateway_receipt_v1",
        "gateway_version": "v0",
        "adapter_id": "poi",
        "adapter_version": "v1",
        "reason_id": output["reason_id"],
        "policy_decision": "accepted" if output["accepted"] else "rejected",
        "envelope_hash": sha256_hex(envelope),
        "output_hash": sha256_hex(output),
        "created_from_contract": "ai_gateway_output_v1",
        "determinism_profile": "deterministic_v1",
    }


def test_build_handoff_accepts_valid_flow() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)

    assert handoff["handoff_version"] == AI_GATEWAY_HANDOFF_V1
    assert handoff["policy_decision"] == "accepted"


def test_build_handoff_rejected_flow_sets_decision() -> None:
    envelope = _envelope()
    output = _output(False)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)

    assert handoff["policy_decision"] == "rejected"


def test_build_handoff_rejects_envelope_hash_mismatch() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)
    receipt["envelope_hash"] = "0" * 64

    with pytest.raises(ValueError, match=ReasonID.INVALID_OUTPUT.value):
        build_handoff_v1(envelope, output, receipt)


def test_build_handoff_rejects_output_hash_mismatch() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)
    receipt["output_hash"] = "0" * 64

    with pytest.raises(ValueError, match=ReasonID.INVALID_OUTPUT.value):
        build_handoff_v1(envelope, output, receipt)


def test_build_handoff_rejects_policy_decision_mismatch() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)
    receipt["policy_decision"] = "rejected"

    with pytest.raises(ValueError, match=ReasonID.INVALID_OUTPUT.value):
        build_handoff_v1(envelope, output, receipt)


def test_validate_handoff_v1_accepts_valid_contract() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)

    validated = validate_handoff_v1(handoff)

    assert validated == handoff


def test_validate_handoff_v1_rejects_unknown_field() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)
    handoff["unexpected"] = True

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_handoff_v1(handoff)


def test_validate_handoff_v1_rejects_wrong_version() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)
    handoff["handoff_version"] = "wrong"

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_handoff_v1(handoff)


def test_validate_handoff_v1_rejects_missing_field() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)
    del handoff["adapter"]

    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_handoff_v1(handoff)


def test_validate_handoff_v1_rejects_invalid_policy_decision() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)
    handoff["policy_decision"] = "invalid"

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_handoff_v1(handoff)


def test_validate_handoff_v1_rejects_invalid_hash() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)
    handoff["envelope_hash"] = "invalid"

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_handoff_v1(handoff)


def test_validate_handoff_v1_allows_empty_context_hash() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)
    handoff["context_hash"] = ""

    validated = validate_handoff_v1(handoff)

    assert validated["context_hash"] == ""


def test_validate_handoff_v1_rejects_non_string_context_hash() -> None:
    envelope = _envelope()
    output = _output(True)
    receipt = _receipt(envelope, output)

    handoff = build_handoff_v1(envelope, output, receipt)
    handoff["context_hash"] = 123

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_handoff_v1(handoff)
