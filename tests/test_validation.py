import pytest

from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.validation import validate_envelope_v1, validate_output_v1


def test_validate_envelope_v1_accepts_valid_envelope() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "deterministic-test-model",
        "input_payload": {"candidate_id": "abc123"},
    }

    validated = validate_envelope_v1(envelope)

    assert validated == envelope


def test_validate_envelope_v1_rejects_non_dict() -> None:
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_envelope_v1([])


def test_validate_envelope_v1_rejects_wrong_contract_version() -> None:
    envelope = {
        "contract_version": "wrong",
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "deterministic-test-model",
        "input_payload": {"candidate_id": "abc123"},
    }

    with pytest.raises(ContractError, match=ReasonID.INVALID_ENVELOPE.value):
        validate_envelope_v1(envelope)


def test_validate_envelope_v1_rejects_missing_required_field() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "deterministic-test-model",
    }

    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_envelope_v1(envelope)


def test_validate_output_v1_accepts_valid_output() -> None:
    output = {
        "contract_version": AI_GATEWAY_OUTPUT_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "accepted": False,
        "reason_id": "POLICY_DENIED",
        "output_payload": {},
        "context_hash": "abc123",
    }

    validated = validate_output_v1(output)

    assert validated == output


def test_validate_output_v1_rejects_non_dict() -> None:
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_output_v1("bad")


def test_validate_output_v1_rejects_wrong_contract_version() -> None:
    output = {
        "contract_version": "wrong",
        "adapter": "poi",
        "task_type": "code_review",
        "accepted": False,
        "reason_id": "POLICY_DENIED",
        "output_payload": {},
        "context_hash": "abc123",
    }

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_output_v1(output)


def test_validate_output_v1_rejects_missing_required_field() -> None:
    output = {
        "contract_version": AI_GATEWAY_OUTPUT_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "accepted": False,
        "reason_id": "POLICY_DENIED",
        "output_payload": {},
    }

    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_output_v1(output)


def test_validate_output_v1_rejects_non_bool_accepted() -> None:
    output = {
        "contract_version": AI_GATEWAY_OUTPUT_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "accepted": "false",
        "reason_id": "POLICY_DENIED",
        "output_payload": {},
        "context_hash": "abc123",
    }

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_output_v1(output)

def test_validate_envelope_v1_rejects_unknown_field() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": {},
        "extra_field": "not-allowed",
    }

    with pytest.raises(ValidationError):
        validate_envelope_v1(envelope)


def test_validate_output_v1_rejects_unknown_field() -> None:
    output = {
        "contract_version": AI_GATEWAY_OUTPUT_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "accepted": False,
        "reason_id": "POLICY_DENIED",
        "output_payload": {},
        "context_hash": "abc",
        "extra_field": "not-allowed",
    }

    with pytest.raises(ValidationError):
        validate_output_v1(output)

def test_validate_envelope_rejects_float_in_payload() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": {"value": 1.23},
    }

    with pytest.raises(ValidationError):
        validate_envelope_v1(envelope)


def test_validate_envelope_rejects_non_string_dict_key() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": {1: "invalid-key"},
    }

    with pytest.raises(ValidationError):
        validate_envelope_v1(envelope)


def test_validate_output_rejects_nested_invalid_type() -> None:
    output = {
        "contract_version": AI_GATEWAY_OUTPUT_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "accepted": False,
        "reason_id": "POLICY_DENIED",
        "output_payload": {"nested": {"value": 1.23}},
        "context_hash": "abc123",
    }

    with pytest.raises(ValidationError):
        validate_output_v1(output)
