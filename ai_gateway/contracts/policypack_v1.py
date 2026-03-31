POLICYPACK_V1 = "policy_pack_v1"

REQUIRED_POLICYPACK_FIELDS = (
    "policypack_version",
    "policypack_id",
    "policypack_version_id",
    "default_decision",
    "adapter_policies",
    "notes",
)

ALLOWED_POLICYPACK_FIELDS = frozenset(REQUIRED_POLICYPACK_FIELDS)
ALLOWED_POLICYPACK_DEFAULT_DECISIONS = frozenset({"deny"})

REQUIRED_ADAPTER_POLICY_FIELDS = (
    "allowed_task_types",
    "allowed_model_families",
    "allowed_actions",
)

ALLOWED_ADAPTER_POLICY_FIELDS = frozenset(REQUIRED_ADAPTER_POLICY_FIELDS)
