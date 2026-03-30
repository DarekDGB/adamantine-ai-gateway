# Adamantine AI Gateway

Fail-closed, contract-first gateway for untrusted AI-originated work.

---

## Purpose

Adamantine AI Gateway is a deterministic boundary layer for external AI-produced artifacts before they can move deeper into the Adamantine stack.

It treats all AI-originated outputs as untrusted input.

No adapter, model, provider, or agent is trusted by default.

The gateway converts variable, source-specific AI outputs into deterministic, contract-bound, policy-controlled evidence that can be evaluated downstream.

---

## Position in the Stack

External AI Source  
→ Adapter  
→ Adamantine AI Gateway  
→ Q-ID  
→ Shield v3  
→ Adaptive Core  
→ AdamantineOS  

---

## Core Principle

Untrusted AI boundary.  
Fail-closed.  
Contract-first.  

---

## Invariants

- No raw AI output enters the system unchecked  
- All accepted artifacts must be contract-bound  
- Canonical serialization is required before hashing  
- Validation happens before downstream use  
- Policy decides what is allowed to pass  
- Identity is required downstream  
- Failure is explicit and closed, never silent  
- Adapters translate source-specific input but do not make trust decisions  

---

## Scope for v0.2.0

- Envelope contract v1  
- Output contract v1  
- Canonical serialization  
- Deterministic hashing  
- Strict validation layer (no unknown fields)  
- Canonical payload enforcement (deterministic-safe types only)  
- Typed error system  
- Reason ID registry  
- Adapter registry  
- Base adapter contract  
- Passive PoI adapter  
- Wallet adapter  
- Determinism rules  
- Negative-first tests  
- 100% enforced coverage  

---

## What Changed in v0.2.0

- Strict schema enforcement (reject unknown fields)  
- Canonical payload validation (no floats, no unsafe types)  
- Recursive payload validation  
- Typed gateway error handling (no string-based guessing)  
- Clean separation of adapter execution and registry lookup  
- Wallet adapter introduced as second adapter  
- Expanded fail-closed coverage across all error paths  

---

## Non-Goals for v0.2.0

- Running real AI models  
- Remote inference execution  
- Consensus integration  
- Live blockchain hooks  
- Autonomous trust decisions  
- Bypass paths around validation or policy  

---

## Adapter Model

Adapters normalize and translate external AI-originated data into the gateway contract shape.

Adapters are not allowed to:
- bypass validation  
- assign trust  
- silently coerce invalid data into valid state  
- directly decide downstream acceptance  

---

## Deterministic Boundary Guarantees

All inputs entering the gateway must satisfy:

- Exact contract structure  
- No unknown fields  
- Canonical-safe payload types only  
- Deterministic serialization compatibility  

This ensures:
- stable hashing  
- reproducible evaluation  
- no hidden or non-deterministic data  

---

## Philosophy

AI is untrusted input.

The gateway does not exist to make AI powerful.  
It exists to make AI-originated artifacts bounded, deterministic, inspectable, and safe to evaluate.

Only verifiable outputs may proceed downstream.

---

## Status

v0.2.0 — Deterministic boundary hardened

The gateway now operates as a strict execution boundary with enforced schema, canonical payload discipline, typed errors, and complete fail-closed coverage.

Next phase: Adapter manifests and controlled adapter ecosystem (v0.3.0).

---

MIT © DarekDGB
