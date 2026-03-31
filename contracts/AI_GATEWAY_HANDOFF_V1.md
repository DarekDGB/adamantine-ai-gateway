# AI_GATEWAY_HANDOFF_V1

## Purpose

`AI_GATEWAY_HANDOFF_V1` defines the deterministic downstream handoff object emitted from Adamantine AI Gateway governed processing.

It is the sealed transition point between:
- validated gateway input
- enforced policy outcome
- adapter-produced output
- receipt-linked gateway evidence

This contract is intended for downstream consumers such as:
- Q-ID
- Shield v3
- Adaptive Core
- AdamantineOS

It does not make the final system decision.
It carries the gateway decision boundary forward in a strict, verifiable form.

---

## Contract ID

`ai_gateway_handoff_v1`

---

## Required Fields

- `handoff_version`
- `adapter`
- `task_type`
- `policy_decision`
- `reason_id`
- `envelope_hash`
- `output_hash`
- `context_hash`

No unknown fields are allowed.

---

## Field Definitions

### `handoff_version`
String. Must equal `ai_gateway_handoff_v1`.

### `adapter`
String. Adapter identifier that produced the gateway output.

Example:
`poi`

### `task_type`
String. The gateway task type associated with the processed request.

Example:
`code_review`

### `policy_decision`
String.

Allowed values:
- `accepted`
- `rejected`

This value must be derived from the validated gateway output and must match the validated receipt.

### `reason_id`
String. Explicit reason identifier copied from validated gateway output.

Examples:
- `ACCEPTED`
- `POLICY_DENIED`
- `UNSUPPORTED_TASK`
- `UNSUPPORTED_MODEL`

### `envelope_hash`
String. Lowercase SHA-256 hash of canonical validated envelope.

Must be exactly 64 lowercase hex characters.

### `output_hash`
String. Lowercase SHA-256 hash of canonical validated output.

Must be exactly 64 lowercase hex characters.

### `context_hash`
String. Context linkage value copied from validated output.

This may be an empty string if no context hash is available.

---

## Determinism Rules

- Canonical JSON only
- No unknown fields
- No floats
- Hashes must be SHA-256 over canonical validated artifacts
- `policy_decision` must be derived deterministically from validated output
- Receipt linkage must match:
  - `envelope_hash`
  - `output_hash`
  - `policy_decision`

If any linkage check fails, construction must fail closed.

---

## Validation Expectations

Validation must reject:
- wrong `handoff_version`
- unknown top-level fields
- missing required fields
- empty required strings except `context_hash`
- invalid `policy_decision`
- invalid hash shape
- non-canonical values

Builder logic must reject:
- envelope hash mismatch vs receipt
- output hash mismatch vs receipt
- policy decision mismatch vs receipt

All failures must be treated as fail-closed.

---

## Non-Goals

`AI_GATEWAY_HANDOFF_V1` does not:
- replace the gateway receipt
- replace adapter manifests
- grant execution authority
- make final AdamantineOS decisions
- introduce time, randomness, or network dependency
