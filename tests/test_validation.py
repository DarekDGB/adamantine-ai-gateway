import pytest

from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.validation import (
    MAX_DEPTH,
    MAX_KEYS,
    MAX_LIST_ITEMS,
    MAX_STRING_LENGTH,
    validate_envelope_v1,
    validate_manifest_v1,
    validate_output_v1,
)


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


def test_validate_envelope_v1_rejects_non_dict_input_payload() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "deterministic-test-model",
        "input_payload": [],
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
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


def test_validate_envelope_rejects_unsupported_type_object() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": {"value": object()},
    }

    with pytest.raises(ValidationError):
        validate_envelope_v1(envelope)


def test_validate_envelope_rejects_nested_invalid_structure_in_list() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": {
            "data": [
                {"valid": "ok"},
                {"invalid": object()},
            ]
        },
    }

    with pytest.raises(ValidationError):
        validate_envelope_v1(envelope)


def test_validate_envelope_accepts_valid_list_payload() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": {
            "data": [
                {"key": "value"},
                {"nested": {"x": 1}},
                ["a", "b", "c"],
                True,
                None,
            ]
        },
    }

    validated = validate_envelope_v1(envelope)

    assert validated == envelope


def test_validate_envelope_rejects_payload_exceeding_max_depth() -> None:
    nested: dict[str, object] = {}
    current = nested
    for depth_index in range(MAX_DEPTH + 1):
        next_level: dict[str, object] = {}
        current[f"level_{depth_index}"] = next_level
        current = next_level

    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": nested,
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_envelope_v1(envelope)


def test_validate_envelope_rejects_overlong_string_in_payload() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": {"value": "x" * (MAX_STRING_LENGTH + 1)},
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_envelope_v1(envelope)


def test_validate_envelope_rejects_payload_list_exceeding_max_items() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": {"items": ["x"] * (MAX_LIST_ITEMS + 1)},
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_envelope_v1(envelope)


def test_validate_envelope_rejects_payload_dict_exceeding_max_keys() -> None:
    payload = {f"k{i}": i for i in range(MAX_KEYS + 1)}
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": payload,
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_envelope_v1(envelope)


def test_validate_envelope_rejects_payload_dict_key_exceeding_max_length() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "test",
        "input_payload": {("k" * (MAX_STRING_LENGTH + 1)): "value"},
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_envelope_v1(envelope)


def test_validate_envelope_rejects_overlong_required_string_field() -> None:
    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "m" * (MAX_STRING_LENGTH + 1),
        "input_payload": {},
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_envelope_v1(envelope)


def test_validate_output_rejects_oversized_list_in_payload() -> None:
    output = {
        "contract_version": AI_GATEWAY_OUTPUT_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "accepted": False,
        "reason_id": "POLICY_DENIED",
        "output_payload": {"items": ["x"] * (MAX_LIST_ITEMS + 1)},
        "context_hash": "abc123",
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_output_v1(output)


def test_validate_manifest_rejects_overlong_required_string_field() -> None:
    manifest = {
        "manifest_version": "adapter_manifest_v1",
        "adapter_id": "poi",
        "adapter_version": "0.5.0",
        "entrypoint": "e" * (MAX_STRING_LENGTH + 1),
        "accepted_input_types": ["policy_test_input"],
        "supported_actions": ["evaluate_candidate"],
        "required_payload_fields": ["task_type", "model_family"],
        "optional_payload_fields": ["input_payload"],
        "output_contract": "ai_gateway_output_v1",
        "determinism_constraints": ["canonical_json_only"],
        "failure_reason_ids": [
            "ACCEPTED",
            "SCHEMA_VIOLATION",
        ],
        "notes": "manifest",
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_manifest_v1(manifest)


def test_validate_manifest_rejects_string_list_exceeding_max_items() -> None:
    manifest = {
        "manifest_version": "adapter_manifest_v1",
        "adapter_id": "poi",
        "adapter_version": "0.5.0",
        "entrypoint": "tests.test_validation.poi",
        "accepted_input_types": ["x"] * (MAX_LIST_ITEMS + 1),
        "supported_actions": ["evaluate_candidate"],
        "required_payload_fields": ["task_type", "model_family"],
        "optional_payload_fields": ["input_payload"],
        "output_contract": "ai_gateway_output_v1",
        "determinism_constraints": ["canonical_json_only"],
        "failure_reason_ids": [
            "ACCEPTED",
            "SCHEMA_VIOLATION",
        ],
        "notes": "manifest",
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_manifest_v1(manifest)
