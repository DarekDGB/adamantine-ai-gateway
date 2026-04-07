import pytest

from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.adapters.wallet import WalletAdapter
from ai_gateway.errors import PolicyError
from ai_gateway.gateway import AIGateway
from ai_gateway.policy import (
    enforce_policy_for_adapter,
    get_adapter_policy,
    policy_reason_for_adapter,
)
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


def _gateway() -> AIGateway:
    registry = AdapterRegistry()
    registry.register("poi", PoIAdapter())
    registry.register("wallet", WalletAdapter())
    return AIGateway(registry)


def _policy_pack() -> dict:
    return {
        "policypack_version": "policy_pack_v1",
        "policypack_id": "adapter-policy-pack",
        "policypack_version_id": "v1.0.0",
        "default_decision": "deny",
        "adapter_policies": {
            "poi": {
                "allowed_task_types": ["code_review", "documentation"],
                "allowed_model_families": ["poi-v1"],
                "allowed_actions": ["evaluate_candidate"],
            },
            "wallet": {
                "allowed_task_types": ["wallet_operation"],
                "allowed_model_families": ["wallet-v1"],
                "allowed_actions": ["build_transaction", "sign_transaction_request"],
            },
        },
        "notes": "Adapter-scoped policy pack for tests",
    }


def test_get_adapter_policy_returns_scoped_policy() -> None:
    policy = get_adapter_policy(_policy_pack(), "poi")

    assert policy["allowed_task_types"] == ["code_review", "documentation"]
    assert policy["allowed_model_families"] == ["poi-v1"]
    assert policy["allowed_actions"] == ["evaluate_candidate"]


def test_get_adapter_policy_rejects_missing_adapter_policy() -> None:
    with pytest.raises(PolicyError) as excinfo:
        get_adapter_policy(_policy_pack(), "missing")

    assert str(excinfo.value) == ReasonID.POLICY_DENIED.value


def test_policy_reason_for_adapter_accepts_matching_scope() -> None:
    reason = policy_reason_for_adapter(
        policy_pack=_policy_pack(),
        adapter_name="poi",
        task_type="code_review",
        model_family="poi-v1",
        action="evaluate_candidate",
    )

    assert reason is None


def test_policy_reason_for_adapter_rejects_wrong_task() -> None:
    reason = policy_reason_for_adapter(
        policy_pack=_policy_pack(),
        adapter_name="poi",
        task_type="test_generation",
        model_family="poi-v1",
        action="evaluate_candidate",
    )

    assert reason == ReasonID.UNSUPPORTED_TASK


def test_policy_reason_for_adapter_rejects_wrong_model() -> None:
    reason = policy_reason_for_adapter(
        policy_pack=_policy_pack(),
        adapter_name="poi",
        task_type="code_review",
        model_family="unknown-model",
        action="evaluate_candidate",
    )

    assert reason == ReasonID.UNSUPPORTED_MODEL


def test_policy_reason_for_adapter_rejects_wrong_action() -> None:
    reason = policy_reason_for_adapter(
        policy_pack=_policy_pack(),
        adapter_name="poi",
        task_type="code_review",
        model_family="poi-v1",
        action="not_allowed",
    )

    assert reason == ReasonID.POLICY_DENIED


def test_enforce_policy_for_adapter_accepts_matching_scope() -> None:
    enforce_policy_for_adapter(
        policy_pack=_policy_pack(),
        adapter_name="poi",
        task_type="code_review",
        model_family="poi-v1",
        action="evaluate_candidate",
    )


def test_enforce_policy_for_adapter_rejects_wrong_task() -> None:
    with pytest.raises(PolicyError) as excinfo:
        enforce_policy_for_adapter(
            policy_pack=_policy_pack(),
            adapter_name="poi",
            task_type="test_generation",
            model_family="poi-v1",
            action="evaluate_candidate",
        )

    assert str(excinfo.value) == ReasonID.UNSUPPORTED_TASK.value


def test_enforce_policy_for_adapter_rejects_wrong_model() -> None:
    with pytest.raises(PolicyError) as excinfo:
        enforce_policy_for_adapter(
            policy_pack=_policy_pack(),
            adapter_name="poi",
            task_type="code_review",
            model_family="unknown-model",
            action="evaluate_candidate",
        )

    assert str(excinfo.value) == ReasonID.UNSUPPORTED_MODEL.value


def test_enforce_policy_for_adapter_rejects_wrong_action() -> None:
    with pytest.raises(PolicyError) as excinfo:
        enforce_policy_for_adapter(
            policy_pack=_policy_pack(),
            adapter_name="poi",
            task_type="code_review",
            model_family="poi-v1",
            action="not_allowed",
        )

    assert str(excinfo.value) == ReasonID.POLICY_DENIED.value


def test_policy_enforcement_accepts_adapter_scoped_poi_request() -> None:
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


def test_policy_enforcement_accepts_adapter_scoped_wallet_request() -> None:
    gateway = _gateway()

    result = gateway.process_with_policy(
        adapter_name="wallet",
        source_input={
            "wallet_id": "wallet-123",
            "network": "dgb",
            "asset": "dgb",
            "action": "build_transaction",
            "request_payload": {"to": "D123", "amount": "10"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is True
    assert result["reason_id"] == "ACCEPTED"


def test_policy_enforcement_rejects_invalid_task_for_adapter() -> None:
    gateway = _gateway()

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "test_generation",
            "model_family": "poi-v1",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.UNSUPPORTED_TASK.value


def test_policy_enforcement_rejects_invalid_model_for_adapter() -> None:
    gateway = _gateway()

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "not-allowed",
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
    assert result["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value


def test_enforce_policy_direct_call_accepts_allowed_documentation_scope() -> None:
    enforce_policy_for_adapter(
        policy_pack=_policy_pack(),
        adapter_name="poi",
        task_type="documentation",
        model_family="poi-v1",
        action="evaluate_candidate",
    )
