# Changelog

All notable changes to this project will be documented in this file.

The format follows a simple release log with explicit scope and locked boundary behavior.

---

## [v1.0.0] - 2026-04-07

### Added
- Public API freeze lock
- Version-truth lock across runtime, package metadata, and release files
- Artifact-chain invariant lock across manifest → envelope → output → receipt → handoff
- Stable reason-ID mapping lock
- Manifest `failure_reason_ids` completeness lock
- Built-in adapter manifest/runtime parity lock
- Governed manifest/runtime enforcement lock
- Receipt-path manifest/runtime enforcement parity lock
- Deterministic fallback artifact lock
- Release-truth / doc-contract parity lock
- Additional tests covering manifest/runtime edge cases and fallback determinism

### Changed
- Gateway hardening elevated from milestone release to locked release surface
- Manifest/runtime enforcement now applies consistently across governed and receipt-aware paths
- Receipt path now matches governed-path enforcement expectations
- Fallback artifact behavior is now tested as deterministic contract behavior
- Release files now reflect a coordinated v1.0.0 locked-state release

### Included in this release
- All functionality from v0.5.0
- Public API freeze
- Version truth guarantees
- Artifact-chain invariant guarantees
- Stable reason-ID semantics
- Manifest failure-reason completeness guarantees
- Built-in adapter manifest/runtime parity guarantees
- Governed manifest/runtime enforcement
- Receipt manifest/runtime enforcement parity
- Deterministic fallback artifact guarantees
- Release truth / doc-contract parity
- 100% test coverage enforced

### Release scope
This release establishes Adamantine AI Gateway as a locked deterministic enforcement boundary by freezing its public API, aligning manifests with runtime behavior, enforcing deterministic fail-closed artifact generation, and binding release documentation to the actual code and contract surface.

### v1.0.0 principles
- Untrusted input boundary
- Fail-closed always
- Contract-first
- Deterministic input/output only
- Strict schema, no unknown fields
- Canonical-safe payloads only
- Explicit adapter declaration via manifests
- Manifest/runtime parity required
- Deterministic evidence via receipts
- Deterministic decisions via handoff artifacts
- Explicit reason_id for all important failures
- No silent fallback
- Adapters translate, gateway verifies and enforces, AdamantineOS decides

---

## [v0.5.0] - 2026-03-31

### Added
- PolicyPack V1 contract (`POLICYPACK_V1.md`)
- Policy validation enforcing adapter-level governance rules
- Policy enforcement integration in gateway (`process_with_policy`)
- AI Gateway Handoff V1 contract (`AI_GATEWAY_HANDOFF_V1.md`)
- Deterministic handoff builder (`build_handoff_v1`)
- Governed gateway processing path (`process_governed`)
- Manifest-required execution mode (no manifest → fail-closed)
- Receipt-required execution mode (always produces evidence)
- Boundary input limits:
  - Maximum payload depth
  - Maximum dict key count
  - Maximum list size
  - Maximum string length
- Extended validation to enforce limits on both payload and contract fields
- Abuse and negative test suite covering:
  - malformed payloads
  - oversized inputs
  - invalid contract structures
  - policy violations
  - fallback paths

### Changed
- Gateway upgraded from validation boundary to enforcement + governance boundary
- Policy enforcement now occurs before output acceptance
- Gateway now produces deterministic handoff artifacts alongside output and receipt
- Validation layer extended to enforce structural limits and prevent resource abuse
- Fail-closed behavior strengthened across governed execution paths
- Receipt and handoff flows hardened with deterministic fallback guarantees
- Test suite expanded to cover governance paths, abuse cases, and boundary limits while maintaining 100% coverage

### Included in this release
- All functionality from v0.3.0
- `POLICYPACK_V1`
- Policy validation and enforcement layer
- `AI_GATEWAY_HANDOFF_V1`
- Deterministic handoff builder
- Governed processing path (`process_governed`)
- Manifest-required execution enforcement
- Receipt-required execution enforcement
- Boundary input limits enforcement
- Abuse/negative test suite
- Deterministic enforcement boundary behavior
- 100% test coverage enforced

### Release scope
This release transforms the Adamantine AI Gateway from a deterministic validation and evidence boundary into a deterministic enforcement and governance boundary by introducing policy packs, handoff artifacts, governed execution paths, and strict input limits while preserving fail-closed and contract-first guarantees.

### v0.5.0 principles
- Untrusted input boundary
- Fail-closed always
- Contract-first
- Deterministic input/output only
- Strict schema, no unknown fields
- Canonical-safe payloads only
- Explicit adapter declaration via manifests
- Deterministic evidence via receipts
- Deterministic decisions via handoff artifacts
- Policy-enforced execution
- No silent fallback
- Explicit reason_id for all failures
- Adapters translate, gateway verifies and enforces, AdamantineOS decides

