import pytest

from ai_gateway.gateway import AIGateway
from ai_gateway.policy import enforce_policy_for_adapter
from ai_gateway.registry import AdapterRegistry
from ai_gateway.contracts.policypack_v1 import POLICYPACK_V1
from ai_gateway.reason_ids import ReasonID
from ai_gateway.errors import PolicyError


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


def _policy_pack() -> dict:
    return {
        "policypack_version": POLICYPACK_V1,
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


def _gateway() -> AIGateway:
    registry = AdapterRegistry()
    registry.register("poi", _DummyAdapter())
    return AIGateway(registry)


def test_policy_enforcement_allows_valid_request() -> None:
    gateway = _gateway()

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is True
    assert result["reason_id"] == "ACCEPTED"


def test_policy_enforcement_rejects_invalid_task_type() -> None:
    gateway = _gateway()

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "documentation",
            "model_family": "poi-v1",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.UNSUPPORTED_TASK.value


def test_policy_enforcement_rejects_invalid_model_family() -> None:
    gateway = _gateway()

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "unknown-model",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.UNSUPPORTED_MODEL.value


def test_policy_enforcement_rejects_invalid_action() -> None:
    gateway = _gateway()

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"action": "not_allowed"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.POLICY_DENIED.value


def test_enforce_policy_direct_call_raises() -> None:
    with pytest.raises(PolicyError):
        enforce_policy_for_adapter(
            policy_pack=_policy_pack(),
            adapter_name="poi",
            task_type="documentation",
            model_family="poi-v1",
            action="evaluate_candidate",
        )
