import pytest

from ai_gateway.contracts.policypack_v1 import POLICYPACK_V1
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.validation import validate_policypack_v1


def _valid_policy_pack() -> dict:
    return {
        "policypack_version": POLICYPACK_V1,
        "policypack_id": "gateway-governed",
        "policypack_version_id": "v0.5.0",
        "default_decision": "deny",
        "adapter_policies": {
            "poi": {
                "allowed_task_types": ["code_review", "documentation"],
                "allowed_model_families": ["poi-v1", "deterministic-test-model"],
                "allowed_actions": ["evaluate_candidate"],
            },
            "wallet": {
                "allowed_task_types": ["wallet_operation"],
                "allowed_model_families": ["wallet-v1"],
                "allowed_actions": ["build_transaction", "sign_transaction_request"],
            },
        },
        "notes": "governed production policy pack",
    }


def test_validate_policypack_v1_accepts_valid_contract() -> None:
    policy_pack = _valid_policy_pack()

    validated = validate_policypack_v1(policy_pack)

    assert validated == policy_pack


def test_validate_policypack_v1_rejects_unknown_top_level_field() -> None:
    policy_pack = _valid_policy_pack()
    policy_pack["unexpected"] = True

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_policypack_v1(policy_pack)


def test_validate_policypack_v1_rejects_wrong_contract_version() -> None:
    policy_pack = _valid_policy_pack()
    policy_pack["policypack_version"] = "wrong"

    with pytest.raises(ContractError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_policypack_v1(policy_pack)


def test_validate_policypack_v1_rejects_missing_required_top_level_field() -> None:
    policy_pack = _valid_policy_pack()
    del policy_pack["notes"]

    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_policypack_v1(policy_pack)


def test_validate_policypack_v1_rejects_non_deny_default() -> None:
    policy_pack = _valid_policy_pack()
    policy_pack["default_decision"] = "allow"

    with pytest.raises(ContractError, match=ReasonID.POLICY_DENIED.value):
        validate_policypack_v1(policy_pack)


def test_validate_policypack_v1_rejects_empty_adapter_policies() -> None:
    policy_pack = _valid_policy_pack()
    policy_pack["adapter_policies"] = {}

    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_policypack_v1(policy_pack)


def test_validate_policypack_v1_rejects_unknown_adapter_policy_field() -> None:
    policy_pack = _valid_policy_pack()
    policy_pack["adapter_policies"]["poi"]["notes"] = "not allowed"

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_policypack_v1(policy_pack)


def test_validate_policypack_v1_rejects_missing_adapter_policy_field() -> None:
    policy_pack = _valid_policy_pack()
    del policy_pack["adapter_policies"]["poi"]["allowed_actions"]

    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_policypack_v1(policy_pack)


def test_validate_policypack_v1_rejects_duplicate_string_entries() -> None:
    policy_pack = _valid_policy_pack()
    policy_pack["adapter_policies"]["poi"]["allowed_actions"] = [
        "evaluate_candidate",
        "evaluate_candidate",
    ]

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_policypack_v1(policy_pack)


def test_validate_policypack_v1_rejects_non_string_adapter_id() -> None:
    policy_pack = _valid_policy_pack()
    policy_pack["adapter_policies"] = {
        123: {
            "allowed_task_types": ["code_review"],
            "allowed_model_families": ["poi-v1"],
            "allowed_actions": ["evaluate_candidate"],
        }
    }

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_policypack_v1(policy_pack)


def test_validate_policypack_v1_rejects_float_inside_policy_values() -> None:
    policy_pack = _valid_policy_pack()
    policy_pack["adapter_policies"]["poi"]["allowed_task_types"] = [
        "code_review",
        1.25,
    ]

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_policypack_v1(policy_pack)
