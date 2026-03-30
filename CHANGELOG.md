# Changelog

All notable changes to this project will be documented in this file.

The format follows a simple release log with explicit scope and locked boundary behavior.

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
