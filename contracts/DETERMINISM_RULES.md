# Determinism Rules V1

## Purpose

This document defines the deterministic behavior required by Adamantine AI Gateway v0.1.0.

Determinism is required so that identical structured inputs always produce identical canonical bytes, identical hashes, and identical contract-bound outputs.

This document exists to prevent ambiguity, output drift, hidden state, and non-reproducible behavior at the gateway boundary.

## Core Principle

Same structured input  
→ same canonical representation  
→ same hash  
→ same contract outcome

If this cannot be guaranteed, the system must fail closed.

## Scope

These rules apply to:

- canonical serialization
- hashing
- envelope construction
- output construction
- adapter behavior
- gateway fail-closed handling

They do not yet define full deterministic AI inference. That is outside v0.1.0 scope.

## Canonical Serialization Rules

Canonical serialization in v0.1.0 is defined as:

- JSON serialization
- UTF-8 encoding
- sorted object keys
- no extra whitespace
- stable separators `(",", ":")`
- no pretty-print formatting

The canonical serialization helper is the single source of truth for canonical bytes.

### Required Behavior

For identical structured values, canonical serialization MUST produce identical bytes.

### Example

Input A:

```json
{"b":2,"a":1}
```

Input B:

```json
{"a":1,"b":2}
```

Canonical output for both:

```json
{"a":1,"b":2}
```

Encoded as UTF-8 bytes.

## Hashing Rules

Hashing in v0.1.0 is defined as:

- SHA-256
- over canonical JSON bytes only
- lowercase hexadecimal digest output

The hashing helper is the single source of truth for deterministic context hashing.

### Required Behavior

For identical canonical bytes, hashing MUST produce identical digests.

Any alternate hashing path is forbidden.

## Envelope Determinism

For identical adapter input, envelope construction MUST produce:

- identical `contract_version`
- identical `adapter`
- identical `task_type`
- identical `model_family`
- identical `input_payload`

No hidden mutation, randomization, or time-based field may affect the envelope.

## Output Determinism

For identical validated envelope input, output construction MUST produce:

- identical `contract_version`
- identical `adapter`
- identical `task_type`
- identical `accepted`
- identical `reason_id`
- identical `output_payload`
- identical `context_hash`

No hidden mutation, randomization, clock access, or environment-dependent behavior may affect output.

## Forbidden Sources of Non-Determinism

The following are forbidden in v0.1.0 boundary processing:

- timestamps
- random values
- UUID generation
- unordered iteration assumptions
- environment-dependent output differences
- hidden global state
- external network calls
- remote inference calls
- silent coercion of invalid input

## Fail-Closed Requirement

If determinism cannot be preserved, processing must not continue as trusted output.

The gateway must fail closed with an explicit rejected output.

## Adapter Rules

Adapters must remain deterministic for identical inputs.

Adapters may:

- normalize structured input
- map source input into gateway contract fields

Adapters may not:

- inject hidden metadata
- fetch remote model results
- guess missing fields
- mutate validated values silently
- override policy outcome

## Gateway Rules

Gateway processing must remain deterministic for:

- adapter lookup
- validation handling
- reason mapping
- fail-closed output shape

Unexpected exceptions must map to explicit rejection, never silent acceptance.

## Testing Requirement

Deterministic behavior must be locked by tests.

At minimum, tests must verify:

- canonical key ordering
- stable hash output for equivalent structured values
- stable contract constants
- stable fail-closed behavior
- stable adapter output for identical input

## Future Hook Points

Later versions may extend these rules to include:

- deterministic inference verification
- reproducibility attestations
- zero-knowledge proof hooks
- model/version pinning
- stronger payload schema constraints

Any extension must preserve the fail-closed core.

## Summary

Determinism is not an optimization.

It is a trust boundary requirement.

If identical structured inputs cannot produce identical bounded outputs, the gateway must reject rather than guess.
