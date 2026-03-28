from ai_gateway.contracts.output_v1 import (
    AI_GATEWAY_OUTPUT_V1,
    REQUIRED_OUTPUT_FIELDS,
)


def test_output_v1_contract_identity() -> None:
    assert AI_GATEWAY_OUTPUT_V1 == "ai_gateway_output_v1"


def test_output_v1_required_fields() -> None:
    assert REQUIRED_OUTPUT_FIELDS == (
        "contract_version",
        "adapter",
        "task_type",
        "accepted",
        "reason_id",
        "output_payload",
        "context_hash",
    )
