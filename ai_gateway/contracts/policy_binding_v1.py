AI_GATEWAY_POLICY_BINDING_V1 = "ai_gateway_policy_binding_v1"
POLICY_BINDING_POLICY_PACK_CONTRACT_V1 = "policy_pack_v1"

REQUIRED_POLICY_BINDING_FIELDS = (
    "policy_binding_version",
    "policy_pack_contract_version",
    "policy_pack_id",
    "policy_pack_version_id",
    "policy_pack_hash",
    "receipt_hash",
    "handoff_hash",
)

ALLOWED_POLICY_BINDING_FIELDS = frozenset(REQUIRED_POLICY_BINDING_FIELDS)

MAX_POLICY_BINDING_ID_LENGTH = 256
MAX_POLICY_BINDING_ARTIFACT_BYTES = 4096
MAX_POLICY_SNAPSHOT_NODES = 20_000
MAX_POLICY_SNAPSHOT_CANONICAL_BYTES = 1_048_576
MAX_EXACT_JSON_INTEGER_BITS = 4096
