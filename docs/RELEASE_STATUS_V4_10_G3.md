# AI Gateway V4.10-G3 Release Truth

Author attribution: **DarekDGB**

Status: G3 candidate prepared; exact-commit CI and fresh-ZIP gate pending.
Scope: documentation and regression tests only; not a new distribution release.

## 1. Authenticated source and independent release decision

Source archive: `adamantine-ai-gateway-main(20260812-060640).zip`

```text
ZIP SHA-256: 6787d064f7751165f16526222c11c931c071d09e629bd434e92024ec288f8ef3
Commit: 42d8866dde3eee01552cc68d59b371d959c2c8e1
Git tree: e5cf9b2c27e44c487bef23c7ae205cc9aea09521
Existing v1.0.0 tag commit: 597db130a67ea366b052afac4e2b822ef3c03a7d
```

The saved source was reauthenticated against unchanged current main on
2026-09-09. That source is 65 commits ahead of the existing tag, with zero
commits behind it. Historical release entries remain historical; the later
V4.9-D2, V4.9-D3A, V4.9-E, and G3 changes remain unreleased.

Decision: retain package/runtime `1.0.0` for G3. The next independent
distribution release number remains unassigned. This is not a Shield `4.0.0`
package, a new release, or permission to republish the changed source under
the existing tag. No tag creation or tag movement is authorized.

This no-bump decision preserves the actual receipt `gateway_version` emitted
by `build_receipt_v1`, not just a display label. A later version bump needs
explicit review of receipt hashes, policy bindings, fixtures, downstream
expectations, and the already implemented exporter input tightening.

## 2. Version map and unchanged identities

| Surface | Exact identity or rule |
|---|---|
| Distribution `adamantine-ai-gateway` | `1.0.0` |
| Runtime `ai_gateway.version.__version__` | `1.0.0` |
| Receipt `gateway_version` | Runtime `1.0.0`, not a protocol version |
| Built-in PoI and Wallet adapter versions | `0.3.0`, independently versioned |
| Frozen V1 evidence | `adamantine_ai_gateway_evidence_v1`; policy-identity unbound |
| Policy-bound evidence V2 | `adamantine_ai_gateway_evidence_v2`; adds separate `policy_binding` |
| Policy-binding artifact | `ai_gateway_policy_binding_v1`; seven fields |
| Bound policy-pack contract | `policy_pack_v1` |
| Canonical byte profile | `ai_gateway_canonical_json_v1` |
| Receipt determinism profile | `canonical_sha256_no_time_v1` |
| Exported source / role | `adamantine-ai-gateway` / `evidence_only` |

All frozen V1 envelope, output, receipt, handoff, manifest, and PolicyPack
shapes remain unchanged. Policy binding is a separate versioned artifact,
not an added V1 receipt or handoff field. V1 has no policy-pack identity or
digest and cannot satisfy an exact-policy expectation.

The V1 from-result helper intentionally requires an exact bounded built-in
dictionary and rejects a present `policy_binding` key, including null. It
cannot detect a binding removed before the call or direct V1-builder use.
An exact-policy consumer must require V2 with no V1 fallback. Shape
preservation is not a claim of unchanged acceptance of every V1 caller input.

The two existing evidence fixtures and canonical-vector file are byte-locked:

```text
tests/fixtures/adamantine/ai_gateway_adamantine_evidence_v1.json
c78eb6657bc7f2b3160839a56f3a18077119e0663c910078238ac518c70f2470
tests/fixtures/adamantine/ai_gateway_adamantine_evidence_v2.json
deaa523cd28a1f8d2a97dbf681bfbc94ee7b682aa62d5c3c5747fbe244e13843
tests/fixtures/canonical/ai_gateway_canonical_json_v1_vectors.json
b14b240cd3f0bd5c9c8e7a55698a92609bcbf5ebb19dfe913514dad8802b4733
```

