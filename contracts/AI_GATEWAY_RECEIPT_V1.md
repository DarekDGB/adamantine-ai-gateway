# AI Gateway Receipt V1

## Contract ID
`ai_gateway_receipt_v1`

---

## Purpose

AI Gateway Receipt V1 defines the deterministic evidence artifact emitted by the Adamantine AI Gateway after processing.

This receipt exists to:
- provide verifiable evidence of gateway processing
- allow downstream systems to validate behavior deterministically
- preserve the exact outcome without relying on internal adapter logic

The receipt is **evidence only**.

It does NOT:
- grant execution authority
- override downstream systems
- replace AdamantineOS decision layer

AdamantineOS remains the final ALLOW / DENY authority.

---

## Status
Active for `v0.3.0`

---

## Required Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| receipt_version | str | Yes | Must equal `ai_gateway_receipt_v1` |
| gateway_version | str | Yes | Gateway version |
| adapter_id | str | Yes | Adapter used |
| adapter_version | str | Yes | From manifest |
| envelope_hash | str | Yes | SHA-256 of canonical envelope |
| output_hash | str | Yes | SHA-256 of canonical output |
| policy_decision | str | Yes | `accepted` or `rejected` |
| reason_id | str | Yes | Explicit reason |
| created_from_contract | str | Yes | Must be `ai_gateway_output_v1` |
| determinism_profile | str | Yes | Determinism profile identifier |

---

## Invariants

- Receipt must be a dictionary
- receipt_version must equal `ai_gateway_receipt_v1`
- All required fields must exist
- Receipt must be canonicalizable JSON
- No timestamps allowed
- No randomness allowed
- Hashes must be deterministic
- reason_id must be preserved exactly
- policy_decision must be explicit
- No hidden metadata allowed

---

## Field Semantics

### receipt_version
Fixed identifier for this contract.

### gateway_version
Version of the gateway that generated the receipt.

### adapter_id
Must match the registered adapter identity.

### adapter_version
Must come from the adapter manifest.

### envelope_hash
SHA-256 hash of canonical serialized envelope.

### output_hash
SHA-256 hash of canonical serialized output.

### policy_decision
High-level outcome classification:
- `accepted`
- `rejected`

### reason_id
Exact reason returned by gateway processing.
Must NOT be modified or remapped.

### created_from_contract
For v0.3.0:
`ai_gateway_output_v1`

### determinism_profile
Suggested value:
`canonical_sha256_no_time_v1`

---

## Validation Rules (STRICT)

1. Receipt must be a dictionary
2. receipt_version must equal `ai_gateway_receipt_v1`
3. All required fields must exist
4. All string fields must be non-empty
5. policy_decision â {accepted, rejected}
6. reason_id must be explicit and unchanged
7. envelope_hash must be 64-character lowercase hex
8. output_hash must be 64-character lowercase hex
9. created_from_contract must be supported
10. Unknown fields must be rejected

---

## Determinism Rules

For identical input and identical adapter state:

â identical envelope_hash  
â identical output_hash  
â identical receipt  

The receipt must be generated using:
- canonical JSON serialization
- SHA-256 hashing
- fixed field set
- no external inputs

---

## Example â Accepted

```json
{
  "receipt_version": "ai_gateway_receipt_v1",
  "gateway_version": "0.3.0",
  "adapter_id": "poi",
  "adapter_version": "0.3.0",
  "envelope_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "output_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "policy_decision": "accepted",
  "reason_id": "ACCEPTED",
  "created_from_contract": "ai_gateway_output_v1",
  "determinism_profile": "canonical_sha256_no_time_v1"
}
```

---

## Example â Rejected

```json
{
  "receipt_version": "ai_gateway_receipt_v1",
  "gateway_version": "0.3.0",
  "adapter_id": "wallet",
  "adapter_version": "0.3.0",
  "envelope_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "output_hash": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "policy_decision": "rejected",
  "reason_id": "ADAPTER_VALIDATION_FAILED",
  "created_from_contract": "ai_gateway_output_v1",
  "determinism_profile": "canonical_sha256_no_time_v1"
}
```

---

## Fail-Closed Behavior

If receipt generation fails:

â Gateway MUST fail closed  
â reason_id = `INTERNAL_ERROR`  
â No partial receipt allowed  

---

## Non-Goals

This contract does NOT define:
- final execution decisions
- identity verification (Q-ID)
- Shield v3 evidence structure
- Adaptive Core governance
- AdamantineOS execution boundary

---

## Summary

AI Gateway Receipt V1 provides:

- deterministic evidence output
- verifiable processing trace
- strict, bounded structure
- compatibility with downstream systems

It transforms the gateway into:

**a deterministic evidence-emitting boundary, not just a processing layer**
