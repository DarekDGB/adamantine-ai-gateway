# AI Gateway AdamantineOS Integration

Author attribution: **DarekDGB**  
Status: V1 and V2 AdamantineOS-facing producer exporters  
AI Gateway package boundary: `v1.0.0` remains unchanged  
AdamantineOS authority: final fail-closed policy and execution decision remains
inside AdamantineOS

## Purpose

This document records the AI Gateway side of the AdamantineOS evidence
connection. AI Gateway is an evidence producer only. It does not approve
execution, sign transactions, broadcast, override policy, or change DigiByte
consensus.

## V1 unbound evidence exporter

```text
build_adamantine_ai_gateway_evidence_v1(...)
build_adamantine_ai_gateway_evidence_from_gateway_result_v1(...)
```

The frozen V1 bundle contains exactly:

```text
evidence_version
source
evidence_role
expected_context_hash
handoff
receipt
```

V1 verifies context and receipt/handoff coherence. It contains no policy-pack
identity or digest and must not be described as proving which policy pack was
evaluated.

The V1 from-result exporter now requires an exact bounded built-in result
snapshot. If the result contains `policy_binding`, even with a null value, it
rejects with `POLICY_BOUND_RESULT_REQUIRES_EVIDENCE_V2`. This prevents the
helper itself from discarding a present binding. It cannot detect prior key
removal or direct V1-builder use; a D3 exact-policy consumer must require V2 and
prohibit fallback to V1.

## V2 policy-bound evidence exporter

```text
build_adamantine_ai_gateway_evidence_v2(...)
build_adamantine_ai_gateway_evidence_from_gateway_result_v2(...)
```

The V2 bundle contains exactly:

```text
evidence_version
source
evidence_role
expected_context_hash
handoff
receipt
policy_binding
```

V2 validates exact built-in artifact snapshots, expected context, output links
on the from-result path, receipt/handoff coherence, decision and reason
semantics, equality of output/handoff context with the canonical envelope hash,
fixed `canonical_sha256_no_time_v1` receipt profile, and canonical
receipt/handoff hashes in `AI_GATEWAY_POLICY_BINDING_V1`.

The output is validated but not exported. The source policy snapshot is also
not exported. The bundle therefore cannot independently recompute the output
or policy hash from its own fields alone.

## Required AdamantineOS path

```text
AI Gateway V1 or V2 evidence
        v
V4.9-D3 AdamantineOS independent evidence normalizer and expected-policy boundary (pending)
        v
AdamantineOS final policy and execution boundary
```

V4.9-D2 implements only the Gateway producer and exporter. It does not modify
AdamantineOS. The V4.9-D3 consumer must receive expected policy ID, version, and
digest from verifier-controlled trusted local configuration and must fail
closed on unknown, missing, malformed, spliced, or mismatched bindings.

## Locked authority behavior

Both evidence versions use `evidence_role: evidence_only`. They intentionally
contain no final approval, execution grant, bypass, rescue, override, signing,
or broadcast authority.

Deterministic linkage is not producer authentication, source provenance,
freshness, replay protection, remote attestation, a signature, or proof of
honest execution. No Gateway evidence result can grant final AdamantineOS
approval.

## Version rule

No package version bump or tag is introduced by V4.9-D2. Package version
`1.0.0` and all frozen V1 artifact shapes remain unchanged.

---

**MIT - DarekDGB**
