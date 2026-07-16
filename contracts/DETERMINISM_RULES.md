# Determinism Rules V1

Author attribution: **DarekDGB**

## Purpose

This document defines the deterministic behavior required by the frozen
Adamantine AI Gateway V1 boundary at package version `1.0.0`.

Determinism is required so that identical structured inputs always produce identical canonical bytes, identical hashes, and identical contract-bound outputs.

This document exists to prevent ambiguity, output drift, hidden state, and non-reproducible behavior at the gateway boundary.

## Core Principle

Same structured input  
-> same canonical representation  
-> same hash  
-> same contract outcome

If this cannot be guaranteed, the system must fail closed.

## Scope

These rules apply to:

- canonical serialization
- hashing
- envelope construction
- output construction
- adapter behavior
- gateway fail-closed handling

They do not define deterministic AI inference. That remains outside the
Gateway boundary.

## Canonical Serialization Rules

Canonical serialization is the named profile
`ai_gateway_canonical_json_v1`, normatively defined in
`AI_GATEWAY_CANONICAL_JSON_V1.md`.

The profile freezes:

- the supported JSON byte value model and D2 exact-host-type rules;
- UTF-8 output and a closed string-escaping algorithm;
- lowercase `\u00xx` escapes for non-short-form controls;
- raw solidus, U+007F, C1, BMP, and astral scalars;
- no Unicode normalization;
- Unicode scalar-value object-key ordering;
- array-order preservation;
- minimal base-10 integer output and float rejection;
- strict duplicate-key rejection at raw-wire boundaries;
- D2 Unicode scalar-value and canonical-byte resource limits; and
- no BOM, whitespace, or trailing newline in canonical output.

The normative profile is the source of truth. Literal bytes, the independent
checker, and differential tests are conformance evidence. Any disagreement is
a failure; production serializer parity alone is not sufficient evidence.

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

Hashing for this profile is defined as:

- SHA-256
- over canonical JSON bytes only
- lowercase hexadecimal digest output

No per-artifact byte prefix exists in this V1 profile. Adding one would change
existing hashes and requires a new versioned contract.

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

The following are forbidden in V1 boundary processing:

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

- literal canonical bytes and SHA-256 vectors
- canonical Unicode scalar-value key ordering
- string escaping, Unicode, and no-normalization behavior
- strict duplicate-key and float rejection at raw-wire boundaries
- expected-equivalence and injective byte pairs
- exact D2 integer, scalar-count, node, depth, collection, and byte boundaries
- seeded differential byte fuzzing against an independent encoder
- stable hash output for equivalent structured values
- stable contract constants
- stable fail-closed behavior
- stable adapter output for identical input

Any minimized differential mismatch must be added to the permanent literal
fixture before closure.

## Future Hook Points

Later versions may extend these rules to include:

- deterministic inference verification
- reproducibility attestations
- zero-knowledge proof hooks
- model/version pinning
- stronger payload schema constraints
- a separately proven Rust implementation

Any extension must preserve the fail-closed core.

No Rust or SDK conformance claim exists until a Rust strict parser and encoder
pass the shared literal vectors and Python-to-Rust byte differential fuzzing.

## Summary

Determinism is not an optimization.

It is a trust boundary requirement.

If identical structured inputs cannot produce identical bounded outputs, the gateway must reject rather than guess.
