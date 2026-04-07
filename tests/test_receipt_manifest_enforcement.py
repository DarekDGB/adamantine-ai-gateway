from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


SOURCE_INPUT = {
    "task_type": "code_review",
    "model_family": "poi-v1",
    "input_payload": {"action": "evaluate_candidate"},
}


BASE_MANIFEST = {
    "manifest_version": "adapter_manifest_v1",
    "adapter_id": "poi",
    "adapter_version": "0.5.0",
    "entrypoint": "tests.test_receipt_manifest_enforcement._AlignedAdapter",
    "accepted_input_types": ["poi_candidate"],
    "supported_actions": ["evaluate_candidate"],
    "required_payload_fields": ["task_type", "model_family", "input_payload"],
    "optional_payload_fields": [],
    "output_contract": "ai_gateway_output_v1",
    "determinism_constraints": ["canonical_json_only"],
    "failure_reason_ids": [
        "ACCEPTED",
        "INVALID_ENVELOPE",
        "INVALID_OUTPUT",
        "SCHEMA_VIOLATION",
        "MISSING_REQUIRED_FIELD",
        "POLICY_DENIED",
        "UNSUPPORTED_TASK",
        "UNSUPPORTED_MODEL",
        "ADAPTER_NOT_REGISTERED",
        "ADAPTER_VALIDATION_FAILED",
        "INTERNAL_ERROR",
    ],
    "notes": "Receipt manifest enforcement tests",
}


class _AlignedAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "poi",
            "task_type": source_input["task_type"],
            "model_family": source_input["model_family"],
            "input_payload": source_input["input_payload"],
        }

    def build_output(self, envelope: dict) -> dict:
        return {
            "contract_version": "ai_gateway_output_v1",
            "adapter": "poi",
            "task_type": envelope["task_type"],
            "accepted": True,
            "reason_id": "ACCEPTED",
            "output_payload": {},
            "context_hash": "",
        }


class _EnvelopeAdapterDriftAdapter(_AlignedAdapter):
    def build_envelope(self, source_input: dict) -> dict:
        envelope = super().build_envelope(source_input)
        envelope["adapter"] = "wallet"
        return envelope


class _OutputContractDriftAdapter(_AlignedAdapter):
    def build_output(self, envelope: dict) -> dict:
        output = super().build_output(envelope)
        output["contract_version"] = "wrong_output_contract"
        return output


class _OutputAdapterDriftAdapter(_AlignedAdapter):
    def build_output(self, envelope: dict) -> dict:
        output = super().build_output(envelope)
        output["adapter"] = "wallet"
        return output


class _OutputTaskTypeDriftAdapter(_AlignedAdapter):
    def build_output(self, envelope: dict) -> dict:
        output = super().build_output(envelope)
        output["task_type"] = "other_task"
        return output


def _gateway(adapter: object, manifest: dict) -> AIGateway:
    registry = AdapterRegistry()
    registry.register("poi", adapter, manifest=manifest)
    return AIGateway(registry)


def test_process_with_receipt_accepts_manifest_aligned_runtime_path() -> None:
    result = _gateway(_AlignedAdapter(), BASE_MANIFEST).process_with_receipt(
        "poi",
        SOURCE_INPUT,
    )

    assert result["output"]["accepted"] is True
    assert result["output"]["reason_id"] == "ACCEPTED"
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == "ACCEPTED"
    assert result["receipt"]["policy_decision"] == "accepted"


def test_process_with_receipt_rejects_runtime_envelope_adapter_drift() -> None:
    result = _gateway(_EnvelopeAdapterDriftAdapter(), BASE_MANIFEST).process_with_receipt(
        "poi",
        SOURCE_INPUT,
    )

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.INVALID_ENVELOPE.value
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == ReasonID.INVALID_ENVELOPE.value
    assert result["receipt"]["policy_decision"] == "rejected"


def test_process_with_receipt_rejects_manifest_declared_action_drift() -> None:
    manifest = dict(BASE_MANIFEST)
    manifest["supported_actions"] = ["different_action"]

    result = _gateway(_AlignedAdapter(), manifest).process_with_receipt(
        "poi",
        SOURCE_INPUT,
    )

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value


def test_process_with_receipt_rejects_output_contract_drift() -> None:
    result = _gateway(_OutputContractDriftAdapter(), BASE_MANIFEST).process_with_receipt(
        "poi",
        SOURCE_INPUT,
    )

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.INVALID_OUTPUT.value
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == ReasonID.INVALID_OUTPUT.value


def test_process_with_receipt_rejects_output_adapter_drift() -> None:
    result = _gateway(_OutputAdapterDriftAdapter(), BASE_MANIFEST).process_with_receipt(
        "poi",
        SOURCE_INPUT,
    )

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.INVALID_OUTPUT.value
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == ReasonID.INVALID_OUTPUT.value


def test_process_with_receipt_rejects_output_task_type_drift() -> None:
    result = _gateway(_OutputTaskTypeDriftAdapter(), BASE_MANIFEST).process_with_receipt(
        "poi",
        SOURCE_INPUT,
    )

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.INVALID_OUTPUT.value
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == ReasonID.INVALID_OUTPUT.value
