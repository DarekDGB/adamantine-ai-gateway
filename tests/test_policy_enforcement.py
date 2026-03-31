import pytest

from ai_gateway.contracts.policypack_v1 import POLICYPACK_V1
from ai_gateway.errors import AdapterError, ContractError, PolicyError, ValidationError
from ai_gateway.gateway import AIGateway
from ai_gateway.policy import enforce_policy_for_adapter
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


def _manifest(adapter_id: str) -> dict:
    return {
        "manifest_version": "adapter_manifest_v1",
        "adapter_id": adapter_id,
        "adapter_version": "0.5.0",
        "entrypoint": f"tests.test_policy_enforcement.{adapter_id}",
        "accepted_input_types": ["policy_test_input"],
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
        "notes": "Policy enforcement test manifest",
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


class _ValidationErrorAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class _ContractErrorAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        raise ContractError(ReasonID.INVALID_ENVELOPE.value)

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class _AdapterErrorAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "poi",
            "task_type": source_input["task_type"],
            "model_family": source_input["model_family"],
            "input_payload": source_input.get("input_payload", {}),
        }

    def build_output(self, envelope: dict) -> dict:
        raise AdapterError(ReasonID.ADAPTER_VALIDATION_FAILED.value)


class _UnexpectedExceptionAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "poi",
            "task_type": source_input["task_type"],
            "model_family": source_input["model_family"],
            "input_payload": source_input.get("input_payload", {}),
        }

    def build_output(self, envelope: dict) -> dict:
        raise RuntimeError("boom")


class _NonDictPayloadAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "poi",
            "task_type": source_input["task_type"],
            "model_family": source_input["model_family"],
            "input_payload": "not-a-dict",
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


class _EmptyActionAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "poi",
            "task_type": source_input["task_type"],
            "model_family": source_input["model_family"],
            "input_payload": {"action": ""},
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
    registry.register("poi", _DummyAdapter(), manifest=_manifest("poi"))
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


def test_enforce_policy_rejects_missing_adapter_policy() -> None:
    with pytest.raises(PolicyError, match=ReasonID.POLICY_DENIED.value):
        enforce_policy_for_adapter(
            policy_pack=_policy_pack(),
            adapter_name="wallet",
            task_type="wallet_operation",
            model_family="wallet-v1",
            action="build_transaction",
        )


def test_process_with_policy_rejects_unregistered_adapter() -> None:
    gateway = AIGateway(AdapterRegistry())

    result = gateway.process_with_policy(
        adapter_name="not-registered",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.ADAPTER_NOT_REGISTERED.value


def test_process_with_policy_rejects_manifestless_registered_adapter() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _DummyAdapter())
    gateway = AIGateway(registry)

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value


def test_process_with_policy_maps_validation_error() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _ValidationErrorAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.SCHEMA_VIOLATION.value


def test_process_with_policy_maps_contract_error() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _ContractErrorAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.INVALID_ENVELOPE.value


def test_process_with_policy_maps_adapter_error() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _AdapterErrorAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value


def test_process_with_policy_maps_unexpected_exception_to_internal_error() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _UnexpectedExceptionAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"action": "evaluate_candidate"},
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.INTERNAL_ERROR.value


def test_process_with_policy_treats_non_dict_action_payload_as_no_action() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _NonDictPayloadAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is True
    assert result["reason_id"] == "ACCEPTED"


def test_process_with_policy_treats_empty_action_as_no_action() -> None:
    registry = AdapterRegistry()
    registry.register("poi", _EmptyActionAdapter(), manifest=_manifest("poi"))
    gateway = AIGateway(registry)

    result = gateway.process_with_policy(
        adapter_name="poi",
        source_input={
            "task_type": "code_review",
            "model_family": "poi-v1",
        },
        policy_pack=_policy_pack(),
    )

    assert result["accepted"] is True
    assert result["reason_id"] == "ACCEPTED"
