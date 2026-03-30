from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.receipt import build_receipt_v1


def test_build_receipt_v1_returns_valid_accepted_receipt() -> None:
    adapter = PoIAdapter()
    source_input = {
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"prompt": "hello"},
    }
    manifest = {
        "manifest_version": "adapter_manifest_v1",
        "adapter_id": "poi",
        "adapter_version": "0.3.0",
        "entrypoint": "ai_gateway.adapters.poi.PoIAdapter",
        "accepted_input_types": ["poi_candidate"],
        "supported_actions": ["evaluate_candidate"],
        "required_payload_fields": ["task_type", "model_family", "input_payload"],
        "optional_payload_fields": [],
        "output_contract": "ai_gateway_output_v1",
        "determinism_constraints": ["canonical_json_only"],
        "failure_reason_ids": ["ACCEPTED", "POLICY_DENIED"],
        "notes": "PoI adapter boundary",
    }

    envelope = adapter.build_envelope(source_input)
    output = adapter.build_output(envelope)
    receipt = build_receipt_v1(manifest=manifest, envelope=envelope, output=output)

    assert receipt["adapter_id"] == "poi"
    assert receipt["policy_decision"] == "accepted"
    assert receipt["reason_id"] == "ACCEPTED"
