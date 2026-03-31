from ai_gateway.contracts.handoff_v1 import AI_GATEWAY_HANDOFF_V1
from ai_gateway.hashing import sha256_hex
from ai_gateway.reason_ids import ReasonID
from ai_gateway.types import Envelope, Output, Receipt
from ai_gateway.validation import validate_envelope_v1, validate_output_v1, validate_receipt_v1


def _policy_decision_from_output(output: Output) -> str:
    if output["accepted"] is True:
        return "accepted"
    return "rejected"


def _context_hash_from_output(output: Output) -> str:
    context_hash = output.get("context_hash", "")
    if not isinstance(context_hash, str):
        return ""
    return context_hash


def build_handoff_v1(
    envelope: Envelope,
    output: Output,
    receipt: Receipt,
) -> dict:
    validated_envelope = validate_envelope_v1(envelope)
    validated_output = validate_output_v1(output)
    validated_receipt = validate_receipt_v1(receipt)

    handoff = {
        "handoff_version": AI_GATEWAY_HANDOFF_V1,
        "adapter": validated_output["adapter"],
        "task_type": validated_output["task_type"],
        "policy_decision": _policy_decision_from_output(validated_output),
        "reason_id": validated_output["reason_id"],
        "envelope_hash": sha256_hex(validated_envelope),
        "output_hash": sha256_hex(validated_output),
        "context_hash": _context_hash_from_output(validated_output),
    }

    if validated_receipt["envelope_hash"] != handoff["envelope_hash"]:
        raise ValueError(ReasonID.INVALID_OUTPUT.value)

    if validated_receipt["output_hash"] != handoff["output_hash"]:
        raise ValueError(ReasonID.INVALID_OUTPUT.value)

    if validated_receipt["policy_decision"] != handoff["policy_decision"]:
        raise ValueError(ReasonID.INVALID_OUTPUT.value)

    return handoff
