from ai_gateway.reason_ids import ReasonID


ALLOWED_TASK_TYPES = (
    "code_review",
    "test_generation",
    "documentation",
    "bug_report",
)

ALLOWED_MODEL_FAMILIES = (
    "deterministic-test-model",
    "poi-v1",
)


def is_task_type_allowed(task_type: str) -> bool:
    return task_type in ALLOWED_TASK_TYPES


def is_model_family_allowed(model_family: str) -> bool:
    return model_family in ALLOWED_MODEL_FAMILIES


def policy_reason_for(task_type: str, model_family: str) -> ReasonID | None:
    if not is_task_type_allowed(task_type):
        return ReasonID.UNSUPPORTED_TASK
    if not is_model_family_allowed(model_family):
        return ReasonID.UNSUPPORTED_MODEL
    return None
