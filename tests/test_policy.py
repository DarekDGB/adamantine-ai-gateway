from ai_gateway.policy import (
    ALLOWED_MODEL_FAMILIES,
    ALLOWED_TASK_TYPES,
    is_model_family_allowed,
    is_task_type_allowed,
    policy_reason_for,
)
from ai_gateway.reason_ids import ReasonID


def test_allowed_task_types_are_locked() -> None:
    assert ALLOWED_TASK_TYPES == (
        "code_review",
        "test_generation",
        "documentation",
        "bug_report",
    )


def test_allowed_model_families_are_locked() -> None:
    assert ALLOWED_MODEL_FAMILIES == (
        "deterministic-test-model",
        "poi-v1",
    )


def test_is_task_type_allowed_true_for_allowlisted_value() -> None:
    assert is_task_type_allowed("code_review") is True


def test_is_task_type_allowed_false_for_unknown_value() -> None:
    assert is_task_type_allowed("unknown_task") is False


def test_is_model_family_allowed_true_for_allowlisted_value() -> None:
    assert is_model_family_allowed("poi-v1") is True


def test_is_model_family_allowed_false_for_unknown_value() -> None:
    assert is_model_family_allowed("unknown-model") is False


def test_policy_reason_for_returns_unsupported_task_first() -> None:
    assert policy_reason_for("unknown_task", "poi-v1") == ReasonID.UNSUPPORTED_TASK


def test_policy_reason_for_returns_unsupported_model() -> None:
    assert policy_reason_for("code_review", "unknown-model") == ReasonID.UNSUPPORTED_MODEL


def test_policy_reason_for_returns_none_when_allowed() -> None:
    assert policy_reason_for("code_review", "poi-v1") is None
