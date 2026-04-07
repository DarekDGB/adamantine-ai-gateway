from unittest.mock import patch

from ai_gateway.errors import AdapterError, PolicyError, ValidationError
from ai_gateway.gateway import AIGateway
from ai_gateway.registry import AdapterRegistry


class LegacyAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "legacy",
            "task_type": "code_review",
            "model_family": "legacy-v1",
            "input_payload": {},
        }

    def build_output(self, envelope: dict) -> dict:
        return {
            "contract_version": "ai_gateway_output_v1",
            "adapter": "legacy",
            "task_type": "code_review",
            "accepted": True,
            "reason_id": "ACCEPTED",
            "output_payload": {"status": "accepted-candidate"},
            "context_hash": "abc123",
        }


class InvalidOutputWithManifestAdapter:
    @property
    def manifest(self) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": "broken",
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_gateway_receipt.InvalidOutputWithManifestAdapter",
            "accepted_input_types": ["broken_input"],
            "supported_actions": ["evaluate_candidate"],
            "required_payload_fields": ["candidate_id"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["ACCEPTED", "INVALID_OUTPUT", "INTERNAL_ERROR"],
            "notes": "Broken adapter for receipt fallback tests",
        }

    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "broken",
            "task_type": "code_review",
            "model_family": "broken-v1",
            "input_payload": {"candidate_id": source_input.get("candidate_id", "1")},
        }

    def build_output(self, envelope: dict) -> dict:
        return {
            "contract_version": "wrong_output_contract",
            "adapter": "broken",
            "task_type": "code_review",
            "accepted": True,
            "reason_id": "ACCEPTED",
            "output_payload": {"status": "accepted-candidate"},
            "context_hash": "abc123",
        }


class ExplodingManifestAdapter:
    @property
    def manifest(self) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": "explode",
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_gateway_receipt.ExplodingManifestAdapter",
            "accepted_input_types": ["explode_input"],
            "supported_actions": ["evaluate_candidate"],
            "required_payload_fields": ["candidate_id"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["ACCEPTED", "INTERNAL_ERROR"],
            "notes": "Exploding adapter for gateway tests",
        }

    def build_envelope(self, source_input: dict) -> dict:
        raise RuntimeError("boom")

    def build_output(self, envelope: dict) -> dict:
        raise RuntimeError("boom")


class PoIAdapter:
    @property
    def manifest(self) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": "poi",
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_gateway_receipt.PoIAdapter",
            "accepted_input_types": ["poi_candidate"],
            "supported_actions": ["evaluate_candidate"],
            "required_payload_fields": ["task_type", "model_family", "input_payload"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["ACCEPTED", "POLICY_DENIED", "INTERNAL_ERROR"],
            "notes": "PoI adapter test manifest",
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


class ValidationManifestAdapter:
    @property
    def manifest(self) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": "validate",
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_gateway_receipt.ValidationManifestAdapter",
            "accepted_input_types": ["validate_input"],
            "supported_actions": ["evaluate_candidate"],
            "required_payload_fields": ["candidate_id"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["MISSING_REQUIRED_FIELD"],
            "notes": "Validation adapter for receipt path tests",
        }

    def build_envelope(self, source_input: dict) -> dict:
        raise ValidationError("MISSING_REQUIRED_FIELD")

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class PolicyManifestAdapter:
    @property
    def manifest(self) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": "policy",
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_gateway_receipt.PolicyManifestAdapter",
            "accepted_input_types": ["policy_input"],
            "supported_actions": ["evaluate_candidate"],
            "required_payload_fields": ["candidate_id"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["POLICY_DENIED"],
            "notes": "Policy adapter for receipt path tests",
        }

    def build_envelope(self, source_input: dict) -> dict:
        raise PolicyError("POLICY_DENIED")

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class ManifestOnlyRegistry:
    def get_manifest(self, name: str) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": name,
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_gateway_receipt.ManifestOnlyRegistry",
            "accepted_input_types": ["registry_input"],
            "supported_actions": ["evaluate_candidate"],
            "required_payload_fields": ["candidate_id"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["ADAPTER_NOT_REGISTERED"],
            "notes": "Registry test manifest",
        }

    def get(self, name: str):
        raise AdapterError("ADAPTER_NOT_REGISTERED")


def test_process_with_receipt_returns_output_and_receipt_for_manifest_adapter() -> None:
    registry = AdapterRegistry()
    registry.register("poi", PoIAdapter())
    gateway = AIGateway(registry)

    result = gateway.process_with_receipt(
        "poi",
        {
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"prompt": "hello"},
        },
    )

    assert result["output"]["accepted"] is True
    assert result["receipt"] is not None
    assert result["receipt"]["adapter_id"] == "poi"
    assert result["receipt"]["policy_decision"] == "accepted"


