# POLICYPACK_V1

## Purpose

`POLICYPACK_V1` defines the deterministic policy object used by Adamantine AI Gateway governed flows.

It is a contract-bound control-plane input.

It does not replace adapter manifests.  
It constrains what already-declared adapter behavior is allowed to execute.

---

## Contract ID

`policy_pack_v1`

---

## Required Fields

- `policypack_version`
- `policypack_id`
- `policypack_version_id`
- `default_decision`
- `adapter_policies`
- `notes`

No unknown fields are allowed.

---

## Field Definitions

### `policypack_version`
String. Must equal `policy_pack_v1`.

### `policypack_id`
String. Stable logical identifier for the policy pack.

Example:  
`gateway-governed`

### `policypack_version_id`
String. Explicit version identifier for the concrete policy pack instance.

Example:  
`v0.5.0`

### `default_decision`
String.

Allowed values:
- `deny`

This contract is fail-closed.  
There is no permissive default mode.

### `adapter_policies`
Object keyed by adapter id.

Each adapter policy object must contain:
- `allowed_task_types`
- `allowed_model_families`
- `allowed_actions`

Each value must be a list of unique non-empty strings.

Example:

```json
{
  "poi": {
    "allowed_task_types": ["code_review", "documentation"],
    "allowed_model_families": ["poi-v1", "deterministic-test-model"],
    "allowed_actions": ["evaluate_candidate"]
  },
  "wallet": {
    "allowed_task_types": ["wallet_operation"],
    "allowed_model_families": ["wallet-v1"],
    "allowed_actions": ["build_transaction", "sign_transaction_request"]
  }
}
```

The adapter id key is authoritative and must be a non-empty string.

Empty `adapter_policies` is invalid.

### `notes`
String. Human-readable description of scope or intent.

---

## Trust and Evidence Boundary

`POLICYPACK_V1` validation proves the shape and allowed values of a policy-pack
input. It does not authenticate the source of that input.

The current `process_with_policy(...)` and `process_governed(...)` APIs receive
the policy pack from their caller. The V1 contract does not provide a trusted
policy registry, verifier-controlled allowlist, signature, or expected digest.

The fields `policypack_id` and `policypack_version_id` are validated labels.
They are not trust anchors. The V1 output, receipt, and handoff contracts contain
no policy-pack ID, version, hash, or policy reference. Distinct policy packs that
permit the same request can therefore produce byte-identical V1 artifacts.

Consequences:

- a V1 output, receipt, or handoff does not prove which policy pack was used;
- a downstream consumer must not infer policy identity from `policy_decision`,
  `reason_id`, or any other V1 artifact field;
- a deployment may pin a policy pack in trusted local configuration, but that
  trust exists outside the V1 evidence chain;
- a consumer that requires proof of an exact policy pack must use a separately
  versioned policy-binding contract and a verifier-controlled expected policy
  reference;
- no policy-identity field may be added silently to a frozen V1 artifact.

V1 artifacts remain deterministic evidence, but they are policy-identity
unbound.

---

## Determinism Rules

- Canonical JSON only
- No unknown fields
- No floats
- No duplicate values inside string lists
- Adapter policy sections must be explicit
- Default behavior is deny
- Validation failure is fail-closed

---

## Non-Goals

`POLICYPACK_V1` does not:
- make final AdamantineOS decisions
- grant wallet signing authority
- override manifest identity
- introduce time-based or random behavior
- authenticate its caller or source
- bind its identity or complete content to V1 output, receipt, or handoff
- prove which policy pack produced a downstream V1 artifact

---

## Validation Expectations

Validation must reject:
- wrong `policypack_version`
- unknown top-level fields
- unknown adapter policy fields
- empty strings
- non-string adapter ids
- empty `adapter_policies`
- duplicate list entries
- unsupported `default_decision`
- non-canonical JSON values

All failures must be treated as fail-closed.
