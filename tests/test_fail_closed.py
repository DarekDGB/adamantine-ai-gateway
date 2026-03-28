from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


class ExplodingAdapter:
    @property
    def name(self) -> str:
        return "explode"

    def build_envelope(self, source_input: dict) -> dict:
        raise RuntimeError("boom")

    def build_output(self, envelope: dict) -> dict:
        raise RuntimeError("boom")


def test_gateway_process_accepts_valid_poi_candidate() -> None:
    registry = AdapterRegistry()
    registry.register("poi", PoIAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "poi",
        {
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"candidate_id": "abc123"},
        },
    )

    assert output["contract_version"] == "ai_gateway_output_v1"
    assert output["adapter"] == "poi"
    assert output["task_type"] == "code_review"
    assert output["accepted"] is True
    assert output["reason_id"] == "ACCEPTED"
    assert output["output_payload"] == {"status": "accepted-candidate"}
    assert len(output["context_hash"]) == 64


def test_gateway_process_rejects_unregistered_adapter() -> None:
    registry = AdapterRegistry()
    gateway = AIGateway(registry)

    output = gateway.process(
        "poi",
        {
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"candidate_id": "abc123"},
        },
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.ADAPTER_NOT_REGISTERED.value
    assert output["output_payload"] == {}
    assert output["context_hash"] == ""


def test_gateway_process_rejects_missing_required_field_fail_closed() -> None:
    registry = AdapterRegistry()
    registry.register("poi", PoIAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "poi",
        {
            "task_type": "code_review",
            "model_family": "poi-v1",
        },
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.MISSING_REQUIRED_FIELD.value
    assert output["output_payload"] == {}
    assert output["context_hash"] == ""


def test_gateway_process_maps_unexpected_exception_to_internal_error() -> None:
    registry = AdapterRegistry()
    registry.register("explode", ExplodingAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "explode",
        {
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"candidate_id": "abc123"},
        },
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.INTERNAL_ERROR.value
    assert output["output_payload"] == {}
    assert output["context_hash"] == ""
