# Adapter Contract V1

## Purpose

This document defines the strict rules that every adapter must follow when interacting with the Adamantine AI Gateway.

Adapters are untrusted translation layers between external AI-originated sources and the gateway contracts.

They do not hold authority to assign trust, acceptance, or final decisions.

## Core Principle

Adapters translate.  
Gateway verifies.  
AdamantineOS decides.

## Responsibilities

An adapter MUST:

- Accept structured source input
- Translate input into `AI_GATEWAY_ENVELOPE_V1`
- Call validation before returning envelope
- Produce `AI_GATEWAY_OUTPUT_V1`
- Remain deterministic for identical inputs
- Never bypass validation or policy
- Never mutate validated envelope silently

## Prohibited Actions

An adapter MUST NOT:

- Execute remote AI calls (v0.1.0)
- Assign trust or final approval
- Bypass gateway validation
- Inject hidden fields
- Modify policy decisions
- Produce non-deterministic outputs
- Swallow errors silently
- Return partial or ambiguous states

## Determinism Requirements

For identical inputs, an adapter MUST:

- Produce identical envelopes
- Produce identical outputs
- Produce identical context hashes

Any deviation is considered a failure.

## Fail-Closed Requirement

If an adapter encounters:

- Invalid input
- Missing fields
- Unexpected structure

It MUST fail through validation or propagate error to gateway.

It must never attempt to "fix" or guess input.

## Output Rules

Adapter output MUST:

- Match `AI_GATEWAY_OUTPUT_V1`
- Always include `accepted`
- Always include `reason_id`
- Always include `context_hash`
- Return empty payload on failure

## Adapter Identity

Each adapter MUST:

- Have a fixed name
- Be registered in AdapterRegistry
- Not override another adapter
- Be explicitly invoked

## Versioning

Adapters must remain compatible with:

- Envelope V1
- Output V1

Breaking changes require new adapter or contract version.

## Example (PoI Adapter Role)

PoI adapter:

- Receives candidate input
- Normalizes into envelope
- Validates structure
- Applies policy check
- Returns contract-bound output

It does NOT:

- Run AI models
- Evaluate correctness of AI result
- Decide final trust

## Summary

Adapters are controlled translators.

They are not decision makers.

They are not trusted components.

Their only purpose is to safely bring external input into a deterministic boundary.
