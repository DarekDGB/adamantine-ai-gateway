# AI Gateway Output V1

Author attribution: **DarekDGB**

## Contract ID

`ai_gateway_output_v1`

## Purpose

AI Gateway Output V1 defines the deterministic output shape emitted by an adapter or the gateway after validation and policy handling.

This contract exists to make every outcome explicit, inspectable, and fail-closed.

## Status

Active frozen V1 contract at package version `1.0.0`.

## Required Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `contract_version` | `str` | Yes | Must equal `ai_gateway_output_v1` |
| `adapter` | `str` | Yes | Adapter name |
| `task_type` | `str` | Yes | Declared task category |
| `accepted` | `bool` | Yes | Explicit Gateway-local outcome flag; never final approval |
| `reason_id` | `str` | Yes | Deterministic outcome reason |
| `output_payload` | `dict` | Yes | Structured bounded result payload |
| `context_hash` | `str` | Yes | Deterministic hash anchor for the evaluated context |

## Invariants

- Output must be a dictionary
- `contract_version` must exactly match `ai_gateway_output_v1`
- All required fields must exist
- No unknown top-level fields are allowed
- `accepted` must always be boolean
- `reason_id` must always be explicit
- Output must be suitable for canonical serialization
- Failure must never be silent
- Rejection must produce bounded output, not partial success

`accepted` describes only the Gateway's own contract and policy result. It is
not Shield signature verification, AdamantineOS approval, signing authority,
broadcast authority, or execution authority.

`output_payload` is bounded adapter data. Shield-like names inside that payload
remain untrusted data; the Gateway does not interpret them as Shield evidence,
keys, signatures, profiles, approval, or authority. The V2 Adamantine evidence
bundle validates the output linkage but does not export `output_payload`.

## Reason Semantics

Examples of explicit reasons include:

- `ACCEPTED`
- `UNSUPPORTED_TASK`
- `UNSUPPORTED_MODEL`
- `INVALID_ENVELOPE`
- `INVALID_OUTPUT`
- `MISSING_REQUIRED_FIELD`
- `SCHEMA_VIOLATION`
- `ADAPTER_NOT_REGISTERED`
- `INTERNAL_ERROR`

## Example Accepted Output

```json
{
  "contract_version": "ai_gateway_output_v1",
  "adapter": "poi",
  "task_type": "code_review",
  "accepted": true,
  "reason_id": "ACCEPTED",
  "output_payload": {
    "status": "accepted-candidate"
  },
  "context_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

## Example Rejected Output

```json
{
  "contract_version": "ai_gateway_output_v1",
  "adapter": "poi",
  "task_type": "unknown_task",
  "accepted": false,
  "reason_id": "UNSUPPORTED_TASK",
  "output_payload": {},
  "context_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

## Fail-Closed Notes

If processing fails, the gateway must emit a rejected output shape rather than throwing trust-bearing partial results downstream.

## Non-Goals

This contract does not define:

- final blockchain consensus acceptance
- miner rewards
- cryptographic proof formats
- Q-ID identity proof binding
- Shield v4 evidence verification, signature bundles, algorithms, profiles,
  key roles, or trust registries
- Adaptive Core governance outcomes
- AdamantineOS final ALLOW/DENY enforcement

Unknown Shield-like or authority-like top-level fields are schema violations;
they cannot extend this frozen contract.
