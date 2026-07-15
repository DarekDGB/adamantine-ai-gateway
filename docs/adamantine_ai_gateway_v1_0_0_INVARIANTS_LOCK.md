# Adamantine AI Gateway — v1.0.0 Invariants Lock

**Status:** LOCKED V1.0.0 BOUNDARY RECORD  
**Release boundary:** `v1.0.0`  
**Current repo state reviewed:** `v1.0.0` fresh V4.9-D2 producer source  
**Owner attribution:** DarekDGB

---

## Purpose

This document preserves the **security, determinism, contract, and release invariants** that define the Adamantine AI Gateway `v1.0.0` boundary and must remain true during later compatibility work.

It exists to prevent scope drift, silent weakening, and false completion.

This is not a feature wishlist.
This is a **boundary lock document**.

Historical build-sequencing and exit-criteria sections are retained as the
record used to establish the `v1.0.0` boundary. They do not describe the current
repository as a pre-release or `v0.5.0` state.

---

## Current confirmed baseline

From the reviewed repository ZIP and roadmap:

- package exists under `ai_gateway/`
- contracts already exist for:
  - `AI_GATEWAY_ENVELOPE_V1`
  - `AI_GATEWAY_OUTPUT_V1`
  - `ADAPTER_MANIFEST_V1`
  - `AI_GATEWAY_RECEIPT_V1`
  - `AI_GATEWAY_HANDOFF_V1`
  - `POLICYPACK_V1`
- registry / gateway / policy / handoff / determinism modules are already present
- PoI and Wallet adapters already exist
- governed flow tests already exist
- 100% coverage discipline is already part of repo culture
- clean-package execution reality must remain explicit and tested

The current source also contains a separately versioned, post-v1.0.0
compatibility extension:

- `AI_GATEWAY_POLICY_BINDING_V1`
- `ADAMANTINE_AI_GATEWAY_EVIDENCE_V2`
- `process_governed_with_policy_binding_v1(...)`

These additions do not change the six frozen V1 artifact shapes or package
version `1.0.0`.

This means `v1.0.0` is **not** about adding ideas from scratch.
It is about freezing and proving the boundary.

---

## One-line definition of v1.0.0

**`v1.0.0` is the point where Adamantine AI Gateway becomes a sealed, deterministic, installable, integration-safe boundary product.**

---

## Core invariant groups

## 1. Public API freeze

The package public API must be intentionally small and explicitly frozen.

### Required invariant

Only documented, tested exports are public boundary API.

### Minimum lock

- public imports must be explicitly defined in `ai_gateway/__init__.py`
- undocumented convenience exports must not leak into public API by accident
- changing or removing a public export requires version review
- README / package exports / tests must agree
- root `ai_gateway.__all__` remains unchanged by V4.9-D2
- new versioned contract and integration symbols are locked in their explicit
  `ai_gateway.contracts` and `ai_gateway.integration` namespaces

### Required proof

- API surface test that asserts exact exported names
- install-based import test using package installation reality
- regression test proving accidental new exports fail the lock

---

## 2. Contract freeze

All public contracts must be treated as versioned boundary law.

### Frozen contracts

- `AI_GATEWAY_ENVELOPE_V1`
- `AI_GATEWAY_OUTPUT_V1`
- `ADAPTER_MANIFEST_V1`
- `AI_GATEWAY_RECEIPT_V1`
- `AI_GATEWAY_HANDOFF_V1`
- `POLICYPACK_V1`

### Post-v1.0.0 compatibility contracts

- `AI_GATEWAY_POLICY_BINDING_V1`
- `ADAMANTINE_AI_GATEWAY_EVIDENCE_V2`

These contracts are separate extensions. They do not silently add, remove, or
reinterpret fields in any frozen V1 contract.

### Required invariant

- no silent field additions
- no silent field removals
- no unknown field acceptance
- no type ambiguity tolerated
- semantic contract change requires explicit version bump
- docs and tests map 1:1 to actual validation behavior

### Required proof

