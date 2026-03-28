import pytest

from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
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
    with pytest.raises(ValueError, match="value must be a dict"):
        validate_envelope_v1([])


def test_validate_envelope_v1_rejects_wrong_contract_version() -> None:
    envelope = {
        "contract_version": "wrong",
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "deterministic-test-model",
        "input_payload": {"candidate_id": "abc123"},
    }

    with pytest.raises(ValueError, match="invalid envelope contract_version"):
        validate_envelope_v1(envelope)


def test_validate_envelope_v1_rejects_missing_required_field() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "deterministic-test-model",
    }

    with pytest.raises(ValueError, match="missing required envelope field: input_payload"):
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
    with pytest.raises(ValueError, match="value must be a dict"):
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

    with pytest.raises(ValueError, match="invalid output contract_version"):
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

    with pytest.raises(ValueError, match="missing required output field: context_hash"):
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

    with pytest.raises(ValueError, match="accepted must be a bool"):
        validate_output_v1(output)
