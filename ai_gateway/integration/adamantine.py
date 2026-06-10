from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai_gateway.validation import validate_handoff_v1, validate_receipt_v1

ADAMANTINE_AI_GATEWAY_EVIDENCE_V1 = "adamantine_ai_gateway_evidence_v1"
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
    return isinstance(value, str) and len(value) == 64 and all(ch in _HEX for ch in value)


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
    gateway_result: Mapping[str, Any],
    expected_context_hash: str,
) -> dict[str, Any]:
    """Build AdamantineOS evidence from AIGateway.process_governed output."""

    handoff = gateway_result.get("handoff")
    receipt = gateway_result.get("receipt")
    if not isinstance(handoff, Mapping):
        raise ValueError("MISSING_HANDOFF")
    if not isinstance(receipt, Mapping):
        raise ValueError("MISSING_RECEIPT")

    return build_adamantine_ai_gateway_evidence_v1(
        handoff=handoff,
        receipt=receipt,
        expected_context_hash=expected_context_hash,
    )
