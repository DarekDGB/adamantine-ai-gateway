# Adamantine AI Gateway

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/DarekDGB/adamantine-ai-gateway)
[![Tests](https://img.shields.io/badge/tests-223%20passed-brightgreen.svg)](https://github.com/DarekDGB/adamantine-ai-gateway)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/DarekDGB/adamantine-ai-gateway)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Fail-closed, contract-first gateway for untrusted AI-originated work.

---

## Overview

Adamantine AI Gateway is a deterministic boundary layer that converts untrusted AI outputs into structured, validated, policy-controlled evidence.

It sits between variable external AI systems and the stricter Adamantine stack.

---

## System Diagram

```text
External AI
    ↓
Adapter
    ↓
Adamantine AI Gateway
    ├─ validate contract boundary
    ├─ enforce manifest/runtime alignment
    ├─ enforce policy
    ├─ produce deterministic output
    ├─ produce deterministic receipt
    └─ produce deterministic handoff
    ↓
Q-ID
    ↓
Shield v3
    ↓
Adaptive Core
    ↓
AdamantineOS
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

## What v1.0.0 Means

v1.0.0 is the first fully locked release of Adamantine AI Gateway as a deterministic execution boundary for untrusted AI-originated work.

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
→ Adapter
→ AI Gateway
→ Output
→ Receipt
→ Handoff
→ Q-ID
→ Shield v3
→ Adaptive Core
→ AdamantineOS
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
Produces output + receipt + handoff as the full governed path.

---

## Security Model

- All AI-originated work is treated as untrusted input
- All accepted artifacts must match strict contract shape
- All governed flows require manifest/runtime alignment
- All decisions must remain deterministic
- All failures must remain fail-closed
- All important rejection paths must emit explicit reason IDs
- No silent fallback is allowed

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
- Adapters translate, gateway verifies and enforces

---

## Release Status

v1.0.0 establishes Adamantine AI Gateway as a locked deterministic enforcement boundary for AI systems.

---

MIT License © DarekDGB
