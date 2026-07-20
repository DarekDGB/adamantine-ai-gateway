# AI Gateway Policy Binding V1

Author attribution: **DarekDGB**  
Contract identifier: `ai_gateway_policy_binding_v1`  
Policy-pack contract identifier: `policy_pack_v1`  
Canonical profile: `ai_gateway_canonical_json_v1`  
Status: V4.9-D2 producer contract with V4.9-D3A byte-profile lock and a
separately verified V4.9-D3B AdamantineOS consumer

## Purpose

`AI_GATEWAY_POLICY_BINDING_V1` provides deterministic content linkage between
one captured PolicyPack V1 snapshot and the receipt and handoff produced for the
same governed operation. It is a separate artifact. It does not add fields to
the frozen V1 output, receipt, or handoff contracts.

## Exact artifact shape

The artifact is an exact JSON object with these seven fields and no others:

| Field | Required value or rule |
|---|---|
| `policy_binding_version` | Exact string `ai_gateway_policy_binding_v1` |
| `policy_pack_contract_version` | Exact string `policy_pack_v1` |
| `policy_pack_id` | Non-empty PolicyPack V1 ID, maximum 256 characters |
| `policy_pack_version_id` | Non-empty PolicyPack V1 version ID, maximum 256 characters |
| `policy_pack_hash` | Lowercase 64-character canonical SHA-256 hex |
| `receipt_hash` | Lowercase 64-character canonical SHA-256 hex |
| `handoff_hash` | Lowercase 64-character canonical SHA-256 hex |

No algorithm or profile field is caller selectable. This contract fixes
`ai_gateway_canonical_json_v1` plus SHA-256. The profile identifier is
contract-fixed and is not a new artifact field. The linked receipt must use
`canonical_sha256_no_time_v1`; any other determinism profile is rejected.

## Policy snapshot and identity rules

The producer must:

1. reject non-built-in JSON types, container subclasses, cycles, floats,
   malformed Unicode, and unsupported structure before using the policy;
2. validate the complete PolicyPack V1 object;
3. capture it as immutable canonical UTF-8 JSON bytes before any registry or
   adapter callback;
4. derive the declared policy ID, version ID, and SHA-256 digest from that one
   validated snapshot;
5. materialize the same captured bytes for policy enforcement; and
6. use the captured identity and digest when constructing the binding.

The policy hash covers every validated PolicyPack V1 field, including `notes`.
Object keys are sorted by Unicode scalar-value sequence under
`ai_gateway_canonical_json_v1`. Array order remains identity-bearing. No
Unicode normalization is applied.

The complete byte algorithm, escaping rules, raw-wire duplicate-key rule,
literal vectors, injectivity pairs, and boundary vectors are defined by
`AI_GATEWAY_CANONICAL_JSON_V1.md`. A raw JSON parser must reject duplicate
decoded keys before constructing a mapping. An already decoded mapping cannot
prove that its wire representation was duplicate-free.

## Artifact-chain checks

Before a binding may be returned, the producer snapshots the envelope, output,
receipt, and handoff into bounded exact built-in JSON values and checks:

- envelope adapter and task match the output;
- receipt and handoff adapter identity match the output;
- handoff task matches the output;
- receipt and handoff envelope hashes equal SHA-256 of the envelope encoded by
  `ai_gateway_canonical_json_v1`;
- receipt and handoff output hashes equal SHA-256 of the output encoded by
  `ai_gateway_canonical_json_v1`;
- receipt and handoff decisions and reason IDs match the output;
- accepted output uses `ACCEPTED` and rejected output uses a registered,
  non-`ACCEPTED` reason ID;
- output and handoff context hashes equal SHA-256 of the envelope encoded by
  `ai_gateway_canonical_json_v1`;
- receipt determinism profile is exactly `canonical_sha256_no_time_v1`; and
- `receipt_hash` and `handoff_hash` bind the validated artifacts encoded by
  `ai_gateway_canonical_json_v1`.

Only the V4.9-D2 path
`AIGateway.process_governed_with_policy_binding_v1(...)` returns this artifact.
The frozen `process_governed(...)` path remains policy-identity unbound.

## Bound denial and atomic failure rules

A genuine policy denial may return a complete rejected chain. Its receipt and
handoff bind the actual validated envelope that was evaluated, so distinct
denied operations do not collapse into the same envelope evidence. The D2
rejected output uses canonical SHA-256 of that envelope as its context hash,
allowing the V2 exporter to check the same expected operation context.

No binding is produced when policy evaluation was not reached. Policy capture,
manifest capability, registry, adapter, output, chain, semantic, hashing,
canonicalization, or builder failure returns an atomic unbound result:

```text
output: fail-closed rejected output
receipt: null
handoff: null
policy_binding: null
```

Malformed policy input fails before registry or adapter callbacks. Unexpected
dependency and backend exceptions map to `INTERNAL_ERROR` and cannot leave
partial evidence.

A missing, blank, non-string, or manifest-undeclared action fails before policy
evaluation with no receipt, handoff, or policy binding. Absence of an action
cannot bypass the manifest or policy action allowlists.

## Resource limits

The D2 exact-snapshot boundary enforces:

- maximum depth: 10;
- maximum keys per object: 1,000;
- maximum items per array: 1,000;
- maximum string and object-key length: 10,000 Unicode scalar values;
- maximum exact JSON integer width: 4,096 bits;
- maximum snapshot nodes: 20,000;
- maximum canonical snapshot size and cumulative string, key, and integer-text
  preflight budget:
  1,048,576 bytes; and
- maximum canonical binding artifact size: 4,096 bytes.

The scalar-value limit is separate from the UTF-8 byte limits. It is not a
UTF-8 byte, UTF-16 code-unit, grapheme, or display-width count.

## Security and authority limits

This artifact provides deterministic content linkage only. It is not:

- producer authentication or source provenance;
- a digital signature or remote attestation;
- freshness or replay protection;
- proof of honest execution;
- proof that a verifier expected or trusted the declared policy;
- approval, override, bypass, rescue, signing, broadcast, or execution
  authority.

The artifact does not contain the source policy snapshot. A consumer cannot
independently recompute `policy_pack_hash` without receiving that snapshot from
a separately controlled source. The V4.9-D3B AdamantineOS consumer compares the
declared ID, version, and complete policy hash only with verifier-controlled
trusted local expectations. Successful comparison remains evidence-only with
`final_approval == false`; it does not authenticate the Gateway or prove the
declared policy snapshot was possessed or enforced.

V4.9-D3A proves the current Python producer against an independent Python
encoder. It does not claim Rust or SDK conformance. A Rust claim requires the
shared literal vectors and Python-to-Rust byte differential fuzzing.

---

**MIT - DarekDGB**
