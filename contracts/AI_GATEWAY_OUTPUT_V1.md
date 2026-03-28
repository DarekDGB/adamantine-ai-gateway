# AI Gateway Output V1

## Contract ID

`ai_gateway_output_v1`

## Purpose

AI Gateway Output V1 defines the deterministic output shape emitted by an adapter or the gateway after validation and policy handling.

This contract exists to make every outcome explicit, inspectable, and fail-closed.

## Status

Active for `v0.1.0`.

## Required Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `contract_version` | `str` | Yes | Must equal `ai_gateway_output_v1` |
| `adapter` | `str` | Yes | Adapter name |
| `task_type` | `str` | Yes | Declared task category |
| `accepted` | `bool` | Yes | Explicit outcome flag |
| `reason_id` | `str` | Yes | Deterministic outcome reason |
| `output_payload` | `dict` | Yes | Structured bounded result payload |
| `context_hash` | `str` | Yes | Deterministic hash anchor for the evaluated context |

## Invariants

- Output must be a dictionary
- `contract_version` must exactly match `ai_gateway_output_v1`
- All required fields must exist
- `accepted` must always be boolean
- `reason_id` must always be explicit
- Output must be suitable for canonical serialization
- Failure must never be silent
- Rejection must produce bounded output, not partial success

## Reason Semantics for v0.1.0

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
- Shield v3 evidence format
- Adaptive Core governance outcomes
- AdamantineOS final ALLOW/DENY enforcement
