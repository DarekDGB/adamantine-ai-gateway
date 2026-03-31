from typing import Any

from ai_gateway.contracts.envelope_v1 import (
    AI_GATEWAY_ENVELOPE_V1,
    REQUIRED_ENVELOPE_FIELDS,
)
from ai_gateway.contracts.manifest_v1 import (
    ADAPTER_MANIFEST_V1,
    ALLOWED_MANIFEST_FIELDS,
    REQUIRED_MANIFEST_FIELDS,
)
from ai_gateway.contracts.output_v1 import (
    AI_GATEWAY_OUTPUT_V1,
    REQUIRED_OUTPUT_FIELDS,
)
from ai_gateway.contracts.policypack_v1 import (
    ALLOWED_ADAPTER_POLICY_FIELDS,
    ALLOWED_POLICYPACK_DEFAULT_DECISIONS,
    ALLOWED_POLICYPACK_FIELDS,
    POLICYPACK_V1,
    REQUIRED_ADAPTER_POLICY_FIELDS,
    REQUIRED_POLICYPACK_FIELDS,
)
from ai_gateway.contracts.receipt_v1 import (
    AI_GATEWAY_RECEIPT_V1,
    ALLOWED_POLICY_DECISIONS,
    ALLOWED_RECEIPT_FIELDS,
    REQUIRED_RECEIPT_FIELDS,
)
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.reason_ids import ReasonID


def _require_dict(value: Any) -> dict:
    if not isinstance(value, dict):
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)
    return value


def _reject_unknown_fields(data: dict, allowed_fields: set[str] | frozenset[str]) -> None:
    for key in data:
        if key not in allowed_fields:
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)


def _validate_canonical_value(value: Any) -> None:
    if isinstance(value, (str, int, bool)) or value is None:
        return

    if isinstance(value, float):
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

    if isinstance(value, list):
        for item in value:
            _validate_canonical_value(item)
        return

    if isinstance(value, dict):
        for key, val in value.items():
            if not isinstance(key, str):
                raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)
            _validate_canonical_value(val)
        return

    raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)


def _validate_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

    _validate_canonical_value(payload)


def _validate_non_empty_str(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)
    return value


def _validate_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

    validated: list[str] = []
    for item in value:
        validated.append(_validate_non_empty_str(item))

    if len(validated) != len(set(validated)):
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

    return validated


def _validate_hash_hex(value: Any) -> str:
    validated = _validate_non_empty_str(value)
    if len(validated) != 64 or any(ch not in "0123456789abcdef" for ch in validated):
        raise ContractError(ReasonID.INVALID_OUTPUT.value)
    return validated


def _validate_adapter_policy(value: Any) -> dict:
    data = _require_dict(value)
    _reject_unknown_fields(data, ALLOWED_ADAPTER_POLICY_FIELDS)

    for field in REQUIRED_ADAPTER_POLICY_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    return {
        "allowed_task_types": _validate_string_list(data["allowed_task_types"]),
        "allowed_model_families": _validate_string_list(data["allowed_model_families"]),
        "allowed_actions": _validate_string_list(data["allowed_actions"]),
    }


def validate_envelope_v1(envelope: Any) -> dict:
    data = _require_dict(envelope)

    if data.get("contract_version") != AI_GATEWAY_ENVELOPE_V1:
        raise ContractError(ReasonID.INVALID_ENVELOPE.value)

    allowed_fields = set(REQUIRED_ENVELOPE_FIELDS)
    allowed_fields.add("contract_version")

    _reject_unknown_fields(data, allowed_fields)

    for field in REQUIRED_ENVELOPE_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    _validate_payload(data["input_payload"])

    return data


def validate_output_v1(output: Any) -> dict:
    data = _require_dict(output)

    if data.get("contract_version") != AI_GATEWAY_OUTPUT_V1:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)

    allowed_fields = set(REQUIRED_OUTPUT_FIELDS)
    allowed_fields.add("contract_version")

    _reject_unknown_fields(data, allowed_fields)

    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    if not isinstance(data["accepted"], bool):
        raise ContractError(ReasonID.INVALID_OUTPUT.value)

    _validate_payload(data["output_payload"])

    return data


def validate_manifest_v1(manifest: Any) -> dict:
    data = _require_dict(manifest)

    if data.get("manifest_version") != ADAPTER_MANIFEST_V1:
        raise ContractError(ReasonID.SCHEMA_VIOLATION.value)

    _reject_unknown_fields(data, ALLOWED_MANIFEST_FIELDS)

    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    for field in (
        "manifest_version",
        "adapter_id",
        "adapter_version",
        "entrypoint",
        "output_contract",
        "notes",
    ):
        _validate_non_empty_str(data[field])

    for field in (
        "accepted_input_types",
        "supported_actions",
        "required_payload_fields",
        "optional_payload_fields",
        "determinism_constraints",
        "failure_reason_ids",
    ):
        _validate_string_list(data[field])

    if data["output_contract"] != AI_GATEWAY_OUTPUT_V1:
        raise ContractError(ReasonID.SCHEMA_VIOLATION.value)

    for reason_id in data["failure_reason_ids"]:
        if reason_id == "ACCEPTED":
            continue
        try:
            ReasonID(reason_id)
        except ValueError as exc:
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value) from exc

    return data


def validate_policypack_v1(policy_pack: Any) -> dict:
    data = _require_dict(policy_pack)

    if data.get("policypack_version") != POLICYPACK_V1:
        raise ContractError(ReasonID.SCHEMA_VIOLATION.value)

    _reject_unknown_fields(data, ALLOWED_POLICYPACK_FIELDS)

    for field in REQUIRED_POLICYPACK_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    for field in (
        "policypack_version",
        "policypack_id",
        "policypack_version_id",
        "default_decision",
        "notes",
    ):
        _validate_non_empty_str(data[field])

    if data["default_decision"] not in ALLOWED_POLICYPACK_DEFAULT_DECISIONS:
        raise ContractError(ReasonID.POLICY_DENIED.value)

    adapter_policies = _require_dict(data["adapter_policies"])
    if not adapter_policies:
        raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    validated_adapter_policies: dict[str, dict] = {}
    for adapter_id, adapter_policy in adapter_policies.items():
        validated_adapter_id = _validate_non_empty_str(adapter_id)
        validated_adapter_policies[validated_adapter_id] = _validate_adapter_policy(
            adapter_policy
        )

    return {
        "policypack_version": data["policypack_version"],
        "policypack_id": data["policypack_id"],
        "policypack_version_id": data["policypack_version_id"],
        "default_decision": data["default_decision"],
        "adapter_policies": validated_adapter_policies,
        "notes": data["notes"],
    }


def validate_receipt_v1(receipt: Any) -> dict:
    data = _require_dict(receipt)

    if data.get("receipt_version") != AI_GATEWAY_RECEIPT_V1:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)

    _reject_unknown_fields(data, ALLOWED_RECEIPT_FIELDS)

    for field in REQUIRED_RECEIPT_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    for field in (
        "receipt_version",
        "gateway_version",
        "adapter_id",
        "adapter_version",
        "reason_id",
        "created_from_contract",
        "determinism_profile",
    ):
        _validate_non_empty_str(data[field])

    if data["policy_decision"] not in ALLOWED_POLICY_DECISIONS:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)

    _validate_hash_hex(data["envelope_hash"])
    _validate_hash_hex(data["output_hash"])

    if data["created_from_contract"] != AI_GATEWAY_OUTPUT_V1:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)

    return data