---

## [v0.3.0] - 2026-03-30

### Added
- Adapter Manifest V1 contract (`ADAPTER_MANIFEST_V1.md`)
- AI Gateway Receipt V1 contract (`AI_GATEWAY_RECEIPT_V1.md`)
- Manifest validation enforcing explicit adapter declaration boundaries
- Receipt validation enforcing deterministic evidence structure
- Deterministic receipt builder (`build_receipt_v1`)
- Manifest-aware adapter registry with manifest storage and validation
- Gateway receipt processing path (`process_with_receipt`)
- Additional tests for manifest validation, receipt validation, registry behavior, and gateway receipt flow

### Changed
- Adapter layer extended from implicit behavior to explicit manifest-declared boundaries
- Registry upgraded from adapter-only storage to manifest-aware control layer
- Gateway extended to support deterministic evidence generation alongside output processing
- Validation layer expanded to include manifest and receipt contract enforcement
- Test suite expanded to cover manifest, receipt, and receipt-aware gateway behavior while maintaining 100% coverage

### Included in this release
- All functionality from v0.2.0
- `ADAPTER_MANIFEST_V1`
- `AI_GATEWAY_RECEIPT_V1`
- Manifest validation layer
- Receipt validation layer
- Deterministic receipt builder
- Manifest-aware registry
- Receipt-capable gateway processing path
- Deterministic evidence generation foundations
- 100% test coverage enforced

### Release scope
This release extends the Adamantine AI Gateway from a deterministic validation boundary into a deterministic evidence-producing boundary by introducing adapter manifests, receipt contracts, and receipt-capable gateway processing while preserving fail-closed and contract-first guarantees.

### v0.3.0 principles
- Untrusted input boundary
- Fail-closed always
- Contract-first
- Deterministic input/output only
- Strict schema, no unknown fields
- Canonical-safe payloads only
- Explicit adapter declaration via manifests
- Deterministic evidence via receipts
- Adapters translate, gateway verifies, AdamantineOS decides

---

## [v0.2.0] - 2026-03-30

### Added
- Wallet adapter as the second core adapter
- Typed gateway error hierarchy in `errors.py`
- Type-based fail-closed reason mapping in the gateway
- Strict schema enforcement rejecting unknown envelope and output fields
- Canonical payload validation for deterministic-safe data only
- Recursive payload validation across nested dict/list structures
- Additional fail-closed and reason-mapping tests
- Additional validation tests for strict and canonical input enforcement

### Changed
- Gateway error handling moved from message-based guessing to typed error handling
- Registry lookup and adapter execution are separated more cleanly in gateway processing
- Validation now enforces exact contract shape rather than allowing extra fields
- Payload validation now rejects non-deterministic or unsafe types such as floats and arbitrary objects

### Included in this release
- Existing contract-first gateway foundation from v0.1.0
- `AI_GATEWAY_ENVELOPE_V1`
- `AI_GATEWAY_OUTPUT_V1`
- Deterministic canonical JSON serialization
- SHA-256 hashing over canonical bytes
- Strict validation layer
- Explicit fail-closed gateway behavior
- Reason ID registry
- Allowlist policy model
- Adapter registry
- Base adapter contract
- Passive PoI adapter
- Wallet adapter
- Determinism rules
- GitHub Actions CI
- 100% test coverage enforced

### Release scope
This release hardens the Adamantine AI Gateway boundary from a minimal safe foundation into a stricter deterministic execution boundary by adding typed errors, wallet adapter support, exact schema enforcement, and canonical payload discipline before manifest and policy-pack expansion.

### v0.2.0 principles
- Untrusted input boundary
- Fail-closed always
- Contract-first
- Deterministic input/output only
- Strict schema, no unknown fields
- Canonical-safe payloads only
- Typed errors, no string-based guessing
- Adapters translate, gateway verifies, AdamantineOS decides

---

## [v0.1.0] - 2026-03-29

### Included in this release
- Contract-first AI boundary foundation
- `AI_GATEWAY_ENVELOPE_V1`
- `AI_GATEWAY_OUTPUT_V1`
- Deterministic canonical JSON serialization
- SHA-256 hashing over canonical bytes
- Strict validation layer
- Explicit fail-closed gateway behavior
- Reason ID registry
- Allowlist policy model
- Adapter registry
- Base adapter contract
- Passive PoI adapter
- Determinism rules
- Adapter contract
- GitHub Actions CI
- 100% test coverage enforced

### Release scope
This release establishes the minimal safe boundary for untrusted AI-originated work before downstream integration with Q-ID, Shield v3, Adaptive Core, and AdamantineOS.

### v0.1.0 principles
- Untrusted AI boundary
- Fail-closed always
- Contract-first
- Deterministic input/output only
- No raw AI output enters unchecked
- Adapters translate, gateway verifies, AdamantineOS decides