def test_process_with_receipt_returns_none_receipt_for_manifestless_adapter() -> None:
    registry = AdapterRegistry()
    registry.register("legacy", LegacyAdapter())
    gateway = AIGateway(registry)

    result = gateway.process_with_receipt("legacy", {})

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == "ADAPTER_VALIDATION_FAILED"
    assert result["receipt"] is None


def test_process_with_receipt_returns_none_receipt_for_unknown_adapter() -> None:
    gateway = AIGateway(AdapterRegistry())

    result = gateway.process_with_receipt("missing", {})

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == "ADAPTER_NOT_REGISTERED"
    assert result["receipt"] is None


def test_process_with_receipt_rejects_invalid_output_before_receipt_fallback() -> None:
    registry = AdapterRegistry()
    registry.register("broken", InvalidOutputWithManifestAdapter())
    gateway = AIGateway(registry)

    result = gateway.process_with_receipt("broken", {"candidate_id": "1"})

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == "INVALID_OUTPUT"
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == "INVALID_OUTPUT"
    assert result["receipt"]["policy_decision"] == "rejected"


def test_process_with_receipt_falls_back_to_internal_error_receipt_when_receipt_builder_raises() -> None:
    registry = AdapterRegistry()
    registry.register("poi", PoIAdapter())
    gateway = AIGateway(registry)

    original_builder = AIGateway.process_with_receipt.__globals__["build_receipt_v1"]

    def _receipt_side_effect(*args, **kwargs):
        if not hasattr(_receipt_side_effect, "called"):
            _receipt_side_effect.called = True
            raise RuntimeError("boom")
        return original_builder(*args, **kwargs)

    with patch("ai_gateway.gateway.build_receipt_v1", side_effect=_receipt_side_effect):
        result = gateway.process_with_receipt(
            "poi",
            {
                "task_type": "code_review",
                "model_family": "poi-v1",
                "input_payload": {"prompt": "hello"},
            },
        )

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == "INTERNAL_ERROR"
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == "INTERNAL_ERROR"
    assert result["receipt"]["policy_decision"] == "rejected"


def test_process_with_receipt_uses_fail_closed_envelope_defaults_when_adapter_raises() -> None:
    registry = AdapterRegistry()
    registry.register("explode", ExplodingManifestAdapter())
    gateway = AIGateway(registry)

    result = gateway.process_with_receipt("explode", {})

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == "INTERNAL_ERROR"
    assert result["receipt"] is not None
    assert result["receipt"]["adapter_id"] == "explode"
    assert result["receipt"]["policy_decision"] == "rejected"


def test_process_with_receipt_preserves_source_model_family_in_fail_closed_envelope() -> None:
    registry = AdapterRegistry()
    registry.register("explode", ExplodingManifestAdapter())
    gateway = AIGateway(registry)

    result = gateway.process_with_receipt(
        "explode",
        {"task_type": "code_review", "model_family": "custom-model"},
    )

    assert result["receipt"] is not None
    assert len(result["receipt"]["envelope_hash"]) == 64


def test_process_with_receipt_maps_adapter_lookup_failure_after_manifest_lookup() -> None:
    gateway = AIGateway(ManifestOnlyRegistry())

    result = gateway.process_with_receipt("ghost", {"candidate_id": "1"})

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == "ADAPTER_NOT_REGISTERED"
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == "ADAPTER_NOT_REGISTERED"


def test_process_with_receipt_maps_validation_error_from_manifest_path() -> None:
    registry = AdapterRegistry()
    registry.register("validate", ValidationManifestAdapter())
    gateway = AIGateway(registry)

    result = gateway.process_with_receipt("validate", {"candidate_id": "1"})

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == "MISSING_REQUIRED_FIELD"
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == "MISSING_REQUIRED_FIELD"


def test_process_with_receipt_maps_policy_error_from_manifest_path() -> None:
    registry = AdapterRegistry()
    registry.register("policy", PolicyManifestAdapter())
    gateway = AIGateway(registry)

    result = gateway.process_with_receipt("policy", {"candidate_id": "1"})

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == "POLICY_DENIED"
    assert result["receipt"] is not None
    assert result["receipt"]["reason_id"] == "POLICY_DENIED"
