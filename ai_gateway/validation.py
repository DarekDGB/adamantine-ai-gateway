from typing import Any

from ai_gateway.contracts.envelope_v1 import (
    AI_GATEWAY_ENVELOPE_V1,
    REQUIRED_ENVELOPE_FIELDS,
)
from ai_gateway.contracts.output_v1 import (
    AI_GATEWAY_OUTPUT_V1,
    REQUIRED_OUTPUT_FIELDS,
)
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.reason_ids import ReasonID


def _require_dict(value: Any) -> dict:
    if not isinstance(value, dict):
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)
    return value


def _reject_unknown_fields(data: dict, allowed_fields: set[str]) -> None:
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
