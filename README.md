# Adamantine AI Gateway

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/DarekDGB/adamantine-ai-gateway)
[![CI](https://github.com/DarekDGB/adamantine-ai-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/DarekDGB/adamantine-ai-gateway/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/DarekDGB/adamantine-ai-gateway)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Fail-closed, contract-first gateway for untrusted AI-originated work.

---

## Overview

Adamantine AI Gateway is a deterministic policy-enforcement and evidence-production boundary that converts untrusted AI outputs into structured, validated, policy-controlled evidence.

It sits between variable external AI systems and the stricter Adamantine stack.

The existing `v1.0.0` tag and the current working tree are different snapshots.
Package/runtime metadata remains `1.0.0`; the V4.9 compatibility extensions
below and V4.10-G3 release-truth work remain unreleased. This source must not
be published as a replacement for the existing tag.

---

## System Diagram

```text
External AI
    v
Adapter
    v
Adamantine AI Gateway
    |-- validate contract boundary
    |-- enforce manifest/runtime alignment
    |-- enforce policy
    |-- produce deterministic output
    |-- produce deterministic receipt
    |-- produce deterministic handoff
    `-- optionally produce a versioned policy binding
    v
Versioned evidence exporter
    v
Independent downstream verifier and final policy boundary
```

---

## v1.0.0 Highlights

- Public API freeze locked
- Version truth locked across runtime, package metadata, and release files
- Artifact-chain invariants locked
- Stable reason-ID mapping locked
- Manifest `failure_reason_ids` completeness locked
- Built-in adapter manifest/runtime parity locked
- Governed manifest enforcement locked
- Receipt-path manifest/runtime enforcement parity locked
- Deterministic fallback artifacts locked
- Release-truth / doc-contract parity locked
- 100% test coverage enforced

---

## Unreleased V4.9-D2 Compatibility Extension

V4.9-D2 adds a separate, versioned producer path without changing the frozen
V1 artifacts, the root package exports, or package version `1.0.0`:

- `AI_GATEWAY_POLICY_BINDING_V1` binds one immutable validated PolicyPack V1
  snapshot to the exact receipt and handoff from the same governed operation.
- `process_governed_with_policy_binding_v1(...)` captures the policy before any
  registry or adapter callback and uses the captured snapshot for enforcement.
- `ADAMANTINE_AI_GATEWAY_EVIDENCE_V2` packages handoff, receipt, and policy
  binding as `evidence_only`.
- the V1 from-result helper rejects a present `policy_binding` key and directs
  the caller to V2.
- malformed, pre-policy, backend, chain, or binding failures return no partial
  receipt, handoff, or policy binding.

This is not a release tag or version bump. The independent AdamantineOS
expected-policy consumer is implemented and separately verified by V4.9-D3B.
Shield compatibility is not claimed by this D2 producer step alone.

---

## Unreleased V4.9-D3A Canonical-Profile Gate

V4.9-D3A names and freezes the byte profile already used by current Gateway
hashes as `ai_gateway_canonical_json_v1`:

- a closed language-neutral contract defines exact bytes and D2 governed limits;
- literal golden bytes and hashes are checked in as data;
- a standalone encoder and strict duplicate-key parser import no Gateway code;
- accepted, rejected, equivalence, injectivity, and exact-boundary vectors are
  locked;
- seeded differential fuzzing compares production and independent bytes before
  hashes; and
- existing artifact fields, hashes, public API, and package version remain
  unchanged.

This gate proves independent Python parity only. It makes no Rust or SDK compatibility claim.
The separately implemented V4.9-D3B AdamantineOS consumer independently uses
the same frozen bytes and verifier-controlled expected-policy values.

---

## Unreleased V4.9-E Shield v4 Compatibility Boundary

V4.9-E freezes AI Gateway as a Gateway-local evidence source, not a Shield
cryptographic verifier:

- Gateway does not verify Shield signatures and has no Shield trust registry,
  Shield key role, or OQS dependency.
- Gateway-local `accepted` and `policy_decision` values are evidence only. They
  are not AdamantineOS approval or execution authority.
- frozen output, receipt, handoff, and evidence objects keep exact closed
  top-level shapes; unknown Shield-like or authority-like fields cannot extend
  those contracts.
- adapter `output_payload` data is not interpreted as Shield evidence or
  authority and is not exported by the V2 evidence bundle.
- Shield v4 keeps `classical-ed25519 + ml-dsa` required and draft
  FN-DSA/Falcon-1024 evidence optional; Gateway neither verifies nor changes
  that policy.
- AdamantineOS remains the independent final fail-closed policy and execution
  boundary, and every Gateway evidence path remains non-authoritative.

See `docs/reports/v4/SHIELD_V4_COMPATIBILITY.md` for the normative compatibility
boundary and its regression evidence.

---

## What v1.0.0 Means

This section describes the historical release boundary, not a claim that later
working-tree additions were included in the existing tag.

v1.0.0 is the first fully locked release of Adamantine AI Gateway as a deterministic policy-enforcement and evidence-production boundary for untrusted AI-originated work.

This release freezes the gateway around these guarantees:

- Fail-closed behavior
- Contract-first validation
- Deterministic artifact generation
- Explicit manifest-declared adapter boundaries
- Explicit policy enforcement
- Stable reason-ID semantics
- Release truth aligned with implementation

This is no longer just a safe prototype boundary.

It is now a **locked release surface** for downstream integration.

---

## Core Flow

```text
External AI
-> Adapter
-> AI Gateway
-> Output
-> Receipt
-> Handoff
-> Optional policy binding
-> Versioned evidence exporter
-> Independent downstream verification
```

---

## Runtime Paths

### `process`
Base deterministic processing path.

### `process_with_policy`
Adds policy enforcement before acceptance.

### `process_with_receipt`
Adds deterministic evidence generation.

### `process_governed`
Produces the frozen V1 output + receipt + handoff result. This V1 path is
policy-identity unbound.

### `process_governed_with_policy_binding_v1`
Produces output + receipt + handoff + `AI_GATEWAY_POLICY_BINDING_V1`. A genuine
policy denial may produce a complete rejected bound chain over the actual
evaluated envelope. If policy evaluation was not reached, or if artifact
construction fails, the three evidence fields are `None`.

### Adamantine evidence exporters

- V1 exports unbound handoff and receipt evidence.
- V2 exports handoff, receipt, and policy binding evidence.
- the V1 from-result exporter rejects any result containing `policy_binding`.

---

## Security Model

- All AI-originated work is treated as untrusted input
- All accepted artifacts must match strict contract shape
- All governed flows require manifest/runtime alignment
- Missing, invalid, or undeclared actions fail before policy-bound evidence
- All decisions must remain deterministic
- All failures must remain fail-closed
- All important rejection paths must emit explicit reason IDs
- No silent fallback is allowed
- Policy-bound evidence must use one pre-callback immutable policy snapshot
- Bound artifacts must pass full envelope/output/receipt/handoff linkage checks
- Output and handoff context hashes must equal the canonical envelope hash
- Receipt hash profile is fixed to `canonical_sha256_no_time_v1`
- D2/V2 policy-bound hash bytes are fixed to `ai_gateway_canonical_json_v1`
- Raw-wire consumers must reject duplicate decoded object keys
- The V1 from-result helper cannot detect a binding removed before the call;
  downstream exact-policy consumers must require V2 and prohibit V1 fallback

No governed path is allowed without:

- Valid contract
- Valid manifest
- Valid policy scope
- Deterministic-safe structure

---

## Contracts

Current contract surface:

- `AI_GATEWAY_ENVELOPE_V1`
- `ADAPTER_MANIFEST_V1`
- `AI_GATEWAY_OUTPUT_V1`
- `AI_GATEWAY_RECEIPT_V1`
- `AI_GATEWAY_HANDOFF_V1`
- `POLICYPACK_V1`
- `AI_GATEWAY_CANONICAL_JSON_V1`
- `AI_GATEWAY_POLICY_BINDING_V1`
- `ADAMANTINE_AI_GATEWAY_EVIDENCE_V2`

See `contracts/` for the formal repo contract documents.

---

## Principles

- Fail-closed always
- Contract-first
- Deterministic processing only
- No unknown fields
- Canonical-safe payloads
- Explicit reason IDs
- No hidden authority
- No silent fallbacks
- Adapters translate; Gateway validates its own contracts and enforces its own policy
- Evidence does not grant approval, signing, broadcast, or execution authority
- AdamantineOS remains the independent final policy and execution boundary

---

## Release Status

The existing `v1.0.0` tag points to commit
`597db130a67ea366b052afac4e2b822ef3c03a7d`. The authenticated pre-G3 working
tree is `42d8866dde3eee01552cc68d59b371d959c2c8e1`, 65 commits ahead of that
tag. V4.10-G3 is documentation and regression-test work only: no package or
runtime version bump, release publication, tag creation, or tag movement.

V4.9-D2, V4.9-D3A, and V4.9-E are
unreleased, V1-shape-preserving compatibility extensions. D3A freezes the
existing D2/V2 hash bytes without changing them. The separate V4.9-D3B
AdamantineOS consumer is verified, but Gateway evidence still provides
deterministic content linkage only;
it does not authenticate the producer, provide freshness or replay protection,
prove honest execution, claim Rust compatibility, or grant final authority.

Frozen V1 evidence remains policy-identity unbound. The separately versioned
`AI_GATEWAY_POLICY_BINDING_V1` is carried by evidence V2, not inserted into
V1. V1 shape preservation is not a claim that all V1 exporter inputs are
unchanged: the from-result helper requires an exact bounded built-in dictionary
and rejects a present `policy_binding` key. An exact-policy consumer must
require V2 with no V1 fallback.

The next independent distribution release number remains unassigned. Gateway
does not inherit Shield's `4.0.0` version. A later release needs explicit review
of exporter input hardening and receipt-version-dependent hashes; retaining
`1.0.0` here does not authorize republishing the changed tree as that release.

See [V4.10-G3 release status](docs/RELEASE_STATUS_V4_10_G3.md) for the version
map, frozen-fixture identities, validation evidence, and post-commit gate.

## Validation Status

| Snapshot | Tests | Coverage |
|---|---|---|
| Pre-G3 source at `42d8866d...` | 413 passed; zero skips | 1117/1117 statements and 394/394 branches; 100% |
| G3 candidate, including six new release-truth tests | 419 passed; zero skips | 1117/1117 statements and 394/394 branches; 100% |

These are CPython 3.11.15 local results. CI uses the Python `3.11` line and
enforces 100% statement and branch coverage. Candidate results are not evidence
that a later GitHub commit passed: require `CI` green on the exact final G3
commit and verify a fresh post-commit ZIP before closing G3.

The standalone canonical-vector checker also passes; it is independent Python
byte-parity evidence, not Rust, SDK, Shield signature, or live-OQS proof.
Gateway has no dedicated native-OQS workflow and none is required for G3.

---

MIT License (c) DarekDGB
