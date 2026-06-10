from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_gateway.integration.adamantine import (
    ADAMANTINE_AI_GATEWAY_EVIDENCE_V1,
    build_adamantine_ai_gateway_evidence_from_gateway_result_v1,
    build_adamantine_ai_gateway_evidence_v1,
)

FIXTURE = Path(__file__).parent / "fixtures" / "adamantine" / "ai_gateway_adamantine_evidence_v1.json"
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text())


def test_build_adamantine_ai_gateway_evidence_v1_matches_fixture() -> None:
    expected = _fixture()

    evidence = build_adamantine_ai_gateway_evidence_v1(
        handoff=expected["handoff"],
        receipt=expected["receipt"],
        expected_context_hash=expected["expected_context_hash"],
    )

    assert evidence == expected
    assert evidence["evidence_version"] == ADAMANTINE_AI_GATEWAY_EVIDENCE_V1
    assert evidence["evidence_role"] == "evidence_only"
    assert "final_approval" not in evidence
    assert "handoff_allowed" not in evidence


def test_build_from_gateway_result_uses_handoff_and_receipt_only() -> None:
    expected = _fixture()
    gateway_result = {
        "output": {"raw_model_output": "must not be exported as authority"},
        "handoff": expected["handoff"],
        "receipt": expected["receipt"],
    }

    evidence = build_adamantine_ai_gateway_evidence_from_gateway_result_v1(
        gateway_result=gateway_result,
        expected_context_hash=expected["expected_context_hash"],
    )

    assert evidence == expected
    assert "output" not in evidence


@pytest.mark.parametrize("bad_hash", ["", "short", "A" * 64])
def test_invalid_expected_context_hash_rejects(bad_hash: str) -> None:
    expected = _fixture()

    with pytest.raises(ValueError, match="INVALID_CONTEXT_HASH"):
        build_adamantine_ai_gateway_evidence_v1(
            handoff=expected["handoff"],
            receipt=expected["receipt"],
            expected_context_hash=bad_hash,
        )


def test_context_hash_mismatch_rejects() -> None:
    expected = _fixture()

    with pytest.raises(ValueError, match="CONTEXT_HASH_MISMATCH"):
        build_adamantine_ai_gateway_evidence_v1(
            handoff=expected["handoff"],
            receipt=expected["receipt"],
            expected_context_hash=HASH_D,
        )


def test_receipt_mismatch_rejects() -> None:
    expected = _fixture()
    receipt = dict(expected["receipt"])
    receipt["output_hash"] = HASH_D

    with pytest.raises(ValueError, match="RECEIPT_MISMATCH"):
        build_adamantine_ai_gateway_evidence_v1(
            handoff=expected["handoff"],
            receipt=receipt,
            expected_context_hash=expected["expected_context_hash"],
        )


def test_missing_gateway_result_handoff_rejects() -> None:
    expected = _fixture()

    with pytest.raises(ValueError, match="MISSING_HANDOFF"):
        build_adamantine_ai_gateway_evidence_from_gateway_result_v1(
            gateway_result={"receipt": expected["receipt"]},
            expected_context_hash=expected["expected_context_hash"],
        )


def test_missing_gateway_result_receipt_rejects() -> None:
    expected = _fixture()

    with pytest.raises(ValueError, match="MISSING_RECEIPT"):
        build_adamantine_ai_gateway_evidence_from_gateway_result_v1(
            gateway_result={"handoff": expected["handoff"]},
            expected_context_hash=expected["expected_context_hash"],
        )


def test_hidden_authority_field_rejects() -> None:
    expected = _fixture()
    handoff = dict(expected["handoff"])
    handoff["final_approval"] = True

    with pytest.raises(Exception):
        build_adamantine_ai_gateway_evidence_v1(
            handoff=handoff,
            receipt=expected["receipt"],
            expected_context_hash=expected["expected_context_hash"],
        )


def test_forbidden_authority_helper_detects_nested_mapping_and_list() -> None:
    from ai_gateway.integration import adamantine as module

    assert module._contains_forbidden_authority_field({"nested": {"override": True}}) is True
    assert module._contains_forbidden_authority_field([{"grant_execution": True}]) is True
    assert module._contains_forbidden_authority_field({"safe": ["value"]}) is False


def test_validated_handoff_authority_field_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    from ai_gateway.integration import adamantine as module

    expected = _fixture()
    monkeypatch.setattr(module, "validate_handoff_v1", lambda _handoff: {"final_approval": True})
    monkeypatch.setattr(module, "validate_receipt_v1", lambda _receipt: expected["receipt"])

    with pytest.raises(ValueError, match="AUTHORITY_FIELD_FORBIDDEN"):
        build_adamantine_ai_gateway_evidence_v1(
            handoff=expected["handoff"],
            receipt=expected["receipt"],
            expected_context_hash=expected["expected_context_hash"],
        )


def test_validated_receipt_authority_field_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    from ai_gateway.integration import adamantine as module

    expected = _fixture()
    monkeypatch.setattr(module, "validate_handoff_v1", lambda _handoff: expected["handoff"])
    monkeypatch.setattr(module, "validate_receipt_v1", lambda _receipt: {"override": True})

    with pytest.raises(ValueError, match="AUTHORITY_FIELD_FORBIDDEN"):
        build_adamantine_ai_gateway_evidence_v1(
            handoff=expected["handoff"],
            receipt=expected["receipt"],
            expected_context_hash=expected["expected_context_hash"],
        )
