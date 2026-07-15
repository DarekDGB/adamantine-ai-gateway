from importlib import import_module, metadata
from pathlib import Path
import tomllib

from ai_gateway import __all__ as root_public_api
from ai_gateway.version import __version__


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
CONTRACTS_DIR = REPO_ROOT / "contracts"


EXPECTED_CONTRACT_DOCS = {
    "ADAPTER_CONTRACT.md",
    "ADAMANTINE_AI_GATEWAY_EVIDENCE_V2.md",
    "ADAPTER_MANIFEST_V1.md",
    "AI_GATEWAY_ENVELOPE_V1.md",
    "AI_GATEWAY_HANDOFF_V1.md",
    "AI_GATEWAY_OUTPUT_V1.md",
    "AI_GATEWAY_RECEIPT_V1.md",
    "AI_GATEWAY_POLICY_BINDING_V1.md",
    "DETERMINISM_RULES.md",
    "POLICYPACK_V1.md",
}

EXPECTED_CODE_CONTRACT_EXPORTS = {
    "AI_GATEWAY_ENVELOPE_V1",
    "ADAPTER_MANIFEST_V1",
    "AI_GATEWAY_OUTPUT_V1",
    "POLICYPACK_V1",
    "AI_GATEWAY_HANDOFF_V1",
    "AI_GATEWAY_RECEIPT_V1",
    "AI_GATEWAY_POLICY_BINDING_V1",
}

EXPECTED_PUBLIC_API_SYMBOLS = {
    "__version__",
    "AIGateway",
    "AdapterRegistry",
    "build_receipt_v1",
}

EXPECTED_README_PHRASES = [
    "Fail-closed, contract-first gateway for untrusted AI-originated work.",
    "## System Diagram",
    "## v1.0.0 Highlights",
    "Artifact-chain invariants locked",
    "Receipt-path manifest/runtime enforcement parity locked",
    "Deterministic fallback artifacts locked",
    "process_governed",
    "## Unreleased V4.9-D2 Compatibility Extension",
    "process_governed_with_policy_binding_v1",
    "ADAMANTINE_AI_GATEWAY_EVIDENCE_V2",
    "deterministic content linkage only",
    "MIT License Â© DarekDGB",
]

EXPECTED_CHANGELOG_UNRELEASED_PHRASES = [
    "## [Unreleased]",
    "AI_GATEWAY_POLICY_BINDING_V1",
    "process_governed_with_policy_binding_v1",
    "ADAMANTINE_AI_GATEWAY_EVIDENCE_V2",
    "POLICY_BOUND_RESULT_REQUIRES_EVIDENCE_V2",
    "package version remains `1.0.0`",
]

EXPECTED_CHANGELOG_V1_0_0_PHRASES = [
    "## [v1.0.0] - 2026-04-07",
    "Public API freeze lock",
    "Artifact-chain invariant lock across manifest â envelope â output â receipt â handoff",
    "Receipt-path manifest/runtime enforcement parity lock",
    "Deterministic fallback artifact lock",
    "Release-truth / doc-contract parity lock",
    "100% test coverage enforced",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _pyproject_version() -> str:
    data = tomllib.loads(_read(PYPROJECT_PATH))
    return data["project"]["version"]


def test_runtime_version_matches_pyproject_and_installed_metadata() -> None:
    assert __version__ == "1.0.0"
    assert _pyproject_version() == __version__
    assert metadata.version("adamantine-ai-gateway") == __version__


def test_readme_and_changelog_match_current_release_version() -> None:
    readme = _read(README_PATH)
    changelog = _read(CHANGELOG_PATH)

    assert "## v1.0.0 Highlights" in readme
    assert "## Unreleased V4.9-D2 Compatibility Extension" in readme
    assert "## [Unreleased]" in changelog
    assert "## [v1.0.0] - 2026-04-07" in changelog


def test_readme_contains_current_release_truth_phrases() -> None:
    readme = _read(README_PATH)

    for phrase in EXPECTED_README_PHRASES:
        assert phrase in readme


def test_changelog_contains_current_release_truth_phrases() -> None:
    changelog = _read(CHANGELOG_PATH)

    for phrase in EXPECTED_CHANGELOG_V1_0_0_PHRASES:
        assert phrase in changelog
    for phrase in EXPECTED_CHANGELOG_UNRELEASED_PHRASES:
        assert phrase in changelog


def test_contract_docs_exist_for_current_runtime_contract_surface() -> None:
    docs = {path.name for path in CONTRACTS_DIR.iterdir() if path.is_file()}
    assert EXPECTED_CONTRACT_DOCS <= docs


def test_contracts_module_exports_match_documented_contract_surface() -> None:
    contracts_module = import_module("ai_gateway.contracts")
    exported = set(contracts_module.__all__)

    assert EXPECTED_CODE_CONTRACT_EXPORTS <= exported


def test_public_api_lock_file_and_runtime_surface_stay_aligned() -> None:
    assert set(root_public_api) == EXPECTED_PUBLIC_API_SYMBOLS


def test_readme_current_release_claims_are_backed_by_runtime_surface() -> None:
    readme = _read(README_PATH)

    assert "process_governed" in readme
    gateway_class = import_module("ai_gateway.gateway").AIGateway
    assert hasattr(gateway_class, "process_governed_with_policy_binding_v1")
    assert hasattr(import_module("ai_gateway.handoff"), "build_handoff_v1")
    assert hasattr(import_module("ai_gateway.receipt"), "build_receipt_v1")
    integration = import_module("ai_gateway.integration")
    assert hasattr(integration, "build_adamantine_ai_gateway_evidence_v2")
    assert hasattr(
        integration,
        "build_adamantine_ai_gateway_evidence_from_gateway_result_v2",
    )


def test_changelog_v1_0_0_claims_are_backed_by_files_present_in_repo() -> None:
    assert (CONTRACTS_DIR / "POLICYPACK_V1.md").exists()
    assert (CONTRACTS_DIR / "AI_GATEWAY_HANDOFF_V1.md").exists()
    assert (CONTRACTS_DIR / "AI_GATEWAY_POLICY_BINDING_V1.md").exists()
    assert (CONTRACTS_DIR / "ADAMANTINE_AI_GATEWAY_EVIDENCE_V2.md").exists()
    assert (REPO_ROOT / "ai_gateway" / "policy.py").exists()
    assert (REPO_ROOT / "ai_gateway" / "handoff.py").exists()


def test_release_truth_lock_is_strict_about_current_v1_state() -> None:
    readme = _read(README_PATH)
    changelog = _read(CHANGELOG_PATH)

    assert "package version `1.0.0`" in readme
    assert "deterministic policy-enforcement and evidence-production boundary" in readme
    assert "tests-223%20passed" not in readme
    assert "actions/workflows/ci.yml/badge.svg" in readme
    assert "This release establishes Adamantine AI Gateway as a locked deterministic enforcement boundary" in changelog
