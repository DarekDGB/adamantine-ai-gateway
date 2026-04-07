from ai_gateway.errors import AdapterError, ValidationError
from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID


MANIFEST = {
    "manifest_version": "adapter_manifest_v1",
    "adapter_id": "poi",
    "adapter_version": "0.5.0",
    "entrypoint": "tests.test_gateway_manifest_runtime_edges._ValidAdapter",
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
    "notes": "Gateway edge coverage tests",
}

VALID_POLICY_PACK = {
    "policypack_version": "policy_pack_v1",
    "policypack_id": "gateway-edge-lock",
    "policypack_version_id": "v1.0.0-lock",
    "default_decision": "deny",
    "adapter_policies": {
        "poi": {
            "allowed_task_types": ["code_review"],
            "allowed_model_families": ["poi-v1"],
            "allowed_actions": ["evaluate_candidate"],
        }
    },
    "notes": "Gateway edge coverage tests",
}

SOURCE_INPUT = {
    "task_type": "code_review",
    "model_family": "poi-v1",
    "input_payload": {"action": "evaluate_candidate"},
}


class _ManifestMissingRegistry:
    def get_manifest(self, name: str) -> dict:
        raise AdapterError(ReasonID.ADAPTER_NOT_REGISTERED.value)

    def get(self, name: str):
        raise AssertionError("should not be called")


class _AdapterMissingRegistry:
    def get_manifest(self, name: str) -> dict:
        return MANIFEST

    def get(self, name: str):
        raise AdapterError(ReasonID.ADAPTER_NOT_REGISTERED.value)


class _ValidationAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class _BoomAdapter:
    def build_envelope(self, source_input: dict) -> dict:
        raise RuntimeError("boom")

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


def test_process_with_policy_fails_closed_when_manifest_lookup_fails() -> None:
    gateway = AIGateway(_ManifestMissingRegistry())

    result = gateway.process_with_policy("poi", SOURCE_INPUT, VALID_POLICY_PACK)

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.ADAPTER_NOT_REGISTERED.value


def test_process_governed_fails_closed_when_adapter_lookup_fails_after_manifest_lookup() -> None:
    gateway = AIGateway(_AdapterMissingRegistry())

    result = gateway.process_governed("poi", SOURCE_INPUT, VALID_POLICY_PACK)

    assert result["output"]["accepted"] is False
    assert result["output"]["reason_id"] == ReasonID.ADAPTER_NOT_REGISTERED.value
    assert result["receipt"] is not None
    assert result["handoff"] is not None
    assert result["receipt"]["reason_id"] == ReasonID.ADAPTER_NOT_REGISTERED.value
    assert result["handoff"]["reason_id"] == ReasonID.ADAPTER_NOT_REGISTERED.value


def test_process_with_policy_maps_validation_error_in_policy_path() -> None:
    class _Registry:
        def get_manifest(self, name: str) -> dict:
            return MANIFEST

        def get(self, name: str):
            return _ValidationAdapter()

    gateway = AIGateway(_Registry())

    result = gateway.process_with_policy("poi", SOURCE_INPUT, VALID_POLICY_PACK)

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.MISSING_REQUIRED_FIELD.value


def test_process_with_policy_maps_unexpected_exception_in_policy_path() -> None:
    class _Registry:
        def get_manifest(self, name: str) -> dict:
            return MANIFEST

        def get(self, name: str):
            return _BoomAdapter()

    gateway = AIGateway(_Registry())

    result = gateway.process_with_policy("poi", SOURCE_INPUT, VALID_POLICY_PACK)

    assert result["accepted"] is False
    assert result["reason_id"] == ReasonID.INTERNAL_ERROR.value


def test_extract_action_returns_none_for_non_dict_payload() -> None:
    assert AIGateway._extract_action({"input_payload": "not-a-dict"}) is None


def test_extract_action_returns_none_for_blank_or_missing_action() -> None:
    assert AIGateway._extract_action({"input_payload": {}}) is None
    assert AIGateway._extract_action({"input_payload": {"action": ""}}) is None


def test_manifest_envelope_alignment_rejects_manifest_adapter_id_drift_directly() -> None:
    try:
        AIGateway._enforce_manifest_envelope_alignment(
            adapter_name="poi",
            manifest={**MANIFEST, "adapter_id": "wallet"},
            envelope={
                "contract_version": "ai_gateway_envelope_v1",
                "adapter": "poi",
                "task_type": "code_review",
                "model_family": "poi-v1",
                "input_payload": {"action": "evaluate_candidate"},
            },
        )
    except Exception as exc:
        assert str(exc) == ReasonID.INVALID_ENVELOPE.value
    else:
        raise AssertionError("manifest adapter drift must fail closed")
