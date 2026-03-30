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


def validate_envelope_v1(envelope: Any) -> dict:
    data = _require_dict(envelope)

    contract_version = data.get("contract_version")
    if contract_version != AI_GATEWAY_ENVELOPE_V1:
        raise ContractError(ReasonID.INVALID_ENVELOPE.value)

    for field in REQUIRED_ENVELOPE_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    return data


def validate_output_v1(output: Any) -> dict:
    data = _require_dict(output)

    contract_version = data.get("contract_version")
    if contract_version != AI_GATEWAY_OUTPUT_V1:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)

    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in data or data[field] is None:
            raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    accepted = data["accepted"]
    if not isinstance(accepted, bool):
        raise ContractError(ReasonID.INVALID_OUTPUT.value)

    return data
