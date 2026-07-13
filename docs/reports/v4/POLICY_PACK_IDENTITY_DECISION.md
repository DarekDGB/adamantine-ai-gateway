# AI Gateway Policy-Pack Identity Decision

Author attribution: **DarekDGB**  
Controlled step: `Shield V4.9-D1`  
Decision status: locked  
Decision: new versioned policy binding required  
Runtime and schema change in this step: none

---

## 1. Purpose

This document records whether frozen AI Gateway V1 evidence proves the identity
of the policy pack used by a governed operation. It also locks the required
AdamantineOS consumption boundary before a new contract is designed.

The decision is evidence based. It does not add fields to, reinterpret, or
replace any frozen V1 output, receipt, or handoff contract.

---

## 2. Fresh-source evidence

The decision was made from these fresh repository archives:

```text
adamantine-ai-gateway
ZIP SHA-256: 0f666ca09586947f3fff0f004910f0e0901ac050d5ba5e4e3f3742eb1226d423
Commit: 0648a0a1c1735500847ba04174d88417db147eec

DigiByte-AdamantineOS
ZIP SHA-256: a7ed29aba2c4d491d34ca6d832bb1a1f10c5a3578a3c4a890788862323d704fc
Commit: 98c5194db9c55ef679e8889e459027644691eb4e
```

Verified baseline:

```text
AI Gateway: 257 passed; 0 skipped; 100% statement and branch coverage
AdamantineOS: 1182 passed; 3 gated real-OQS skips; 100% statement coverage
```

The local AdamantineOS skips are the dedicated real-liboqs tests. This decision
does not change PQC code or make a live-OQS claim.

---

## 3. Verified V1 behavior

The Gateway receives `policy_pack` directly from the caller of
`process_with_policy(...)` or `process_governed(...)`. V1 contains no trusted
policy loader, verifier-controlled policy registry, expected policy digest,
policy signature, or authenticated policy source.

`validate_policypack_v1(...)` validates contract shape and values. It does not
authenticate `policypack_id`, `policypack_version_id`, `notes`, or the caller.

The frozen V1 artifact shapes contain no policy-pack identity:

```text
AI_GATEWAY_OUTPUT_V1: no policy ID, version, hash, or reference
AI_GATEWAY_RECEIPT_V1: no policy ID, version, hash, or reference
AI_GATEWAY_HANDOFF_V1: no policy ID, version, hash, or reference
```

Tests prove that two policy packs with different IDs, versions, and permitted
rule sets can produce byte-identical output, receipt, and handoff when both
permit the evaluated request. A downstream consumer cannot distinguish those
packs from V1 evidence.

AdamantineOS independently validates the closed V1 handoff and receipt shapes,
lowercase SHA-256 field syntax, pairwise equality of the envelope/output hash
fields and shared decision fields, and the expected context hash. It does not
receive the source envelope or output and therefore cannot independently
recompute those two hashes. Its V1 normalizer receives no expected policy-pack
identity or digest, and its result contains no policy-pack identity.

---

## 4. Decision

The trusted-local-configuration prerequisite for a V1 identity claim is not
met. The selected path is:

```text
NEW VERSIONED POLICY BINDING REQUIRED
```

V1 remains byte-exact and policy-identity unbound. It may remain deterministic
advisory evidence, but neither Gateway nor AdamantineOS may claim that V1 proves
which policy pack produced the decision.

No V1 field is added, removed, or reinterpreted by this decision.

---

## 5. Required producer design

A later controlled step must introduce a separately versioned policy-binding
artifact. At minimum, its normative design must bind:

```text
binding contract version
policy-pack contract version
policy-pack ID
policy-pack version ID
canonical SHA-256 of the complete validated policy snapshot
receipt hash
handoff hash
```

Producer requirements:

- capture one immutable validated snapshot of the complete policy pack;
- use that same snapshot for enforcement and binding construction;
- include every identity-bearing V1 policy field, including `notes`, in the
  canonical policy hash;
- use canonical JSON and lowercase SHA-256 hex;
- normalize object-key order while preserving array order as identity-bearing;
- bind the policy reference to the exact receipt and handoff from the same
  governed operation;
- reject missing, malformed, unknown, oversized, or mismatched binding data;
- prevent caller mutation from changing the captured snapshot;
- keep all existing V1 artifacts and APIs byte-for-byte compatible;
- never add approval, signing, broadcast, override, bypass, downgrade, rescue,
  or execution authority.

The deterministic binding proves artifact-to-policy-reference consistency. It
is not producer authentication, remote attestation, a signature, or proof that
untrusted runtime code executed honestly.

---

## 6. AdamantineOS consumption semantics

AdamantineOS remains an independent, verify-only, fail-closed policy and
execution boundary.

For frozen V1 evidence:

- `ALLOW_EVIDENCE_CONTINUE_CHECKS` means only that the accepted V1 handoff and
  receipt are internally coherent for the expected context;
- it does not mean that a particular policy pack was used;
- `final_approval` remains false;
- no policy identity may be inferred from `policy_decision`, `reason_id`,
  adapter identity, Gateway version, Q-ID identity, or any external label;
- V1 must not satisfy a check that requires an exact Gateway policy identity.

For the future policy-bound path:

- AdamantineOS must receive its expected policy ID, version, and digest from
  verifier-controlled trusted local configuration;
- unknown, missing, malformed, spliced, or mismatched bindings fail closed;
- a binding cannot bypass independent replay controls, and any earlier replay
  denial remains dominant;
- a policy-bound path must not fall back automatically to unbound V1 evidence;
- a valid binding remains evidence only and cannot grant execution authority;
- AdamantineOS's unrelated internal risk `PolicyPack` must not be reused as the
  AI Gateway policy-pack identity contract;
- Q-ID identity keys and Shield decision-evidence keys remain separate and must
  not be reused for this binding.

---

## 7. Controlled sequencing

The implementation is split to keep each security boundary independently
reviewable:

```text
V4.9-D1  decision, V1 truth correction, and regression lock
V4.9-D2  Gateway versioned policy-binding producer
V4.9-D3  AdamantineOS independent policy-binding consumer
V4.9-E   Gateway Shield v4 compatibility contract
```

V4.9-E must not begin until V4.9-D3 is verified from fresh post-commit ZIPs.

---

## 8. Security and authority lock

AI Gateway does not sign transactions, broadcast, change DigiByte consensus, or
make final AdamantineOS policy decisions.

Shield cryptographic verification remains in the Shield and AdamantineOS
boundaries. Required Shield algorithms remain `classical-ed25519 + ml-dsa`.
Optional `fn-dsa` evidence cannot rescue, replace, downgrade, or override a
required result. This policy-pack decision introduces no OQS dependency and no
claim that FIPS 206 is final.

Cryptographic or deterministic evidence does not grant execution authority.
