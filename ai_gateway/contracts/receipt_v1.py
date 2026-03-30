AI_GATEWAY_RECEIPT_V1 = "ai_gateway_receipt_v1"

REQUIRED_RECEIPT_FIELDS = (
    "receipt_version",
    "gateway_version",
    "adapter_id",
    "adapter_version",
    "envelope_hash",
    "output_hash",
    "policy_decision",
    "reason_id",
    "created_from_contract",
    "determinism_profile",
)

ALLOWED_RECEIPT_FIELDS = frozenset(REQUIRED_RECEIPT_FIELDS)
ALLOWED_POLICY_DECISIONS = frozenset({"accepted", "rejected"})
RECEIPT_DETERMINISM_PROFILE_V1 = "canonical_sha256_no_time_v1"
