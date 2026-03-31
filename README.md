# Adamantine AI Gateway

Fail-closed, contract-first gateway for untrusted AI-originated work.

------------------------------------------------------------------------

## Overview

Adamantine AI Gateway is a deterministic boundary layer that converts\
untrusted AI outputs into structured, validated, policy-controlled\
evidence.

External AI\
→ Adapter\
→ AI Gateway\
→ Q-ID → Shield v3 → Adaptive Core → AdamantineOS

------------------------------------------------------------------------

## v0.5.0 Highlights

-   PolicyPack V1 (deterministic policy enforcement contract)
-   AI Gateway Handoff V1 (final decision artifact for downstream
    systems)
-   Governed processing path (`process_governed`)
-   Manifest-required execution mode (no manifest → fail)
-   Receipt-required execution mode (always produces evidence)
-   Boundary input limits (depth, size, structure, strings)
-   Strict abuse/negative test coverage
-   100% test coverage enforced

------------------------------------------------------------------------

## What Changed in v0.5.0

v0.5.0 upgrades the gateway from a validation layer to a full\
**enforcement and governance boundary**.

The system now:

-   Enforces policy before execution
-   Requires adapter manifests
-   Produces deterministic receipts for all flows
-   Generates handoff artifacts for downstream decision systems
-   Rejects malformed or abusive inputs at the boundary

This transforms the gateway into a **deterministic execution firewall
for AI-originated work**.

------------------------------------------------------------------------

## Core Flow

External AI\
→ Adapter (translation)\
→ AI Gateway (validation + policy enforcement)\
→ Receipt (evidence)\
→ Handoff (decision artifact)\
→ Q-ID → Shield v3 → Adaptive Core → AdamantineOS

------------------------------------------------------------------------

## Principles

-   Fail-closed always\
-   Contract-first\
-   Deterministic processing\
-   No unknown fields\
-   Canonical-safe payloads\
-   Explicit reason_id for all failures\
-   No silent fallbacks\
-   Adapters translate, gateway verifies and enforces

------------------------------------------------------------------------

## Security Model

-   All AI output is treated as untrusted input\
-   All inputs must pass strict contract validation\
-   All actions must pass policy enforcement\
-   All decisions are recorded as deterministic evidence\
-   All failures produce valid contract outputs

No execution is allowed without:

-   Valid contract\
-   Valid policy\
-   Valid manifest\
-   Deterministic validation

------------------------------------------------------------------------

## Status

v0.5.0 establishes Adamantine AI Gateway as a\
**deterministic enforcement boundary for AI systems**.

------------------------------------------------------------------------

MIT © DarekDGB
