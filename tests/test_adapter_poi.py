from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1


def test_poi_adapter_name_is_locked() -> None:
    assert PoIAdapter().name == "poi"


def test_poi_adapter_build_envelope_returns_valid_envelope() -> None:
    adapter = PoIAdapter()

    envelope = adapter.build_envelope(
        {
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"candidate_id": "abc123"},
        }
    )

    assert envelope == {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"candidate_id": "abc123"},
    }


def test_poi_adapter_build_output_accepts_allowlisted_candidate() -> None:
    adapter = PoIAdapter()

    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"candidate_id": "abc123"},
    }

    output = adapter.build_output(envelope)

    assert output["contract_version"] == AI_GATEWAY_OUTPUT_V1
    assert output["adapter"] == "poi"
    assert output["task_type"] == "code_review"
    assert output["accepted"] is True
    assert output["reason_id"] == "ACCEPTED"
    assert output["output_payload"] == {"status": "accepted-candidate"}
    assert len(output["context_hash"]) == 64


def test_poi_adapter_build_output_rejects_unsupported_task() -> None:
    adapter = PoIAdapter()

    envelope = {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "poi",
        "task_type": "unknown_task",
        "model_family": "poi-v1",
        "input_payload": {"candidate_id": "abc123"},
    }

    output = adapter.build_output(envelope)

    assert output["accepted"] is False
    assert output["reason_id"] == "UNSUPPORTED_TASK"
    assert output["output_payload"] == {}