- contract tests must reject unknown fields and malformed values
- canonical fixture tests must lock valid examples
- regression fixtures must exist for every frozen contract

---

## 3. Artifact-chain invariants

A governed output is not trusted as isolated objects.
The full evidence chain must remain internally coherent.

### Required invariant

A governed handoff must bind together a coherent chain:

`manifest -> envelope -> output -> receipt -> handoff`

Policy evaluation is a required governed-path precondition, but the frozen V1
output, receipt, and handoff artifacts do not contain a policy reference. They
must not be described as proving which policy pack was evaluated.

### Required locks

- adapter identity in manifest must match adapter used in execution
- action requested must be declared by manifest capability
- envelope contents used for execution must match contents represented in receipt / handoff chain
- output object used in receipt must be the exact output represented by handoff
- policy-pack identity must not be inferred from a V1 handoff, receipt, policy decision, or reason ID
- any exact-policy claim requires a separately versioned binding to the complete validated policy snapshot and the artifact chain
- tampering with any linked object must invalidate downstream trust

### Required proof

- mismatch-chain negative tests
- handoff tamper tests
- cross-object hash / identity lock tests
- regression proof that distinct policy packs can produce identical V1 artifacts
- no partially coherent evidence bundle accepted as valid governed output

### V4.9-D policy-pack identity decision

The current governed API accepts a caller-supplied policy pack. No trusted
policy loader, pinned registry, expected policy digest, or authenticated policy
source exists in V1. The `policypack_id` and `policypack_version_id` fields are
therefore validated labels, not evidence-chain trust anchors.

V1 remains frozen and policy-identity unbound. A downstream consumer may handle
V1 as advisory evidence, but it must not claim that V1 proves an active policy
identity. Where exact policy identity is required, missing versioned binding is
a failed precondition; there must be no silent fallback to V1.

V4.9-D2 implements the selected path as a new versioned policy-binding artifact.
It binds the canonical hash and declared ID/version of one immutable validated
policy snapshot to the receipt and handoff produced from that same governed
operation. This does not authorize a silent field addition to any frozen V1
contract.

### V4.9-D2 producer status

V4.9-D2 implements the selected producer path:

- the complete PolicyPack V1 object is exact-type checked, bounded, validated,
  and captured as immutable canonical bytes before registry or adapter
  callbacks;
- the captured bytes are materialized for enforcement, so binding identity and
  policy evaluation use the same snapshot;
- policy, receipt, and handoff digests use fixed canonical JSON plus SHA-256;
- envelope, output, receipt, and handoff identity, hash, decision, reason,
  context, and receipt-profile links are checked before a binding is returned;
- output and handoff context hashes must equal the canonical envelope hash;
- a genuine policy denial binds the actual validated envelope evaluated for
  that operation and uses its canonical hash as the rejected output context;
- a pre-policy, manifest-capability, adapter, backend, chain, hashing, or
  builder failure returns a rejected output with receipt, handoff, and policy
  binding all absent;
- a missing, blank, non-string, or undeclared action cannot bypass manifest or
  policy action allowlists and receives no bound evidence;
- the frozen `process_governed(...)` result remains unbound and unchanged;
- the V1 from-result helper rejects a present `policy_binding` key and directs
  callers to `ADAMANTINE_AI_GATEWAY_EVIDENCE_V2`; it cannot detect prior key
  removal or direct V1-builder use, so D3 must require V2 and prohibit fallback
  wherever exact policy identity is required.

This is producer-side deterministic content linkage, not authentication,
source provenance, freshness, replay protection, remote attestation, proof of
honest execution, or authority. The independent AdamantineOS expected-policy
consumer remains V4.9-D3 work.

---

## 4. Manifest runtime-binding invariants

Manifest existence alone is not enough.
The manifest must actively constrain runtime behavior.

### Required invariant

In governed mode, the manifest is part of enforcement, not metadata.

### Required locks

- no governed registration without manifest
- manifest identity must match adapter identity exactly
- manifest cannot be mutated after registration
- declared capabilities must constrain allowed actions
- undeclared action attempts must fail closed
- undeclared adapter behavior must fail closed
- production registration path and test/legacy registration path must be clearly separated if both exist

