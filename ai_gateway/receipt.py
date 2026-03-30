from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.contracts.receipt_v1 import (
    AI_GATEWAY_RECEIPT_V1,
    RECEIPT_DETERMINISM_PROFILE_V1,
)
from ai_gateway.determinism import context_hash_for_value
from ai_gateway.types import Envelope, Manifest, Output, Receipt
from ai_gateway.validation import (
    validate_envelope_v1,
    validate_manifest_v1,
    validate_output_v1,
    validate_receipt_v1,
)
from ai_gateway.version import __version__


def build_receipt_v1(*, manifest: Manifest, envelope: Envelope, output: Output) -> Receipt:
    validated_manifest = validate_manifest_v1(manifest)
    validated_envelope = validate_envelope_v1(envelope)
    validated_output = validate_output_v1(output)

    receipt: Receipt = {
        "receipt_version": AI_GATEWAY_RECEIPT_V1,
        "gateway_version": __version__,
        "adapter_id": validated_manifest["adapter_id"],
        "adapter_version": validated_manifest["adapter_version"],
        "envelope_hash": context_hash_for_value(validated_envelope),
        "output_hash": context_hash_for_value(validated_output),
        "policy_decision": "accepted" if validated_output["accepted"] else "rejected",
        "reason_id": validated_output["reason_id"],
        "created_from_contract": AI_GATEWAY_OUTPUT_V1,
        "determinism_profile": RECEIPT_DETERMINISM_PROFILE_V1,
    }

    return validate_receipt_v1(receipt)
