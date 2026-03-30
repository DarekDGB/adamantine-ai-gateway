# Adapter Manifest V1

## Contract ID
`adapter_manifest_v1`

## Purpose

Adapter Manifest V1 defines the deterministic declaration required for every adapter registered in the Adamantine AI Gateway.

This contract ensures adapters are explicit, inspectable, and bounded components — not just executable code.

The manifest declares:
- what the adapter accepts
- what it may output
- what failure space it operates in

The manifest is declarative only.

It does not:
- execute logic
- assign trust
- override gateway validation or fail-closed behavior

---

## Status
Active for `v0.3.0`

---

## Required Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| manifest_version | str | Yes | Must equal adapter_manifest_v1 |
| adapter_id | str | Yes | Stable adapter identifier |
| adapter_version | str | Yes | Adapter version |
| entrypoint | str | Yes | Python import path |
| accepted_input_types | list[str] | Yes | Allowed input categories |
| supported_actions | list[str] | Yes | Explicit allowed actions |
| required_payload_fields | list[str] | Yes | Required payload fields |
| optional_payload_fields | list[str] | Yes | Optional payload fields |
| output_contract | str | Yes | Must be ai_gateway_output_v1 |
| determinism_constraints | list[str] | Yes | Determinism guarantees |
| failure_reason_ids | list[str] | Yes | Allowed failure reasons |
| notes | str | Yes | Bounded description |

---

## Invariants

- Manifest must be a dictionary
- manifest_version must equal adapter_manifest_v1
- All required fields must exist
- adapter_id must be stable and explicit
- supported_actions must be explicit
- undeclared actions are rejected
- failure_reason_ids must be bounded
- no hidden behavior allowed
- must be canonicalizable JSON
- must not weaken fail-closed guarantees

---

## Determinism Constraints (Examples)

- same_input_same_envelope
- same_envelope_same_output
- canonical_json_only
- no_time_dependency
- no_randomness
- no_network_calls

---

## Example — PoI Adapter

```json
{
  "manifest_version": "adapter_manifest_v1",
  "adapter_id": "poi",
  "adapter_version": "0.3.0",
  "entrypoint": "ai_gateway.adapters.poi.PoIAdapter",
  "accepted_input_types": ["poi_candidate"],
  "supported_actions": ["evaluate_candidate"],
  "required_payload_fields": ["task_type", "model_family", "input_payload"],
  "optional_payload_fields": [],
  "output_contract": "ai_gateway_output_v1",
  "determinism_constraints": [
    "same_input_same_envelope",
    "same_envelope_same_output",
    "canonical_json_only",
    "no_time_dependency",
    "no_randomness",
    "no_network_calls"
  ],
  "failure_reason_ids": [
    "UNSUPPORTED_TASK",
    "INVALID_ENVELOPE",
    "SCHEMA_VIOLATION",
    "POLICY_DENIED"
  ],
  "notes": "PoI adapter boundary"
}
```

---

# AI Gateway Receipt V1

## Contract ID
`ai_gateway_receipt_v1`

---

## Purpose

Defines the deterministic receipt emitted by the gateway after processing.

This receipt:
- provides evidence
- enables downstream verification
- does NOT grant final authority

AdamantineOS remains the final decision layer.

---

## Required Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| receipt_version | str | Yes | Must equal ai_gateway_receipt_v1 |
| gateway_version | str | Yes | Gateway version |
| adapter_id | str | Yes | Adapter used |
| adapter_version | str | Yes | From manifest |
| envelope_hash | str | Yes | SHA-256 |
| output_hash | str | Yes | SHA-256 |
| policy_decision | str | Yes | accepted/rejected |
| reason_id | str | Yes | Explicit reason |
| created_from_contract | str | Yes | ai_gateway_output_v1 |
| determinism_profile | str | Yes | Determinism profile |

---

## Invariants

- deterministic
- no timestamps
- no randomness
- canonical JSON only
- hashes must be stable
- reason_id must be preserved exactly

---

## Example — Accepted

```json
{
  "receipt_version": "ai_gateway_receipt_v1",
  "gateway_version": "0.3.0",
  "adapter_id": "poi",
  "adapter_version": "0.3.0",
  "envelope_hash": "aaa...",
  "output_hash": "bbb...",
  "policy_decision": "accepted",
  "reason_id": "ACCEPTED",
  "created_from_contract": "ai_gateway_output_v1",
  "determinism_profile": "canonical_sha256_no_time_v1"
}
```

---

## Example — Rejected

```json
{
  "receipt_version": "ai_gateway_receipt_v1",
  "gateway_version": "0.3.0",
  "adapter_id": "wallet",
  "adapter_version": "0.3.0",
  "envelope_hash": "ccc...",
  "output_hash": "ddd...",
  "policy_decision": "rejected",
  "reason_id": "ADAPTER_VALIDATION_FAILED",
  "created_from_contract": "ai_gateway_output_v1",
  "determinism_profile": "canonical_sha256_no_time_v1"
}
```

---

## Determinism Rules

For identical inputs:
→ identical envelope_hash  
→ identical output_hash  
→ identical receipt  

---

## Summary

This step upgrades the gateway from:
“code that processes adapters”

to:

“contract-driven system with declared adapter boundaries and deterministic receipts”
