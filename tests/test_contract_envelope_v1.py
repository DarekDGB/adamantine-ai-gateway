from ai_gateway.contracts.envelope_v1 import (
    AI_GATEWAY_ENVELOPE_V1,
    REQUIRED_ENVELOPE_FIELDS,
)


def test_envelope_v1_contract_identity() -> None:
    assert AI_GATEWAY_ENVELOPE_V1 == "ai_gateway_envelope_v1"


def test_envelope_v1_required_fields() -> None:
    assert REQUIRED_ENVELOPE_FIELDS == (
        "contract_version",
        "adapter",
        "task_type",
        "model_family",
        "input_payload",
    )