The V1 fixture's synthetic adapter version `1.0.0` is fixture data, not a
claim that the built-in adapters moved from `0.3.0`. No fixture is rewritten.

## 3. Security and authority boundary

Gateway validates its own contracts, enforces its own policy, and emits
Gateway-local evidence. Gateway does not verify Shield signatures, hold a
Shield trust registry or key role, or depend on OQS. Gateway-local `accepted`
and `policy_decision` values are not downstream approval or execution authority.

The separately verified AdamantineOS V2 consumer uses expected context,
policy ID, policy version, and complete policy hash from verifier-controlled
trusted local configuration. It accepts raw bytes, rejects duplicate decoded
keys, has no V1 fallback, keeps earlier denials dominant, and returns
evidence-only results with `final_approval == false`.

An unsigned V2 bundle proves deterministic declared-content linkage only.
It omits the source envelope, output, and policy snapshot. It does not prove
producer authentication, source provenance, freshness, replay protection,
remote attestation, honest execution, or possession or enforcement of the
declared policy snapshot. No signing, broadcast, consensus change, override,
bypass, rescue, or final execution authority is added. AdamantineOS remains
the independent final fail-closed policy and execution boundary.

Independent Python canonical-byte parity is not Rust or SDK compatibility,
Shield signature verification, or live-OQS proof. This step introduces no
new algorithm or standards claim.

See the unchanged [Shield compatibility boundary](reports/v4/SHIELD_V4_COMPATIBILITY.md),
[policy identity decision](reports/v4/POLICY_PACK_IDENTITY_DECISION.md), and
[integration contract](reports/v1/ADAMANTINEOS_INTEGRATION.md).

## 4. Verification evidence and required gate

| Snapshot | Passed | Skipped | Statements | Branches |
|---|---:|---:|---|---|
| Authenticated pre-G3 source | 413 | 0 | 1117/1117; 100% | 394/394; 100% |
| G3 candidate with six added regression tests | 419 | 0 | 1117/1117; 100% | 394/394; 100% |

Local evidence uses CPython 3.11.15 with an editable install, normal bytecode
writing, and ordinary pytest/coverage output. All tests pass without failures
or errors. The separate standard-library canonical-vector checker passes.
The existing full-repository UTF-8/C1/mojibake lock remains unchanged and green.
The new G3 transfer check scans only its four copy files, not generated caches,
bytecode, editable-install metadata, or coverage files.

The pre-G3 [CI run #197](https://github.com/DarekDGB/adamantine-ai-gateway/actions/runs/29781059560)
reports 413 passed and 100% statement/branch coverage on the authenticated
source commit. It is not post-G3 evidence.

After manually committing all four G3 files, require:

1. The existing `CI` workflow green on that exact final commit: 419 passed,
   zero skips/failures/errors, 100% statement and branch coverage.
2. A fresh post-commit ZIP verified against the copy-only package and unchanged
   source, including encoding, attribution, and all frozen bytes.

CI runs automatically for pushes and pull requests to `main`; it has no
manual-dispatch control. There is no native-OQS workflow to run for Gateway.
The workflow is unchanged: moving action tags, `ubuntu-latest`, Python `3.11`,
and ranged development dependencies remain V4.10-K reproducibility follow-up,
not a claim of an exact pinned future CI environment.

## 5. Exact copy scope

```text
NEW:
  docs/RELEASE_STATUS_V4_10_G3.md
  tests/test_v410g3_release_truth.py
REPLACE:
  README.md
  CHANGELOG.md
DELETE: none
```

Four ASCII-safe, LF-terminated payloads; 91 unrelated source files unchanged;
93 source files become 95 candidate files. No runtime, package metadata,
dependency, workflow, existing test, contract, fixture, or license file changes.
The existing adapter manifests are runtime contracts, not release inventories;
their bytes and all frozen hashes remain unchanged.

G3 remains prepared until the exact-commit CI and fresh-ZIP gate closes.
H-L remain not started; no release action is authorized by this document.

---

**MIT - DarekDGB**
