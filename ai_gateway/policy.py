from ai_gateway.errors import PolicyError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.types import PolicyPack
from ai_gateway.validation import validate_policypack_v1


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


def get_adapter_policy(policy_pack: PolicyPack, adapter_name: str) -> dict:
    validated = validate_policypack_v1(policy_pack)

    adapter_policies = validated["adapter_policies"]
    if adapter_name not in adapter_policies:
        raise PolicyError(ReasonID.POLICY_DENIED.value)

    return adapter_policies[adapter_name]


def policy_reason_for_adapter(
    policy_pack: PolicyPack,
    adapter_name: str,
    task_type: str,
    model_family: str,
    action: str | None = None,
) -> ReasonID | None:
    adapter_policy = get_adapter_policy(policy_pack, adapter_name)

    if task_type not in adapter_policy["allowed_task_types"]:
        return ReasonID.UNSUPPORTED_TASK

    if model_family not in adapter_policy["allowed_model_families"]:
        return ReasonID.UNSUPPORTED_MODEL

    if action is not None and action not in adapter_policy["allowed_actions"]:
        return ReasonID.POLICY_DENIED

    return None


def enforce_policy_for_adapter(
    policy_pack: PolicyPack,
    adapter_name: str,
    task_type: str,
    model_family: str,
    action: str | None = None,
) -> None:
    reason = policy_reason_for_adapter(
        policy_pack=policy_pack,
        adapter_name=adapter_name,
        task_type=task_type,
        model_family=model_family,
        action=action,
    )
    if reason is not None:
        raise PolicyError(reason.value)
