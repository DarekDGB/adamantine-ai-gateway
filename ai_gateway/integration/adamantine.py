from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai_gateway.contracts.receipt_v1 import RECEIPT_DETERMINISM_PROFILE_V1
from ai_gateway.hashing import sha256_hex
from ai_gateway.policy_binding import _snapshot_exact_json_artifact
from ai_gateway.reason_ids import ReasonID
from ai_gateway.validation import (
    validate_handoff_v1,
    validate_output_v1,
    validate_policy_binding_v1,
    validate_receipt_v1,
)

ADAMANTINE_AI_GATEWAY_EVIDENCE_V1 = "adamantine_ai_gateway_evidence_v1"
ADAMANTINE_AI_GATEWAY_EVIDENCE_V2 = "adamantine_ai_gateway_evidence_v2"
ADAMANTINE_AI_GATEWAY_SOURCE = "adamantine-ai-gateway"
ADAMANTINE_EVIDENCE_ROLE = "evidence_only"
_HEX = frozenset("0123456789abcdef")

_FORBIDDEN_AUTHORITY_FIELDS = frozenset(
    {
        "allow",
        "approve",
        "approved",
        "authority",
        "authorization",
        "bypass",
        "final_approval",
        "grant_execution",
        "handoff_allowed",
        "override",
    }
)


