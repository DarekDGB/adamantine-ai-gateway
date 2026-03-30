import pytest

from ai_gateway.contracts.manifest_v1 import ADAPTER_MANIFEST_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.validation import validate_manifest_v1


def valid_manifest() -> dict:
    return {
        "manifest_version": ADAPTER_MANIFEST_V1,
        "adapter_id": "poi",
        "adapter_version": "0.3.0",
        "entrypoint": "ai_gateway.adapters.poi.PoIAdapter",
        "accepted_input_types": ["poi_candidate"],
        "supported_actions": ["evaluate_candidate"],
        "required_payload_fields": ["task_type", "model_family", "input_payload"],
        "optional_payload_fields": [],
        "output_contract": AI_GATEWAY_OUTPUT_V1,
        "determinism_constraints": ["canonical_json_only"],
        "failure_reason_ids": ["ACCEPTED", ReasonID.POLICY_DENIED.value],
        "notes": "PoI adapter boundary",
    }


def test_validate_manifest_v1_accepts_valid_manifest() -> None:
    manifest = valid_manifest()

    validated = validate_manifest_v1(manifest)

    assert validated == manifest


def test_validate_manifest_v1_rejects_unknown_field() -> None:
    manifest = valid_manifest()
    manifest["unexpected"] = True

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_manifest_v1(manifest)


def test_validate_manifest_v1_rejects_invalid_manifest_version() -> None:
    manifest = valid_manifest()
    manifest["manifest_version"] = "wrong"

    with pytest.raises(ContractError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_manifest_v1(manifest)


def test_validate_manifest_v1_rejects_unknown_reason_id() -> None:
    manifest = valid_manifest()
    manifest["failure_reason_ids"] = ["NOT_REAL"]

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_manifest_v1(manifest)


def test_validate_manifest_v1_rejects_missing_required_field() -> None:
    manifest = valid_manifest()
    del manifest["notes"]

    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_manifest_v1(manifest)


def test_validate_manifest_v1_rejects_blank_string_field() -> None:
    manifest = valid_manifest()
    manifest["notes"] = "   "

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_manifest_v1(manifest)


def test_validate_manifest_v1_rejects_non_list_field() -> None:
    manifest = valid_manifest()
    manifest["supported_actions"] = "evaluate_candidate"

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_manifest_v1(manifest)


def test_validate_manifest_v1_rejects_duplicate_list_entries() -> None:
    manifest = valid_manifest()
    manifest["supported_actions"] = ["evaluate_candidate", "evaluate_candidate"]

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_manifest_v1(manifest)


def test_validate_manifest_v1_rejects_wrong_output_contract() -> None:
    manifest = valid_manifest()
    manifest["output_contract"] = "wrong_output_contract"

    with pytest.raises(ContractError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_manifest_v1(manifest)
