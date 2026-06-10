# AI Gateway AdamantineOS Integration

Author attribution: **DarekDGB**
Status: AdamantineOS-facing evidence exporter for Milestone 16F
AI Gateway version boundary: `v1.0.0` remains unchanged
AdamantineOS authority: final fail-closed decision remains inside AdamantineOS

## Purpose

This document records the AI Gateway side of the AdamantineOS Milestone 16F connection.

AI Gateway is an evidence producer only. It exports deterministic handoff and receipt evidence for AdamantineOS, but it does not approve execution, signing, broadcasting, or wallet actions.

## Exported surface

```text
ai_gateway.integration.adamantine.build_adamantine_ai_gateway_evidence_v1(...)
ai_gateway.integration.adamantine.build_adamantine_ai_gateway_evidence_from_gateway_result_v1(...)
```

The exported evidence bundle contains:

```text
evidence_version
source
evidence_role
expected_context_hash
handoff
receipt
```

It intentionally does not contain:

```text
final_approval
handoff_allowed
grant_execution
override
authority
```

## Required AdamantineOS path

```text
AI Gateway handoff / receipt evidence
        v
AdamantineOS AI Gateway policy evidence boundary
        v
AdamantineOS final policy engine
```

## Locked behavior

```text
AI Gateway evidence is evidence only.
Raw AI output is not exported as authority.
Expected context hash must be lowercase 64-character hex.
Handoff context hash must match the expected context hash.
Receipt must match handoff adapter, envelope hash, output hash, policy decision, and reason ID.
Missing handoff or receipt rejects.
Hidden authority fields reject.
No AI Gateway result can grant final AdamantineOS approval.
```

## Version rule

No version bump or tag is introduced by this integration hardening step.
