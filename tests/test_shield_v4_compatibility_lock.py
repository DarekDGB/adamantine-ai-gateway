from __future__ import annotations

import ast
import json
from pathlib import Path
import tomllib

import pytest

from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.contracts.handoff_v1 import (
    ALLOWED_HANDOFF_FIELDS,
    REQUIRED_HANDOFF_FIELDS,
)
from ai_gateway.contracts.output_v1 import REQUIRED_OUTPUT_FIELDS
from ai_gateway.contracts.policy_binding_v1 import (
    ALLOWED_POLICY_BINDING_FIELDS,
    REQUIRED_POLICY_BINDING_FIELDS,
)
from ai_gateway.contracts.receipt_v1 import (
    ALLOWED_RECEIPT_FIELDS,
    REQUIRED_RECEIPT_FIELDS,
)
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.gateway import AIGateway
from ai_gateway.integration.adamantine import (
    _FORBIDDEN_AUTHORITY_FIELDS,
    build_adamantine_ai_gateway_evidence_from_gateway_result_v2,
)
from ai_gateway.registry import AdapterRegistry
from ai_gateway.validation import (
    validate_handoff_v1,
    validate_output_v1,
    validate_policy_binding_v1,
    validate_receipt_v1,
)


ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY_DOC = ROOT / "docs" / "reports" / "v4" / "SHIELD_V4_COMPATIBILITY.md"
EVIDENCE_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "adamantine"
    / "ai_gateway_adamantine_evidence_v2.json"
)

CURRENT_STATUS_DOCS = (
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "contracts" / "AI_GATEWAY_HANDOFF_V1.md",
    ROOT / "contracts" / "AI_GATEWAY_OUTPUT_V1.md",
    ROOT / "contracts" / "AI_GATEWAY_RECEIPT_V1.md",
    ROOT / "contracts" / "AI_GATEWAY_POLICY_BINDING_V1.md",
    ROOT / "contracts" / "ADAMANTINE_AI_GATEWAY_EVIDENCE_V2.md",
    ROOT / "docs" / "reports" / "v1" / "ADAMANTINEOS_INTEGRATION.md",
    ROOT / "docs" / "reports" / "v4" / "POLICY_PACK_IDENTITY_DECISION.md",
    ROOT / "docs" / "adamantine_ai_gateway_v1_0_0_INVARIANTS_LOCK.md",
    COMPATIBILITY_DOC,
)
V49E_CHANGED_PATHS = CURRENT_STATUS_DOCS + (
    ROOT / "tests" / "test_shield_v4_compatibility_lock.py",
    ROOT / "tests" / "test_v49d_policy_pack_identity_decision_lock.py",
)

