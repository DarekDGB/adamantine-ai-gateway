from pathlib import Path

from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.contracts.handoff_v1 import ALLOWED_HANDOFF_FIELDS, REQUIRED_HANDOFF_FIELDS
from ai_gateway.contracts.output_v1 import REQUIRED_OUTPUT_FIELDS
from ai_gateway.contracts.receipt_v1 import ALLOWED_RECEIPT_FIELDS, REQUIRED_RECEIPT_FIELDS
from ai_gateway.gateway import AIGateway
from ai_gateway.hashing import sha256_hex
from ai_gateway.registry import AdapterRegistry
from ai_gateway.validation import validate_policypack_v1


ROOT = Path(__file__).parents[1]
POLICY_CONTRACT = ROOT / "contracts" / "POLICYPACK_V1.md"
INVARIANTS = ROOT / "docs" / "adamantine_ai_gateway_v1_0_0_INVARIANTS_LOCK.md"
DECISION = ROOT / "docs" / "reports" / "v4" / "POLICY_PACK_IDENTITY_DECISION.md"

POLICY_IDENTITY_FIELDS = {
    "policypack_id",
    "policypack_version_id",
    "policypack_hash",
    "policy_pack_id",
    "policy_pack_version_id",
    "policy_pack_hash",
    "policy_reference",
}

EXPECTED_OUTPUT_FIELDS = (
    "contract_version",
    "adapter",
    "task_type",
    "accepted",
    "reason_id",
    "output_payload",
    "context_hash",
)
EXPECTED_RECEIPT_FIELDS = (
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
EXPECTED_HANDOFF_FIELDS = (
    "handoff_version",
    "adapter",
    "task_type",
    "policy_decision",
    "reason_id",
    "envelope_hash",
    "output_hash",
    "context_hash",
)

SOURCE_INPUT = {
    "task_type": "code_review",
    "model_family": "poi-v1",
    "input_payload": {
        "action": "evaluate_candidate",
        "prompt": "review this",
    },
}

MANIFEST = {
    "manifest_version": "adapter_manifest_v1",
    "adapter_id": "poi",
    "adapter_version": "1.0.0",
    "entrypoint": "ai_gateway.adapters.poi.PoIAdapter",
    "accepted_input_types": ["poi_candidate"],
    "supported_actions": ["evaluate_candidate"],
    "required_payload_fields": ["task_type", "model_family", "input_payload"],
    "optional_payload_fields": [],
    "output_contract": "ai_gateway_output_v1",
    "determinism_constraints": ["canonical_json_only"],
    "failure_reason_ids": [
        "ACCEPTED",
        "UNSUPPORTED_TASK",
        "UNSUPPORTED_MODEL",
        "POLICY_DENIED",
        "SCHEMA_VIOLATION",
        "INVALID_ENVELOPE",
        "INVALID_OUTPUT",
        "ADAPTER_VALIDATION_FAILED",
        "INTERNAL_ERROR",
    ],
    "notes": "V4.9-D policy identity decision lock",
}


def _policy_pack(
    *,
    policy_id: str,
    version_id: str,
    extra_task_type: str,
    notes: str,
) -> dict:
    return {
        "policypack_version": "policy_pack_v1",
        "policypack_id": policy_id,
        "policypack_version_id": version_id,
        "default_decision": "deny",
        "adapter_policies": {
            "poi": {
                "allowed_task_types": ["code_review", extra_task_type],
                "allowed_model_families": ["poi-v1"],
                "allowed_actions": ["evaluate_candidate"],
            }
        },
        "notes": notes,
    }


def _gateway() -> AIGateway:
    registry = AdapterRegistry()
    registry.register("poi", PoIAdapter(), manifest=MANIFEST)
    return AIGateway(registry)


def test_frozen_v1_artifact_shapes_have_no_policy_identity_fields() -> None:
    locked_shapes = (
        (REQUIRED_OUTPUT_FIELDS, EXPECTED_OUTPUT_FIELDS),
        (REQUIRED_RECEIPT_FIELDS, EXPECTED_RECEIPT_FIELDS),
        (REQUIRED_HANDOFF_FIELDS, EXPECTED_HANDOFF_FIELDS),
    )
    for fields, expected in locked_shapes:
        assert fields == expected
        assert POLICY_IDENTITY_FIELDS.isdisjoint(fields)

    assert ALLOWED_RECEIPT_FIELDS == frozenset(EXPECTED_RECEIPT_FIELDS)
    assert ALLOWED_HANDOFF_FIELDS == frozenset(EXPECTED_HANDOFF_FIELDS)
    assert POLICY_IDENTITY_FIELDS.isdisjoint(ALLOWED_RECEIPT_FIELDS)
    assert POLICY_IDENTITY_FIELDS.isdisjoint(ALLOWED_HANDOFF_FIELDS)


def test_distinct_permitting_policy_packs_produce_identical_unbound_v1_artifacts() -> None:
    policy_a = _policy_pack(
        policy_id="policy-a",
        version_id="v1",
        extra_task_type="documentation",
        notes="strict review profile",
    )
    policy_b = _policy_pack(
        policy_id="policy-b",
        version_id="v999",
        extra_task_type="test_generation",
        notes="broader unrelated profile",
    )

    validated_a = validate_policypack_v1(policy_a)
    validated_b = validate_policypack_v1(policy_b)
    assert sha256_hex(validated_a) != sha256_hex(validated_b)

    gateway = _gateway()
    result_a = gateway.process_governed("poi", SOURCE_INPUT, policy_a)
    result_b = gateway.process_governed("poi", SOURCE_INPUT, policy_b)

    assert result_a["output"]["accepted"] is True
    assert result_b["output"]["accepted"] is True
    assert result_a["output"] == result_b["output"]
    assert result_a["receipt"] == result_b["receipt"]
    assert result_a["handoff"] == result_b["handoff"]


def test_decision_documents_lock_path_two_without_reinterpreting_v1() -> None:
    policy_contract = POLICY_CONTRACT.read_text()
    invariants = INVARIANTS.read_text()
    decision = DECISION.read_text()

    assert "V1 artifacts remain deterministic evidence, but they are policy-identity\nunbound." in policy_contract
    assert "manifest -> envelope -> output -> receipt -> handoff -> policy reference" not in invariants
    assert "new versioned policy-binding artifact" in invariants
    assert (
        "**Current repo state reviewed:** `v1.0.0` plus the fresh V4.9-D3A producer and\n"
        "V4.9-E compatibility source"
    ) in invariants
    assert "**Current repo state reviewed:** `v0.5.0`" not in invariants
    assert "Decision: new versioned policy binding required" in decision
    assert "No V1 field is added, removed, or reinterpreted" in decision
    assert "cannot independently\nrecompute those two hashes" in decision
    assert "AIGateway.process_governed_with_policy_binding_v1" in decision
    assert "deterministic binding provides content linkage" in decision
    assert "V4.9-D3B complete: independently verified AdamantineOS" in decision
    assert "V4.9-E   implemented here: Gateway Shield v4 compatibility" in decision
    assert "V4.9-D3  pending" not in decision


def test_decision_locks_adamantineos_as_non_final_independent_consumer() -> None:
    decision = DECISION.read_text()

    required_statements = (
        "`final_approval` remains false",
        "must not fall back automatically to unbound V1 evidence",
        "verifier-controlled trusted local configuration",
        "binding cannot bypass independent replay controls",
        "cannot grant execution authority",
        "Q-ID identity keys and Shield decision-evidence keys remain separate",
    )
    for statement in required_statements:
        assert statement in decision
