AI_GATEWAY_HANDOFF_V1 = "ai_gateway_handoff_v1"

REQUIRED_HANDOFF_FIELDS = (
    "handoff_version",
    "adapter",
    "task_type",
    "policy_decision",
    "reason_id",
    "envelope_hash",
    "output_hash",
    "context_hash",
)

ALLOWED_HANDOFF_FIELDS = frozenset(REQUIRED_HANDOFF_FIELDS)

ALLOWED_HANDOFF_DECISIONS = frozenset({
    "accepted",
    "rejected",
})