def _is_sha256_hex(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(ch in _HEX for ch in value)


def _contains_forbidden_authority_field(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if isinstance(key, str) and key in _FORBIDDEN_AUTHORITY_FIELDS:
                return True
            if _contains_forbidden_authority_field(child):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_authority_field(item) for item in value)
    return False


def _receipt_matches_handoff(handoff: Mapping[str, Any], receipt: Mapping[str, Any]) -> bool:
    return (
        receipt.get("adapter_id") == handoff.get("adapter")
        and receipt.get("envelope_hash") == handoff.get("envelope_hash")
        and receipt.get("output_hash") == handoff.get("output_hash")
        and receipt.get("policy_decision") == handoff.get("policy_decision")
        and receipt.get("reason_id") == handoff.get("reason_id")
    )


def _reason_semantics_are_valid(policy_decision: str, reason_id: str) -> bool:
    if policy_decision == "accepted":
        return reason_id == "ACCEPTED"
    if reason_id == "ACCEPTED":
        return False
    try:
        ReasonID(reason_id)
    except ValueError:
        return False
    return True


def _output_matches_evidence(
    output: Mapping[str, Any],
    handoff: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> bool:
    policy_decision = "accepted" if output.get("accepted") else "rejected"
    return (
        output.get("adapter") == handoff.get("adapter")
        and output.get("adapter") == receipt.get("adapter_id")
        and output.get("task_type") == handoff.get("task_type")
        and output.get("context_hash") == handoff.get("context_hash")
        and policy_decision == handoff.get("policy_decision")
        and policy_decision == receipt.get("policy_decision")
        and output.get("reason_id") == handoff.get("reason_id")
        and output.get("reason_id") == receipt.get("reason_id")
        and sha256_hex(output) == handoff.get("output_hash")
        and sha256_hex(output) == receipt.get("output_hash")
        and _reason_semantics_are_valid(policy_decision, output.get("reason_id"))
    )


def build_adamantine_ai_gateway_evidence_v1(
    *,
    handoff: Mapping[str, Any],
    receipt: Mapping[str, Any],
    expected_context_hash: str,
) -> dict[str, Any]:
    """Build AdamantineOS-consumable AI Gateway evidence.

    The AI Gateway remains an evidence producer only. This exporter creates a
    deterministic handoff bundle for AdamantineOS without adding any final
    approval or execution authority field.
    """

    if not _is_sha256_hex(expected_context_hash):
        raise ValueError("INVALID_CONTEXT_HASH")

    validated_handoff = validate_handoff_v1(handoff)
    validated_receipt = validate_receipt_v1(receipt)

    if _contains_forbidden_authority_field(validated_handoff):
        raise ValueError("AUTHORITY_FIELD_FORBIDDEN")
    if _contains_forbidden_authority_field(validated_receipt):
        raise ValueError("AUTHORITY_FIELD_FORBIDDEN")

    if validated_handoff["context_hash"] != expected_context_hash:
        raise ValueError("CONTEXT_HASH_MISMATCH")

    if not _receipt_matches_handoff(validated_handoff, validated_receipt):
        raise ValueError("RECEIPT_MISMATCH")

    return {
        "evidence_version": ADAMANTINE_AI_GATEWAY_EVIDENCE_V1,
        "source": ADAMANTINE_AI_GATEWAY_SOURCE,
        "evidence_role": ADAMANTINE_EVIDENCE_ROLE,
        "expected_context_hash": expected_context_hash,
        "handoff": dict(validated_handoff),
        "receipt": dict(validated_receipt),
    }


def build_adamantine_ai_gateway_evidence_from_gateway_result_v1(
    *,
    gateway_result: dict[str, Any],
    expected_context_hash: str,
) -> dict[str, Any]:
    """Build AdamantineOS evidence from AIGateway.process_governed output."""

    if type(gateway_result) is not dict:
        raise ValueError("GATEWAY_RESULT_SCHEMA_INVALID")
    normalized_result = _snapshot_exact_json_artifact(gateway_result)
    if "policy_binding" in normalized_result:
        raise ValueError("POLICY_BOUND_RESULT_REQUIRES_EVIDENCE_V2")

    handoff = normalized_result.get("handoff")
    receipt = normalized_result.get("receipt")
    if not isinstance(handoff, Mapping):
        raise ValueError("MISSING_HANDOFF")
    if not isinstance(receipt, Mapping):
        raise ValueError("MISSING_RECEIPT")

    return build_adamantine_ai_gateway_evidence_v1(
        handoff=handoff,
        receipt=receipt,
        expected_context_hash=expected_context_hash,
    )


def build_adamantine_ai_gateway_evidence_v2(
    *,
    handoff: dict[str, Any],
    receipt: dict[str, Any],
    policy_binding: dict[str, Any],
    expected_context_hash: str,
) -> dict[str, Any]:
    """Build policy-bound evidence for an independent AdamantineOS consumer."""

    if not _is_sha256_hex(expected_context_hash):
        raise ValueError("INVALID_CONTEXT_HASH")
    if type(handoff) is not dict:
        raise ValueError("MISSING_HANDOFF")
    if type(receipt) is not dict:
        raise ValueError("MISSING_RECEIPT")
    if type(policy_binding) is not dict:
        raise ValueError("MISSING_POLICY_BINDING")

    artifacts = _snapshot_exact_json_artifact(
        {
            "handoff": handoff,
            "receipt": receipt,
            "policy_binding": policy_binding,
        }
    )
    validated_handoff = validate_handoff_v1(
        artifacts["handoff"]
    )
    validated_receipt = validate_receipt_v1(
        artifacts["receipt"]
    )
    validated_binding = validate_policy_binding_v1(
        artifacts["policy_binding"]
    )

    for artifact in (validated_handoff, validated_receipt, validated_binding):
        if _contains_forbidden_authority_field(artifact):
            raise ValueError("AUTHORITY_FIELD_FORBIDDEN")

    if validated_handoff["context_hash"] != expected_context_hash:
        raise ValueError("CONTEXT_HASH_MISMATCH")
    if validated_handoff["context_hash"] != validated_handoff["envelope_hash"]:
        raise ValueError("CONTEXT_ENVELOPE_HASH_MISMATCH")
    if not _receipt_matches_handoff(validated_handoff, validated_receipt):
        raise ValueError("RECEIPT_MISMATCH")
    if not _reason_semantics_are_valid(
        validated_handoff["policy_decision"],
        validated_handoff["reason_id"],
    ):
        raise ValueError("EVIDENCE_SEMANTICS_MISMATCH")
    if validated_receipt["determinism_profile"] != RECEIPT_DETERMINISM_PROFILE_V1:
        raise ValueError("UNSUPPORTED_DETERMINISM_PROFILE")
    if validated_binding["receipt_hash"] != sha256_hex(validated_receipt):
        raise ValueError("POLICY_BINDING_RECEIPT_HASH_MISMATCH")
    if validated_binding["handoff_hash"] != sha256_hex(validated_handoff):
        raise ValueError("POLICY_BINDING_HANDOFF_HASH_MISMATCH")

    return {
        "evidence_version": ADAMANTINE_AI_GATEWAY_EVIDENCE_V2,
        "source": ADAMANTINE_AI_GATEWAY_SOURCE,
        "evidence_role": ADAMANTINE_EVIDENCE_ROLE,
        "expected_context_hash": expected_context_hash,
        "handoff": dict(validated_handoff),
        "receipt": dict(validated_receipt),
        "policy_binding": dict(validated_binding),
    }


def build_adamantine_ai_gateway_evidence_from_gateway_result_v2(
    *,
    gateway_result: dict[str, Any],
    expected_context_hash: str,
) -> dict[str, Any]:
    """Build V2 evidence from the exact policy-bound Gateway result shape."""

    if type(gateway_result) is not dict:
        raise ValueError("GATEWAY_RESULT_SCHEMA_INVALID")
    normalized_result = _snapshot_exact_json_artifact(gateway_result)
    if set(normalized_result) != {"output", "receipt", "handoff", "policy_binding"}:
        raise ValueError("GATEWAY_RESULT_SCHEMA_INVALID")

    handoff = normalized_result["handoff"]
    receipt = normalized_result["receipt"]
    policy_binding = normalized_result["policy_binding"]
    output = normalized_result["output"]
    if type(output) is not dict:
        raise ValueError("MISSING_OUTPUT")
    if type(handoff) is not dict:
        raise ValueError("MISSING_HANDOFF")
    if type(receipt) is not dict:
        raise ValueError("MISSING_RECEIPT")
    if type(policy_binding) is not dict:
        raise ValueError("MISSING_POLICY_BINDING")

    validated_output = validate_output_v1(output)
    validated_handoff = validate_handoff_v1(handoff)
    validated_receipt = validate_receipt_v1(receipt)
    if not _output_matches_evidence(
        validated_output,
        validated_handoff,
        validated_receipt,
    ):
        raise ValueError("OUTPUT_EVIDENCE_MISMATCH")

    return build_adamantine_ai_gateway_evidence_v2(
        handoff=validated_handoff,
        receipt=validated_receipt,
        policy_binding=policy_binding,
        expected_context_hash=expected_context_hash,
    )