### Required proof

- tests for missing manifest rejection
- tests for manifest mismatch rejection
- tests for post-registration mutation protection
- tests for capability-bound action acceptance / rejection

---

## 5. Canonical governed-path invariant

### Required invariant

`v1.0.0` must have one canonical, stable, documented governed processing flow.

### Canonical flow

1. adapter registered in governed mode
2. manifest validated and bound
3. input boundary validation applied
4. adapter action/capability checked against manifest
5. policy pack validated and evaluated
6. adapter execution occurs under deterministic rules
7. output validated
8. receipt built
9. handoff built
10. governed result returned

### V4.9-D2 policy-bound extension flow

1. exact bounded PolicyPack V1 captured before callbacks
2. manifest loaded and adapter envelope captured as exact built-in JSON
3. the captured policy snapshot evaluated against that envelope
4. genuine policy denial retains the evaluated envelope; pre-policy failure is
   not bindable
5. accepted adapter output captured and validated
6. receipt and handoff built
7. full chain, reason semantics, context, and fixed receipt profile checked
8. separate policy-binding artifact built
9. exact four-key result returned atomically

### Required locks

- compatibility helpers may exist, but they must not blur the official governed path
- governed success without receipt must be impossible
- governed success without valid handoff must be impossible
- governed success without policy evaluation must be impossible
- governed success without manifest binding must be impossible

### Required proof

- one end-to-end governed-path test asserting exact sequence invariants
- failure tests proving each missing stage fails closed
- README example matching real code path exactly

---

## 6. Determinism lock

Determinism must be proven, not claimed.

### Required invariant

The governed path must not depend on time, randomness, hidden global state, unordered serialization, or network behavior.

### Required locks

- canonical serialization rules fixed and documented
- repeated identical inputs produce byte-stable artifacts where expected
- hash inputs are canonicalized deterministically
- no hidden entropy source may influence governed output
- fixture outputs remain stable across runs

### Required proof

- repeated-run determinism tests
- canonical hashing regression fixtures
- cross-object equivalence tests for re-ordered but semantically equivalent input
- explicit tests for rejection of non-deterministic or unsupported structures if applicable
- committed fixtures stored in repo and treated as release locks

---

## 7. Reason ID completeness lock

Reason IDs are boundary API, not internal decoration.

### Required invariant

Every fail-closed boundary rejection path must map to a stable, registered `reason_id`.

### Required locks

- no free-form string reason paths for governed boundary failures
- reason meanings documented clearly
- reason IDs treated as stable downstream integration surface
- additions require docs/tests/changelog alignment
- orphaned or unreachable reason IDs must not accumulate silently

### Required proof

- registry completeness test covering all exported reason IDs
- tests that main fail-closed paths produce exact reason IDs
- docs-to-code consistency test for registered reason IDs if feasible

---

## 8. Abuse-suite lock

Security posture must be negative-first.

### Required invariant

`v1.0.0` is not complete unless hostile and malformed inputs are intentionally covered.

### Minimum abuse classes

- malformed manifest
- malformed receipt
- malformed policy pack
- malformed handoff
- contract mismatch chain
- oversized payload
- deeply nested payload
- undeclared wallet action attempt
- undeclared adapter capability attempt
- tampered evidence chain attempt
- invalid canonicalization edge cases
- boundary bypass attempts through helper paths

### Required proof

- abuse tests organized clearly as first-class suite coverage
- each abuse class mapped to deterministic rejection expectation
- coverage remains 100% after abuse hardening

---

## 9. Package-install reality lock

A boundary product is not release-ready if it only works in source-tree assumptions.

### Required invariant

The package must work from installation reality, not only local import accidents.

### Required locks

- CI must install package before test execution in at least one path
- package version truth must align across code / metadata / docs / changelog
- public imports must work after installation
- no reliance on implicit working-directory import behavior

### Required proof

