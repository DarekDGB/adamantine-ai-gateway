from ai_gateway.adapters.poi import PoIAdapter


def test_poi_adapter_output_is_deterministic() -> None:
    adapter = PoIAdapter()

    envelope = {
        "contract_version": "ai_gateway_envelope_v1",
        "adapter": "poi",
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"candidate_id": "abc123"},
    }

    first = adapter.build_output(envelope)
    second = adapter.build_output(envelope)

    assert first == second
