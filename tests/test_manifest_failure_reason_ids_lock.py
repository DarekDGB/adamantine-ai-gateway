from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


VALID_POLICY_PACK = {
    "policypack_version": "policy_pack_v1",
    "policypack_id": "manifest-reason-lock",
    "policypack_version_id": "v1.0.0-lock",
    "default_decision": "deny",
    "adapter_policies": {
        "poi": {
            "allowed_task_types": ["code_review"],
            "allowed_model_families": ["poi-v1"],
            "allowed_actions": ["evaluate_candidate"],
        }
    },
    "notes": "Manifest failure_reason_ids lock tests",
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
            "reason_id": ReasonID.ACCEPTED.value,
            "output_payload": {},
            "context_hash": "",
        }


BASE_MANIFEST = {
    "manifest_version": "adapter_manifest_v1",
    "adapter_id": "poi",
    "adapter_version": "0.5.0",
    "entrypoint": "tests.test_manifest_failure_reason_ids_lock._ValidAdapter",
    "accepted_input_types": ["poi_candidate"],
    "supported_actions": ["evaluate_candidate"],
    "required_payload_fields": ["task_type", "model_family", "input_payload"],
    "optional_payload_fields": [],
    "output_contract": "ai_gateway_output_v1",
    "determinism_constraints": ["canonical_json_only"],
    "failure_reason_ids": [
        ReasonID.ACCEPTED.value,
        ReasonID.INVALID_ENVELOPE.value,
        ReasonID.INVALID_OUTPUT.value,
        ReasonID.SCHEMA_VIOLATION.value,
        ReasonID.MISSING_REQUIRED_FIELD.value,
        ReasonID.POLICY_DENIED.value,
        ReasonID.UNSUPPORTED_TASK.value,
        ReasonID.UNSUPPORTED_MODEL.value,
        ReasonID.ADAPTER_NOT_REGISTERED.value,
        ReasonID.ADAPTER_VALIDATION_FAILED.value,
        ReasonID.INTERNAL_ERROR.value,
    ],
    "notes": "Manifest failure_reason_ids lock tests",
}


def _registered_gateway(manifest: dict) -> AIGateway:
    registry = AdapterRegistry()
    registry.register("poi", _ValidAdapter(), manifest=manifest)
    return AIGateway(registry)


def _manifest_reason_ids(manifest: dict) -> set[str]:
    return set(manifest["failure_reason_ids"])


def _all_known_reason_id_values() -> set[str]:
    return {reason.value for reason in ReasonID}


def _required_fail_closed_reasons() -> set[str]:
    return {
        ReasonID.INVALID_ENVELOPE.value,
        ReasonID.INVALID_OUTPUT.value,
        ReasonID.SCHEMA_VIOLATION.value,
        ReasonID.MISSING_REQUIRED_FIELD.value,
        ReasonID.POLICY_DENIED.value,
        ReasonID.UNSUPPORTED_TASK.value,
        ReasonID.UNSUPPORTED_MODEL.value,
        ReasonID.ADAPTER_NOT_REGISTERED.value,
        ReasonID.ADAPTER_VALIDATION_FAILED.value,
        ReasonID.INTERNAL_ERROR.value,
    }


def test_manifest_failure_reason_ids_are_known_reason_ids() -> None:
    unknown = _manifest_reason_ids(BASE_MANIFEST) - _all_known_reason_id_values()
    assert unknown == set()


def test_manifest_failure_reason_ids_contain_no_duplicates() -> None:
    reason_ids = BASE_MANIFEST["failure_reason_ids"]
    assert len(reason_ids) == len(set(reason_ids))


def test_manifest_failure_reason_ids_include_accepted_for_successful_adapter() -> None:
    result = _registered_gateway(BASE_MANIFEST).process("poi", SOURCE_INPUT)

    assert result["accepted"] is True
    assert result["reason_id"] == ReasonID.ACCEPTED.value
    assert ReasonID.ACCEPTED.value in BASE_MANIFEST["failure_reason_ids"]


def test_manifest_failure_reason_ids_include_required_fail_closed_reasons() -> None:
    manifest_reasons = _manifest_reason_ids(BASE_MANIFEST)
    missing = _required_fail_closed_reasons() - manifest_reasons
    assert missing == set()


def test_manifest_failure_reason_ids_cover_real_emitted_policy_reasons() -> None:
    gateway = _registered_gateway(BASE_MANIFEST)

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
        {**SOURCE_INPUT, "input_payload": {"action": "not_allowed"}},
        VALID_POLICY_PACK,
    )

    manifest_reasons = _manifest_reason_ids(BASE_MANIFEST)

    assert unsupported_task["reason_id"] in manifest_reasons
    assert unsupported_task["reason_id"] == ReasonID.UNSUPPORTED_TASK.value

    assert unsupported_model["reason_id"] in manifest_reasons
    assert unsupported_model["reason_id"] == ReasonID.UNSUPPORTED_MODEL.value

    assert denied_action["reason_id"] in manifest_reasons
    assert denied_action["reason_id"] == ReasonID.POLICY_DENIED.value


def test_manifest_failure_reason_ids_cover_real_emitted_validation_reasons() -> None:
    gateway = _registered_gateway(BASE_MANIFEST)

    missing_field = gateway.process(
        "poi",
        {
            "task_type": "code_review",
            "model_family": "poi-v1",
        },
    )

    manifest_reasons = _manifest_reason_ids(BASE_MANIFEST)

    assert missing_field["accepted"] is False
    assert missing_field["reason_id"] == ReasonID.MISSING_REQUIRED_FIELD.value
    assert missing_field["reason_id"] in manifest_reasons


def test_manifest_missing_emitted_reason_is_detected() -> None:
    manifest = dict(BASE_MANIFEST)
    manifest["failure_reason_ids"] = [
        reason
        for reason in BASE_MANIFEST["failure_reason_ids"]
        if reason != ReasonID.UNSUPPORTED_TASK.value
    ]

    gateway = _registered_gateway(manifest)
    result = gateway.process_with_policy(
        "poi",
        {**SOURCE_INPUT, "task_type": "documentation"},
        VALID_POLICY_PACK,
    )

    declared = _manifest_reason_ids(manifest)

    assert result["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert result["reason_id"] not in declared


def test_manifest_with_unknown_reason_id_is_detected() -> None:
    manifest = dict(BASE_MANIFEST)
    manifest["failure_reason_ids"] = BASE_MANIFEST["failure_reason_ids"] + ["NOT_A_REAL_REASON"]

    unknown = _manifest_reason_ids(manifest) - _all_known_reason_id_values()

    assert unknown == {"NOT_A_REAL_REASON"}
