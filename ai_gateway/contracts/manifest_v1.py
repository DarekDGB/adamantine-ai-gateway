ADAPTER_MANIFEST_V1 = "adapter_manifest_v1"

REQUIRED_MANIFEST_FIELDS = (
    "manifest_version",
    "adapter_id",
    "adapter_version",
    "entrypoint",
    "accepted_input_types",
    "supported_actions",
    "required_payload_fields",
    "optional_payload_fields",
    "output_contract",
    "determinism_constraints",
    "failure_reason_ids",
    "notes",
)

ALLOWED_MANIFEST_FIELDS = frozenset(REQUIRED_MANIFEST_FIELDS)
