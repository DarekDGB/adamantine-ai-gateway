from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.gateway import AIGateway
from ai_gateway.registry import AdapterRegistry


def test_gateway_output_is_deterministic() -> None:
    registry = AdapterRegistry()
    registry.register("poi", PoIAdapter())
    gateway = AIGateway(registry)

    source_input = {
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"candidate_id": "abc123"},
    }

    first = gateway.process("poi", source_input)
    second = gateway.process("poi", source_input)

    assert first == second