SHIELD_CRYPTO_OR_AUTHORITY_FIELDS = frozenset(
    {
        "algorithm",
        "algorithm_family",
        "authority",
        "final_approval",
        "key_id",
        "key_role",
        "key_version",
        "registry_version",
        "shield_receipt",
        "shield_verdict",
        "signature",
        "signature_bundle",
        "standard_profile",
    }
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _v2_fixture() -> dict:
    value = json.loads(_read(EVIDENCE_FIXTURE))
    assert type(value) is dict
    return value


def test_normative_compatibility_document_locks_the_non_verifier_boundary() -> None:
    text = _read(COMPATIBILITY_DOC)
    required = (
        "Author attribution: **DarekDGB**",
        "does not verify Shield signatures",
        "does not parse, verify, or enforce any of these Shield algorithms",
        "has no Shield trust registry",
        "required: classical-ed25519 + ml-dsa",
        "optional: fn-dsa",
        "fips206-draft-falcon1024-v1",
        "This document makes no final FIPS 206 claim.",
        "`accepted` and `policy_decision: accepted` describe only the Gateway's local",
        "evidence_role: evidence_only",
        "final_approval == false",
        "AdamantineOS",
        "independent final fail-closed local policy and\nexecution boundary",
        "does not\n"
        "change runtime code, fixtures, workflows, dependencies, package version, public\n"
        "API, canonical bytes, or artifact hashes",
    )
    for phrase in required:
        assert phrase in text


def test_current_facing_docs_remove_stale_shield_v3_and_pending_d3_claims() -> None:
    stale_status_phrases = (
        "remains V4.9-D3B work",
        "remain V4.9-D3 work",
        "V4.9-D3  pending",
        "V4.9-E   blocked",
        "Until D3 is implemented",
        "expected-policy boundary (pending)",
    )
    for path in CURRENT_STATUS_DOCS:
        text = _read(path)
        for phrase in stale_status_phrases:
            assert phrase not in text, f"stale status in {path.relative_to(ROOT)}"

    for path in (
        ROOT / "README.md",
        ROOT / "contracts" / "AI_GATEWAY_HANDOFF_V1.md",
        ROOT / "contracts" / "AI_GATEWAY_OUTPUT_V1.md",
        ROOT / "contracts" / "AI_GATEWAY_RECEIPT_V1.md",
        COMPATIBILITY_DOC,
    ):
        assert "Shield v3" not in _read(path)

    output_contract = _read(ROOT / "contracts" / "AI_GATEWAY_OUTPUT_V1.md")
    assert "Active for `v0.1.0`" not in output_contract
    assert "Reason Semantics for v0.1.0" not in output_contract


def test_gateway_runtime_has_no_shield_or_oqs_dependency() -> None:
    imported_modules: set[str] = set()
    for path in sorted((ROOT / "ai_gateway").rglob("*.py")):
        source = _read(path)
        lowered_source = source.lower()
        assert "shield" not in lowered_source
        assert "oqs" not in lowered_source
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

    lowered = {module.lower() for module in imported_modules}
    assert not any("shield" in module for module in lowered)
    assert not any("oqs" in module for module in lowered)

    project_text = _read(ROOT / "pyproject.toml")
    assert "shield" not in project_text.lower()
    assert "oqs" not in project_text.lower()
    project = tomllib.loads(project_text)["project"]
    assert project["version"] == "1.0.0"
    assert project["dependencies"] == []

    workflows = sorted(
        path
        for path in (ROOT / ".github" / "workflows").iterdir()
        if path.suffix in {".yaml", ".yml"}
    )
    assert [path.name for path in workflows] == ["ci.yml"]
    assert "oqs" not in _read(workflows[0]).lower()


def test_gateway_contract_field_sets_remain_closed_and_non_shield() -> None:
    expected = {
        "output": (
            "contract_version",
            "adapter",
            "task_type",
            "accepted",
            "reason_id",
            "output_payload",
            "context_hash",
        ),
        "handoff": (
            "handoff_version",
            "adapter",
            "task_type",
            "policy_decision",
            "reason_id",
            "envelope_hash",
            "output_hash",
            "context_hash",
        ),
        "receipt": (
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
        ),
        "policy_binding": (
            "policy_binding_version",
            "policy_pack_contract_version",
            "policy_pack_id",
            "policy_pack_version_id",
            "policy_pack_hash",
            "receipt_hash",
            "handoff_hash",
        ),
    }

    actual = {
        "output": tuple(REQUIRED_OUTPUT_FIELDS),
        "handoff": tuple(REQUIRED_HANDOFF_FIELDS),
        "receipt": tuple(REQUIRED_RECEIPT_FIELDS),
        "policy_binding": tuple(REQUIRED_POLICY_BINDING_FIELDS),
    }
    assert actual == expected
    assert ALLOWED_HANDOFF_FIELDS == frozenset(expected["handoff"])
    assert ALLOWED_RECEIPT_FIELDS == frozenset(expected["receipt"])
    assert ALLOWED_POLICY_BINDING_FIELDS == frozenset(expected["policy_binding"])
    for fields in actual.values():
        assert not (set(fields) & SHIELD_CRYPTO_OR_AUTHORITY_FIELDS)


def test_v2_evidence_shape_is_exact_and_never_exports_output_or_approval() -> None:
    evidence = _v2_fixture()
    assert tuple(evidence) == (
        "evidence_role",
        "evidence_version",
        "expected_context_hash",
        "handoff",
        "policy_binding",
        "receipt",
        "source",
    )
    assert evidence["evidence_role"] == "evidence_only"
    assert "output" not in evidence
    assert "output_payload" not in evidence
    assert "final_approval" not in json.dumps(evidence, sort_keys=True)


def test_shield_and_authority_like_top_level_fields_fail_closed() -> None:
    evidence = _v2_fixture()
    valid_output = {
        "contract_version": "ai_gateway_output_v1",
        "adapter": "poi",
        "task_type": "code_review",
        "accepted": True,
        "reason_id": "ACCEPTED",
        "output_payload": {},
        "context_hash": evidence["expected_context_hash"],
    }
    validators_and_values = (
        (validate_output_v1, valid_output),
        (validate_handoff_v1, evidence["handoff"]),
        (validate_receipt_v1, evidence["receipt"]),
        (validate_policy_binding_v1, evidence["policy_binding"]),
    )

    for validator, valid in validators_and_values:
        for field in SHIELD_CRYPTO_OR_AUTHORITY_FIELDS | _FORBIDDEN_AUTHORITY_FIELDS:
            changed = dict(valid)
            changed[field] = False
            with pytest.raises((ContractError, ValidationError)):
                validator(changed)


def test_adapter_payload_names_remain_data_and_are_not_exported_as_evidence() -> None:
    class _UntrustedPayloadAdapter(PoIAdapter):
        def build_output(self, envelope: dict) -> dict:
            output = super().build_output(envelope)
            output["output_payload"] = {
                "signature": "untrusted-data",
                "final_approval": False,
            }
            return output

    adapter = _UntrustedPayloadAdapter()
    registry = AdapterRegistry()
    registry.register("poi", adapter, manifest=adapter.manifest)
    result = AIGateway(registry).process_governed_with_policy_binding_v1(
        "poi",
        {
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {
                "action": "evaluate_candidate",
                "prompt": "review this",
            },
        },
        {
            "policypack_version": "policy_pack_v1",
            "policypack_id": "v49e-policy",
            "policypack_version_id": "v1",
            "default_decision": "deny",
            "adapter_policies": {
                "poi": {
                    "allowed_task_types": ["code_review"],
                    "allowed_model_families": ["poi-v1"],
                    "allowed_actions": ["evaluate_candidate"],
                }
            },
            "notes": "V4.9-E payload boundary",
        },
    )
    output = result["output"]
    handoff = result["handoff"]
    assert type(output) is dict
    assert type(handoff) is dict
    assert output["output_payload"]["signature"] == "untrusted-data"
    assert output["output_payload"]["final_approval"] is False

    evidence = build_adamantine_ai_gateway_evidence_from_gateway_result_v2(
        gateway_result=result,
        expected_context_hash=handoff["context_hash"],
    )
    assert "output" not in evidence
    assert "output_payload" not in evidence
    assert "final_approval" not in json.dumps(evidence, sort_keys=True)


def test_all_ten_authority_names_remain_recursively_forbidden() -> None:
    assert _FORBIDDEN_AUTHORITY_FIELDS == frozenset(
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


def test_v49e_document_attribution_is_darekdgb_only() -> None:
    assert _read(Path(__file__).resolve()).isascii()
    allowed_attribution_lines = frozenset(
        {
            "Author attribution: DarekDGB",
            "Owner attribution: DarekDGB",
            "MIT - DarekDGB",
            "MIT \u2014 DarekDGB",
            "MIT License (c) DarekDGB",
        }
    )
    for path in V49E_CHANGED_PATHS:
        text = _read(path)
        lowered_text = text.lower()
        for alternate in (
            "anth" + "ropic",
            "chat" + "gpt",
            "clau" + "de",
            "open" + "ai",
        ):
            assert alternate not in lowered_text, path.relative_to(ROOT)
        for line in text.splitlines():
            normalized = line.strip().replace("**", "")
            lowered = normalized.lower()
            if lowered.startswith(
                ("author:", "author attribution:", "owner attribution:", "copyright")
            ):
                assert normalized in allowed_attribution_lines, path.relative_to(ROOT)
            if lowered.startswith(("mit -", "mit \u2014", "mit license (c)")):
                assert normalized in allowed_attribution_lines, path.relative_to(ROOT)

    assert "Author attribution: **DarekDGB**" in _read(COMPATIBILITY_DOC)
    project = tomllib.loads(_read(ROOT / "pyproject.toml"))["project"]
    assert project["authors"] == [{"name": "DarekDGB"}]
