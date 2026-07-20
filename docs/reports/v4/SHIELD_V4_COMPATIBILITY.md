# AI Gateway Shield v4 Compatibility Boundary

Author attribution: **DarekDGB**  
Step: `Shield V4.9-E`  
Status: compatibility boundary implemented in this source  
Gateway package version: `1.0.0` unchanged

## 1. Purpose

This document freezes how Adamantine AI Gateway may interact with the Shield
v4 ecosystem without becoming a Shield cryptographic verifier or an execution
authority.

AI Gateway validates its own contracts, enforces its own Gateway policy, and
produces Gateway-local deterministic evidence. Shield and AdamantineOS retain
their separate responsibilities.

## 2. Responsibility boundary

| Boundary | Responsibility |
|---|---|
| AI Gateway | Validate Gateway contracts, enforce Gateway policy, and emit Gateway-local evidence |
| Shield components and Orchestrator | Produce and verify Shield decision evidence under Shield roles, domains, algorithms, and profiles |
| AdamantineOS | Independently verify supplied evidence and apply the final fail-closed local policy and execution boundary |

AI Gateway does not verify Shield signatures and does not:

- import Shield runtime code;
- hold or interpret a Shield trust registry;
- select or satisfy a Shield key role;
- depend on OQS or expose a live-OQS workflow;
- sign transactions or Shield evidence;
- broadcast transactions;
- change DigiByte consensus; or
- grant final approval or execution authority.

AI Gateway has no Shield trust registry or Shield key role.

## 3. Shield policy reference

The current Shield v4 policy is stated here only to prevent compatibility
misrepresentation:

```text
required: classical-ed25519 + ml-dsa
optional: fn-dsa
optional family: pqc-fn-dsa
optional profile: fips206-draft-falcon1024-v1
optional parameter set: Falcon-1024
```

Draft FN-DSA/Falcon-1024 evidence is optional additional evidence. It cannot
replace Ed25519 or ML-DSA, rescue a required failure, weaken verifier policy, or
become execution authority. This document makes no final FIPS 206 claim.

AI Gateway does not parse, verify, or enforce any of these Shield algorithms or
profiles. It cannot approve, override, bypass, downgrade, or rescue a Shield
result.

AdamantineOS remains the independent final fail-closed local policy and
execution boundary.

## 4. Frozen Gateway-local contract shapes

The compatibility boundary does not add a Shield field to any Gateway artifact.
The existing exact top-level shapes remain:

### `AI_GATEWAY_OUTPUT_V1`

```text
contract_version
adapter
task_type
accepted
reason_id
output_payload
context_hash
```

### `AI_GATEWAY_RECEIPT_V1`

```text
receipt_version
gateway_version
adapter_id
adapter_version
envelope_hash
output_hash
policy_decision
reason_id
created_from_contract
determinism_profile
```

### `AI_GATEWAY_HANDOFF_V1`

```text
handoff_version
adapter
task_type
policy_decision
reason_id
envelope_hash
output_hash
context_hash
```

### `AI_GATEWAY_POLICY_BINDING_V1`

```text
policy_binding_version
policy_pack_contract_version
policy_pack_id
policy_pack_version_id
policy_pack_hash
receipt_hash
handoff_hash
```

### Adamantine evidence V1

```text
evidence_version
source
evidence_role
expected_context_hash
handoff
receipt
```

### Adamantine evidence V2

```text
evidence_version
source
evidence_role
expected_context_hash
handoff
receipt
policy_binding
```

None of these top-level schemas defines a Shield signature, signature bundle,
Shield algorithm, Shield `standard_profile`, Shield key ID, Shield key role,
Shield registry, or `final_approval` field.

The receipt field `determinism_profile` is Gateway-local canonical hashing
metadata fixed to `canonical_sha256_no_time_v1`. It is not a Shield signature
profile.

## 5. Gateway acceptance is not authority

`accepted` and `policy_decision: accepted` describe only the Gateway's local
contract and policy result. They do not mean:

- a Shield signature was verified;
- a Shield receipt was accepted;
- an expected Shield policy was satisfied;
- AdamantineOS granted final approval; or
- execution is authorized.

Every Adamantine evidence bundle uses `evidence_role: evidence_only` and omits
`final_approval`.

## 6. Shield-like and authority-like input

Unknown top-level fields are rejected by the frozen output, receipt, handoff,
and policy-binding validators. A caller cannot extend those contracts with a
signature, algorithm, profile, key role, Shield receipt, approval, bypass, or
execution field.

`output_payload` is bounded adapter data. Shield-like names inside that payload
remain untrusted data and are not interpreted as Shield evidence or authority.
The V2 exporter validates output linkage but does not export the output or its
payload.

Within exported handoff, receipt, and policy-binding artifacts, the Adamantine
evidence exporter recursively forbids these authority-shaped field names:

```text
allow
approve
approved
authority
authorization
bypass
final_approval
grant_execution
handoff_allowed
override
```

## 7. Independent D3B consumer boundary

The separately verified V4.9-D3B AdamantineOS consumer:

- accepts exact raw bytes only on the V2 policy-bound path;
- rejects duplicate decoded JSON keys before mapping construction;
- independently reproduces `ai_gateway_canonical_json_v1` bytes;
- receives expected context, policy ID, policy version, and complete policy
  hash from verifier-controlled trusted local configuration;
- rejects missing binding with no V1 fallback;
- keeps earlier denials dominant; and
- returns evidence-only results with `final_approval == false`.

That consumer does not transfer authority to Gateway. Successful verification
proves deterministic declared-content linkage and agreement with local
expectations only.

The V2 bundle is unsigned and omits the source envelope, output, and policy
snapshot. Neither Gateway nor the D3B consumer proves producer authentication,
source provenance, freshness, replay protection, remote attestation, honest
execution, possession or enforcement of the declared policy snapshot, signing,
broadcast, consensus change, or final execution authority.

## 8. Regression evidence

`tests/test_shield_v4_compatibility_lock.py` locks:

- the exact non-verifier responsibility statements in this document;
- the absence of Shield and OQS runtime dependencies;
- the unchanged closed Gateway artifact field sets;
- rejection of Shield-like and authority-like top-level fields;
- the exact ten recursively forbidden authority names;
- Gateway-local acceptance semantics;
- removal of stale predecessor-topology and pending-D3 claims; and
- DarekDGB-only attribution in every V4.9-E file.

This V4.9-E step changes documentation and regression tests only. It does not
change runtime code, fixtures, workflows, dependencies, package version, public
API, canonical bytes, or artifact hashes.

---

**MIT - DarekDGB**
