import ai_gateway.gateway as gateway_module
from ai_gateway.errors import AdapterError
from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


def _manifest(adapter_id: str) -> dict:
    return {
        "manifest_version": "adapter_manifest_v1",
        "adapter_id": adapter_id,
        "adapter_version": "0.5.0",
        "entrypoint": f"tests.test_gateway_governed.{adapter_id}",
        "accepted_input_types": ["governed_test_input"],
        "supported_actions": ["evaluate_candidate"],
        "required_payload_fields": ["task_type", "model_family"],
        "optional_payload_fields": ["input_payload"],
        "output_contract": "ai_gateway_output_v1",
        "determinism_constraints": ["canonical_json_only"],
        "failure_reason_ids": [
            "ACCEPTED",
            "SCHEMA_VIOLATION",
            "INVALID_ENVELOPE",
            "POLICY_DENIED",
            "ADAPTER_VALIDATION_FAILED",
            "INTERNAL_ERROR",
        ],
        "notes": "Governed path test manifest",
    }


def _policy_pack() -> dict:
    return {
        "policypack_version": "policy_pack_v1",
        "policypack_id": "test",
        "policypack_version_id": "v0.5.0",
        "default_decision": "deny",
        "adapter_policies": {
            "poi": {
                "allowed_task_types": ["code_review"],
                "allowed_model_families": ["poi-v1"],
                "allowed_actions": ["evaluate_candidate"],
            }
        },
        "notes": "test",
    }


class _DummyAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "poi",
            "task_type": source_input["task_type"],
            "model_family": source_input["model_family"],
            "input_payload": source_input.get("input_payload", {}),
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


class _RejectedAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "poi",
            "task_type": source_input["task_type"],
            "model_family": source_input["model_family"],
            "input_payload": source_input.get("input_payload", {}),
        }

    def build_output(self, envelope: dict) -> dict:
        return {
            "contract_version": "ai_gateway_output_v1",
            "adapter": "poi",
            "task_type": envelope["task_type"],
            "accepted": False,
            "reason_id": ReasonID.POLICY_DENIED.value,
            "output_payload": {},
            "context_hash": "",
        }


def _source_input(action: str = "evaluate_candidate") -> dict:
    return {
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"action": action},
    }


def test_process_governed_success_returns_output_receipt_handoff() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _DummyAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    result = gateway.process_governed("poi", _source_input(), _policy_pack())

    assert result["output"]["accepted"] is True
    assert result["output"]["reason_id"] == "ACCEPTED"
    assert result["receipt"] is not None
    assert result["handoff"] is not None
    assert result["receipt"]["policy_decision"] == "accepted"
    assert result["handoff"]["policy_decision"] == "accepted"


def test_process_governed_manifest_missing_fails_closed() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _DummyAdapter())
    gateway = AIGateway(registry)

    result = gateway.process_governed("poi", _source_input(), _policy_pack())

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value
    assert result["receipt"] is None
    assert result["handoff"] is None


def test_process_governed_rejected_output_still_builds_receipt_and_handoff() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _RejectedAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    result = gateway.process_governed("poi", _source_input(), _policy_pack())

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.POLICY_DENIED.value
    assert result["receipt"] is not None
    assert result["handoff"] is not None
    assert result["receipt"]["policy_decision"] == "rejected"
    assert result["handoff"]["policy_decision"] == "rejected"


def test_process_governed_falls_back_to_internal_error_with_artifacts_when_primary_build_fails(
    monkeypatch,
) -> None:
    registry = AdapterRegistry()
    registry.register("poi", _DummyAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    original_build_receipt = gateway_module.build_receipt_v1
    call_count = {"count": 0}

    def flaky_build_receipt(manifest: dict, envelope: dict, output: dict) -> dict:
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise RuntimeError("first receipt build fails")
        return original_build_receipt(
            manifest=manifest,
            envelope=envelope,
            output=output,
        )

    monkeypatch.setattr(gateway_module, "build_receipt_v1", flaky_build_receipt)

    result = gateway.process_governed("poi", _source_input(), _policy_pack())

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.INTERNAL_ERROR.value
    assert result["receipt"] is not None
    assert result["handoff"] is not None
    assert result["receipt"]["policy_decision"] == "rejected"
    assert result["handoff"]["policy_decision"] == "rejected"


def test_process_governed_returns_none_artifacts_when_primary_and_fallback_build_fail(
    monkeypatch,
) -> None:
    registry = AdapterRegistry()
    registry.register("poi", _DummyAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    def always_fail_build_receipt(manifest: dict, envelope: dict, output: dict) -> dict:
        raise RuntimeError("receipt build fails always")

    monkeypatch.setattr(gateway_module, "build_receipt_v1", always_fail_build_receipt)

    result = gateway.process_governed("poi", _source_input(), _policy_pack())

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.INTERNAL_ERROR.value
    assert result["receipt"] is None
    assert result["handoff"] is None
