# Adamantine AI Gateway Evidence V2

Author attribution: **DarekDGB**  
Evidence identifier: `adamantine_ai_gateway_evidence_v2`  
Source identifier: `adamantine-ai-gateway`  
Evidence role: `evidence_only`  
Status: V4.9-D2 producer-side export contract with a separately verified
V4.9-D3B AdamantineOS consumer

## Purpose

This contract packages a validated AI Gateway handoff, receipt, and
`AI_GATEWAY_POLICY_BINDING_V1` artifact for an independent AdamantineOS
consumer. It is evidence packaging only. It does not modify AdamantineOS or
grant final policy or execution authority.

## Exact evidence shape

The V2 bundle contains exactly these seven fields:

| Field | Required value or rule |
|---|---|
| `evidence_version` | Exact string `adamantine_ai_gateway_evidence_v2` |
| `source` | Exact string `adamantine-ai-gateway` |
| `evidence_role` | Exact string `evidence_only` |
| `expected_context_hash` | Caller-supplied expected lowercase 64-character SHA-256 hex; the D3B consumer compares it with verifier-controlled local context |
| `handoff` | Valid `AI_GATEWAY_HANDOFF_V1` artifact |
| `receipt` | Valid `AI_GATEWAY_RECEIPT_V1` artifact |
| `policy_binding` | Valid `AI_GATEWAY_POLICY_BINDING_V1` artifact |

Authority-bearing fields are forbidden recursively. The bundle does not
contain `output`, a source PolicyPack snapshot, final approval, or an execution
decision.

## Producer APIs

```text
build_adamantine_ai_gateway_evidence_v2(...)
build_adamantine_ai_gateway_evidence_from_gateway_result_v2(...)
```

The direct builder requires exact built-in JSON dictionaries for handoff,
receipt, and policy binding. It captures those artifacts as one bounded
canonical snapshot before validation.

The from-result builder accepts only the exact four-key result returned by
`process_governed_with_policy_binding_v1(...)`:

```text
output
receipt
handoff
policy_binding
```

It snapshots the complete result before reading its keys, validates the output,
and checks that the output hash, adapter, task, context, decision, and reason ID
match the receipt and handoff. The output is checked but is not exported.

## Required linkage checks

The exporter rejects unless:

- `expected_context_hash` is an exact built-in lowercase SHA-256 hex string;
- handoff context equals both the expected context and its envelope hash;
- receipt and handoff agree on adapter, envelope hash, output hash, policy
  decision, and reason ID;
- decision and reason semantics are coherent;
- receipt determinism profile is exactly
  `canonical_sha256_no_time_v1`;
- binding `receipt_hash` equals canonical SHA-256 of the validated receipt; and
- binding `handoff_hash` equals canonical SHA-256 of the validated handoff.

Malformed, subclassed, oversized, cyclic, spliced, semantically contradictory,
or caller-profile-selected inputs reject. Backend and hashing exceptions do not
produce an evidence bundle.

## From-result no-drop rule

The frozen V1 evidence exporter remains available for unbound V1 results.
However,
`build_adamantine_ai_gateway_evidence_from_gateway_result_v1(...)` requires an
exact bounded built-in result dictionary snapshot and rejects any result containing a
`policy_binding` key with:

```text
POLICY_BOUND_RESULT_REQUIRES_EVIDENCE_V2
```

The rejection applies even if the binding value is `null`. This helper prevents
in-call removal of a present binding. It cannot detect a caller that deleted the
key before the call or used the direct V1 builder. The verified D3B consumer
requires V2 and prohibits fallback to V1 wherever exact policy identity is
required.

## Consumer boundary and limitations

V4.9-D2 implements producer-side validation and packaging. The separate
V4.9-D3B AdamantineOS consumer independently reproduces the frozen canonical
bytes and checks expected context, policy ID, policy version, and complete
policy hash against verifier-controlled trusted local configuration. It rejects
missing binding with no V1 fallback and keeps earlier denials dominant.

Successful D3B verification proves deterministic declared-content linkage and
agreement with those local expectations. It is not Gateway authentication or
an AdamantineOS policy-acceptance or execution-authority proof; every consumer
result keeps `final_approval == false`.

The bundle provides deterministic content linkage. It does not provide:

- producer authentication, signature, source provenance, or attestation;
- freshness or replay protection;
- proof of honest execution;
- proof that the declared policy was trusted by the consumer;
- downgrade, rescue, bypass, override, signing, broadcast, or execution
  authority.

Because the bundle does not contain the output or source policy snapshot, a
consumer cannot independently recompute their hashes from this bundle alone.

---

**MIT - DarekDGB**
