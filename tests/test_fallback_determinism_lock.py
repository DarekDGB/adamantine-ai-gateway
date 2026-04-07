from unittest.mock import patch

from ai_gateway.gateway import AIGateway
from ai_gateway.registry import AdapterRegistry


VALID_POLICY_PACK = {
    "policypack_version": "policy_pack_v1",
    "policypack_id": "fallback-determinism-lock",
    "policypack_version_id": "v1.0.0-lock",
    "default_decision": "deny",
    "adapter_policies": {},
    "notes": "Fallback determinism lock tests",
}


class _ExplodingManifestAdapter:
    @property
    def manifest(self) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": "explode",
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_fallback_determinism_lock._ExplodingManifestAdapter",
            "accepted_input_types": ["explode_input"],
            "supported_actions": ["evaluate_candidate"],
            "required_payload_fields": ["candidate_id"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["ACCEPTED", "INTERNAL_ERROR"],
            "notes": "Exploding adapter for fallback determinism tests",
        }

    def build_envelope(self, source_input: dict) -> dict:
        raise RuntimeError("boom")

    def build_output(self, envelope: dict) -> dict:
        raise RuntimeError("boom")


class _WalletExplodingManifestAdapter:
    @property
    def manifest(self) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": "wallet",
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_fallback_determinism_lock._WalletExplodingManifestAdapter",
            "accepted_input_types": ["wallet_request"],
            "supported_actions": ["build_transaction"],
            "required_payload_fields": ["wallet_id"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["ACCEPTED", "INTERNAL_ERROR"],
            "notes": "Wallet exploding adapter for fallback determinism tests",
        }

    def build_envelope(self, source_input: dict) -> dict:
        raise RuntimeError("boom")

    def build_output(self, envelope: dict) -> dict:
        raise RuntimeError("boom")


class _AlignedAdapter:
    @property
    def manifest(self) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": "poi",
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_fallback_determinism_lock._AlignedAdapter",
            "accepted_input_types": ["poi_candidate"],
            "supported_actions": ["evaluate_candidate"],
            "required_payload_fields": ["task_type", "model_family", "input_payload"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["ACCEPTED", "INTERNAL_ERROR"],
            "notes": "Aligned adapter for fallback determinism tests",
        }

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
            "output_payload": {"status": "accepted-candidate"},
            "context_hash": "abc123",
        }


def _gateway(name: str, adapter: object) -> AIGateway:
    registry = AdapterRegistry()
    registry.register(name, adapter)
    return AIGateway(registry)


def test_receipt_fallback_is_deterministic_for_same_failing_input() -> None:
    gateway = _gateway("explode", _ExplodingManifestAdapter())
    source_input = {
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"candidate_id": "abc123"},
    }

    first = gateway.process_with_receipt("explode", source_input)
    second = gateway.process_with_receipt("explode", source_input)

    assert first == second
    assert first["output"]["reason_id"] == "INTERNAL_ERROR"
    assert first["receipt"]["reason_id"] == "INTERNAL_ERROR"
    assert first["receipt"]["policy_decision"] == "rejected"


def test_governed_fallback_is_deterministic_for_same_failing_input() -> None:
    gateway = _gateway("explode", _ExplodingManifestAdapter())
    source_input = {
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"candidate_id": "abc123"},
    }

    first = gateway.process_governed("explode", source_input, VALID_POLICY_PACK)
    second = gateway.process_governed("explode", source_input, VALID_POLICY_PACK)

    assert first == second
    assert first["output"]["reason_id"] == "INTERNAL_ERROR"
    assert first["receipt"]["reason_id"] == "INTERNAL_ERROR"
    assert first["handoff"]["reason_id"] == "INTERNAL_ERROR"
    assert first["handoff"]["envelope_hash"] == first["receipt"]["envelope_hash"]
    assert first["handoff"]["output_hash"] == first["receipt"]["output_hash"]


def test_wallet_receipt_fallback_uses_stable_wallet_defaults() -> None:
    gateway = _gateway("wallet", _WalletExplodingManifestAdapter())
    source_input = {
        "wallet_id": "wallet-1",
        "action": "build_transaction",
        "request_payload": {},
    }

    first = gateway.process_with_receipt("wallet", source_input)
    second = gateway.process_with_receipt("wallet", source_input)

    assert first == second
    assert first["output"]["task_type"] == "wallet_operation"
    assert first["receipt"]["reason_id"] == "INTERNAL_ERROR"
    assert len(first["receipt"]["envelope_hash"]) == 64


def test_receipt_builder_fallback_is_deterministic_when_builder_raises() -> None:
    gateway = _gateway("poi", _AlignedAdapter())
    source_input = {
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"action": "evaluate_candidate"},
    }
    original_builder = AIGateway.process_with_receipt.__globals__["build_receipt_v1"]

    def _boom_then_original(*args, **kwargs):
        if not hasattr(_boom_then_original, "called"):
            _boom_then_original.called = True
            raise RuntimeError("boom")
        return original_builder(*args, **kwargs)

    with patch("ai_gateway.gateway.build_receipt_v1", side_effect=_boom_then_original):
        first = gateway.process_with_receipt("poi", source_input)

    def _boom_then_original_again(*args, **kwargs):
        if not hasattr(_boom_then_original_again, "called"):
            _boom_then_original_again.called = True
            raise RuntimeError("boom")
        return original_builder(*args, **kwargs)

    with patch("ai_gateway.gateway.build_receipt_v1", side_effect=_boom_then_original_again):
        second = gateway.process_with_receipt("poi", source_input)

    assert first == second
    assert first["output"]["reason_id"] == "INTERNAL_ERROR"
    assert first["receipt"]["reason_id"] == "INTERNAL_ERROR"


def test_governed_fallback_to_none_receipt_and_handoff_is_stable_when_all_fallback_builders_fail() -> None:
    gateway = _gateway("poi", _AlignedAdapter())
    source_input = {
        "task_type": "code_review",
        "model_family": "poi-v1",
        "input_payload": {"action": "evaluate_candidate"},
    }

    with (
        patch("ai_gateway.gateway.build_receipt_v1", side_effect=RuntimeError("boom")),
        patch("ai_gateway.gateway.build_handoff_v1", side_effect=RuntimeError("boom")),
    ):
        first = gateway.process_governed("poi", source_input, VALID_POLICY_PACK)

    with (
        patch("ai_gateway.gateway.build_receipt_v1", side_effect=RuntimeError("boom")),
        patch("ai_gateway.gateway.build_handoff_v1", side_effect=RuntimeError("boom")),
    ):
        second = gateway.process_governed("poi", source_input, VALID_POLICY_PACK)

    assert first == second
    assert first["output"]["reason_id"] == "INTERNAL_ERROR"
    assert first["receipt"] is None
    assert first["handoff"] is None
