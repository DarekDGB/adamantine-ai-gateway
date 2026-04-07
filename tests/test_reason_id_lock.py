from ai_gateway.errors import AdapterError, ContractError, ValidationError
from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


MANIFEST = {
    "manifest_version": "adapter_manifest_v1",
    "adapter_id": "poi",
    "adapter_version": "0.5.0",
    "entrypoint": "tests.test_reason_id_lock.PoIAdapter",
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
    "notes": "Reason ID lock tests",
}


VALID_POLICY_PACK = {
    "policypack_version": "policy_pack_v1",
    "policypack_id": "reason-lock",
    "policypack_version_id": "v1.0.0-lock",
    "default_decision": "deny",
    "adapter_policies": {
        "poi": {
            "allowed_task_types": ["code_review"],
            "allowed_model_families": ["poi-v1"],
            "allowed_actions": ["evaluate_candidate"],
        }
    },
    "notes": "Reason ID lock policy",
}


SOURCE_INPUT = {
    "task_type": "code_review",
    "model_family": "poi-v1",
    "input_payload": {"action": "evaluate_candidate"},
}


class _ValidAdapter:
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


class _MissingFieldAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class _SchemaViolationAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class _InvalidEnvelopeAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        raise ContractError(ReasonID.INVALID_ENVELOPE.value)

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class _InvalidOutputAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": "poi",
            "task_type": source_input["task_type"],
            "model_family": source_input["model_family"],
            "input_payload": source_input["input_payload"],
        }

    def build_output(self, envelope: dict) -> dict:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)


class _UnknownAdapterErrorAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        raise AdapterError("unmapped-adapter-error")

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class _UnexpectedExceptionAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        raise RuntimeError("boom")

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class _ManifestOnlyRegistry:
    def get_manifest(self, name: str) -> dict:
        if name != "poi":
            raise AdapterError(ReasonID.ADAPTER_NOT_REGISTERED.value)
        return MANIFEST

    def get(self, name: str):
        raise AdapterError(ReasonID.ADAPTER_NOT_REGISTERED.value)


def _gateway(adapter: object) -> AIGateway:
    registry = AdapterRegistry()
    registry.register("poi", adapter, manifest=MANIFEST)
    return AIGateway(registry)


def test_missing_required_field_maps_to_stable_reason_id() -> None:
    output = _gateway(_MissingFieldAdapter()).process("poi", SOURCE_INPUT)

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.MISSING_REQUIRED_FIELD.value


def test_schema_violation_maps_to_stable_reason_id() -> None:
    output = _gateway(_SchemaViolationAdapter()).process("poi", SOURCE_INPUT)

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.SCHEMA_VIOLATION.value


def test_invalid_envelope_maps_to_stable_reason_id() -> None:
    output = _gateway(_InvalidEnvelopeAdapter()).process("poi", SOURCE_INPUT)

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.INVALID_ENVELOPE.value


def test_invalid_output_maps_to_stable_reason_id() -> None:
    output = _gateway(_InvalidOutputAdapter()).process("poi", SOURCE_INPUT)

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.INVALID_OUTPUT.value


def test_policy_rejections_map_to_explicit_specific_reason_ids() -> None:
    gateway = _gateway(_ValidAdapter())

    unsupported_task = gateway.process_with_policy(
        "poi",
        {**SOURCE_INPUT, "task_type": "documentation"},
        VALID_POLICY_PACK,
    )
    unsupported_model = gateway.process_with_policy(
        "poi",
        {**SOURCE_INPUT, "model_family": "unknown-model"},
        VALID_POLICY_PACK,
    )
    denied_action = gateway.process_with_policy(
        "poi",
        {
            **SOURCE_INPUT,
            "input_payload": {"action": "not_allowed"},
        },
        VALID_POLICY_PACK,
    )

    assert unsupported_task["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert unsupported_model["reason_id"] == ReasonID.UNSUPPORTED_MODEL.value
    assert denied_action["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value


def test_unregistered_adapter_maps_to_adapter_not_registered() -> None:
    gateway = AIGateway(_ManifestOnlyRegistry())

    output = gateway.process("poi", SOURCE_INPUT)

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.ADAPTER_NOT_REGISTERED.value


def test_unmapped_adapter_error_uses_fail_closed_adapter_validation_failed_default() -> None:
    output = _gateway(_UnknownAdapterErrorAdapter()).process("poi", SOURCE_INPUT)

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value


def test_unexpected_exception_maps_only_to_internal_error() -> None:
    output = _gateway(_UnexpectedExceptionAdapter()).process("poi", SOURCE_INPUT)

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.INTERNAL_ERROR.value


def test_governed_chain_preserves_reason_id_across_output_receipt_and_handoff() -> None:
    gateway = _gateway(_ValidAdapter())

    result = gateway.process_governed(
        "poi",
        {**SOURCE_INPUT, "task_type": "documentation"},
        VALID_POLICY_PACK,
    )

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert result["receipt"] is not None
    assert result["handoff"] is not None
    assert result["receipt"]["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert result["handoff"]["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert result["receipt"]["policy_decision"] == "rejected"
    assert result["handoff"]["policy_decision"] == "rejected"
