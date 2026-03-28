from typing import Any

from ai_gateway.contracts.envelope_v1 import (
    AI_GATEWAY_ENVELOPE_V1,
    REQUIRED_ENVELOPE_FIELDS,
)
from ai_gateway.contracts.output_v1 import (
    AI_GATEWAY_OUTPUT_V1,
    REQUIRED_OUTPUT_FIELDS,
)


def _require_dict(value: Any) -> dict:
    if not isinstance(value, dict):
        raise ValueError("value must be a dict")
    return value


def validate_envelope_v1(envelope: Any) -> dict:
    data = _require_dict(envelope)

    contract_version = data.get("contract_version")
    if contract_version != AI_GATEWAY_ENVELOPE_V1:
        raise ValueError("invalid envelope contract_version")

    for field in REQUIRED_ENVELOPE_FIELDS:
        if field not in data:
            raise ValueError(f"missing required envelope field: {field}")

    return data


def validate_output_v1(output: Any) -> dict:
    data = _require_dict(output)

    contract_version = data.get("contract_version")
    if contract_version != AI_GATEWAY_OUTPUT_V1:
        raise ValueError("invalid output contract_version")

    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in data:
            raise ValueError(f"missing required output field: {field}")

    accepted = data["accepted"]
    if not isinstance(accepted, bool):
        raise ValueError("accepted must be a bool")

    return data
