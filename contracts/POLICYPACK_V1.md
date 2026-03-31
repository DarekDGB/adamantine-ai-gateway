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
