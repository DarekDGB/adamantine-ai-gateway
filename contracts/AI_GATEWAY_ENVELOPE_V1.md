# AI Gateway Envelope V1

## Contract ID

`ai_gateway_envelope_v1`

## Purpose

AI Gateway Envelope V1 defines the minimum deterministic input shape that an adapter must produce before downstream validation and policy evaluation.

This contract exists to ensure that source-specific AI-originated input is translated into a bounded, structured, inspectable form.

The envelope is an input contract only. It does not imply trust, acceptance, or downstream authorization.

## Status

Active for `v0.1.0`.

## Required Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `contract_version` | `str` | Yes | Must equal `ai_gateway_envelope_v1` |
| `adapter` | `str` | Yes | Name of the adapter that translated the source input |
| `task_type` | `str` | Yes | Declared task category |
| `model_family` | `str` | Yes | Declared model family or deterministic model identifier |
| `input_payload` | `dict` | Yes | Structured bounded payload for downstream handling |

## Invariants

- Envelope must be a dictionary
- `contract_version` must exactly match `ai_gateway_envelope_v1`
- All required fields must exist
- Envelope does not grant trust
- Envelope must be suitable for canonical serialization
- Raw unbounded AI output must not bypass this contract
- Adapters may translate input, but may not assign trust

## Example

```json
{
  "contract_version": "ai_gateway_envelope_v1",
  "adapter": "poi",
  "task_type": "code_review",
  "model_family": "poi-v1",
  "input_payload": {
    "candidate_id": "abc123"
  }
}
```

## Validation Rules for v0.1.0

Validation currently enforces:

1. Envelope value must be a dictionary
2. `contract_version` must equal `ai_gateway_envelope_v1`
3. All required fields must be present

Additional semantic validation may be added in later versions, but must not silently weaken existing rules.

## Fail-Closed Notes

Any invalid envelope must be rejected by validation or mapped into an explicit fail-closed output path by the gateway.

No invalid envelope may silently proceed.

## Non-Goals

This contract does not define:

- final acceptance
- consensus eligibility
- remote model execution
- cryptographic identity binding
- downstream AdamantineOS decisioning

Those are outside the scope of Envelope V1.
