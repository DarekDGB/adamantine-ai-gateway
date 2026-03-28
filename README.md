# Adamantine AI Gateway

Fail-closed, contract-first gateway for untrusted AI-originated work.

## Purpose

Adamantine AI Gateway is a deterministic boundary layer for external AI-produced artifacts before they can move deeper into the Adamantine stack.

It is designed to treat all AI-originated outputs as untrusted input.

No adapter, model, provider, or agent is trusted by default.

The gateway exists to convert variable, source-specific AI outputs into deterministic, contract-bound, policy-controlled evidence that can be evaluated downstream.

## Position in the Stack

External AI Source  
→ Adapter  
→ Adamantine AI Gateway  
→ Q-ID  
→ Shield v3  
→ Adaptive Core  
→ AdamantineOS

## Core Principle

Untrusted AI boundary.  
Fail-closed.  
Contract-first.

## Invariants

- No raw AI output enters the system unchecked
- All accepted artifacts must be contract-bound
- Canonical serialization is required before hashing
- Validation happens before downstream use
- Policy decides what is allowed to pass
- Identity is required downstream
- Failure is explicit and closed, never silent
- Adapters translate source-specific input but do not make trust decisions

## Scope for v0.1.0

- Envelope contract v1
- Output contract v1
- Canonical serialization
- Deterministic hashing
- Validation layer
- Reason ID registry
- Adapter registry
- Determinism rules
- Base adapter contract
- Single passive PoI adapter
- Negative-first tests
- 100% enforced coverage

## Non-Goals for v0.1.0

- Running real AI models
- Remote inference execution
- Consensus integration
- Live blockchain hooks
- Autonomous trust decisions
- Bypass paths around validation or policy

## Adapter Model

Adapters are allowed to normalize and translate external AI-originated data into the gateway contract shape.

Adapters are not allowed to:
- bypass validation
- assign trust
- silently coerce invalid data into valid state
- directly decide downstream acceptance

## Philosophy

AI is untrusted input.

The gateway does not exist to make AI powerful.  
It exists to make AI-originated artifacts bounded, deterministic, inspectable, and safe to evaluate.

Only verifiable outputs may proceed downstream.

## Status

Blueprint and v0.1.0 foundation in progress.