- install-and-test CI path
- import smoke tests from installed package context
- version truth alignment tests if not already present

---

## 10. Adapter behavior freeze

A frozen boundary cannot have fuzzy adapter semantics.

### Required invariant

Official adapter set and action space must be explicit at `v1.0.0`.

### Minimum freeze target

- PoI adapter frozen
- Wallet adapter frozen
- wallet action space frozen
- adapter capabilities declared and enforced
- new adapters after `v1.0.0` require explicit manifest/action review

### Required proof

- adapter behavior matrix tests
- declared capability vs supported action tests
- rejection tests for undeclared or unsupported actions

---

## 11. Integration-ready downstream profile

`v1.0.0` must be usable by downstream systems without guesswork.

### Required invariant

Downstream consumers must know exactly what is stable and what they can trust.

### Required locks

- README must show canonical governed flow
- handoff consumption example must exist
- downstream integration notes must explicitly reference AdamantineOS compatibility expectations
- boundary responsibility must be stated clearly: gateway validates and packages evidence, but does not make final AdamantineOS decisions
- frozen components must be declared in release notes

### Required proof

- docs example that matches real tested flow
- integration example or example fixture bundle checked into repo
- the V1 from-result helper refuses a present policy-binding key; because it
  cannot detect prior removal or direct V1-builder use, the D3 consumer must
  require V2 and prohibit fallback when exact policy identity is required
- AdamantineOS verifier-controlled expected-policy comparison remains a
  separate consumer responsibility and is not claimed complete by D2

---

## 12. Version-truth lock

Release truth must not drift.

### Required invariant

Version, freeze state, and stable boundary claims must be aligned everywhere.

### Required locks

- package version
- changelog release entry
- README milestone language
- contract docs freeze language
- tag/release notes

### Required proof

- release checklist or test-backed assertions where practical
- no `v1.0.0` tag unless docs and version truth are aligned

---

## Explicit non-goals for v1.0.0

The following are **not** required for `v1.0.0` unless already planned elsewhere:

- adding many new adapters
- adding dynamic policy discovery from networked sources
- expanding gateway into final decision engine behavior
- coupling gateway directly to AdamantineOS internal decision authority
- optional convenience paths that weaken governed boundary discipline

`v1.0.0` should prioritize **seal and proof**, not surface expansion.

---

## v1.0.0 exit criteria

Do **not** tag `v1.0.0` unless all are true:

- public API surface is frozen and tested
- all public contracts are frozen and regression-locked
- artifact chain invariants are tested
- manifests are runtime-binding in governed mode
- one canonical governed path is documented and tested
- determinism fixtures are committed and stable
- reason IDs are frozen and complete for fail-closed paths
- abuse suite is explicit and green
- package-install reality is proven in CI
- adapter behavior matrix is frozen and green
- integration-ready downstream example exists
- version truth is aligned everywhere
- 100% coverage still holds

---

## Recommended first build step

### Step 1

**Lock package-install reality and public API freeze before deeper refactors.**

Why this should be first:

- it is small enough to do safely in one step
- it protects against “works only in source tree” mistakes
- it freezes the public boundary before deeper internals change
- it supports all later `v1.0.0` proof work

### Step 1 exact scope

- add install-based CI proof if missing
- add public API exact-export test
- add installed-package smoke import test
- add version truth assertions if needed
- keep 100% coverage green

### Step 1 done definition

- repo installs cleanly
- public exports are locked
- tests prove installed imports work
- no coverage regression

---

## Recommended sequencing after Step 1

1. package-install reality + API freeze
2. artifact-chain invariant tests
3. manifest runtime-binding hardening
4. canonical governed-path lock
5. determinism regression fixtures
6. reason ID completeness lock
7. abuse-suite expansion and final freeze docs

---

## Final build posture

Build `v1.0.0` like a sealed wall.

No soft edges.  
No optional truth.  
No hidden assumptions.  
No “close enough” release logic.  

The gateway should leave `v1.0.0` as a deterministic product boundary that downstream systems can rely on without guessing.

---

**MIT — DarekDGB**
