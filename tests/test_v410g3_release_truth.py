"""V4.10-G3 release-truth locks. Author attribution: DarekDGB."""

from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import re
import tomllib

from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.adapters.wallet import WalletAdapter
from ai_gateway.integration.adamantine import (
    ADAMANTINE_AI_GATEWAY_EVIDENCE_V1,
    ADAMANTINE_AI_GATEWAY_EVIDENCE_V2,
    ADAMANTINE_AI_GATEWAY_SOURCE,
    ADAMANTINE_EVIDENCE_ROLE,
)
from ai_gateway.version import __version__


ROOT = Path(__file__).resolve().parents[1]
STATUS = "docs/RELEASE_STATUS_V4_10_G3.md"
COPY_FILES = (
    "README.md",
    "CHANGELOG.md",
    STATUS,
    "tests/test_v410g3_release_truth.py",
)
FROZEN_FILES = {
    "pyproject.toml": "c70759a3946d3c80e4f6d9e014e8b3d4cb26005f3eb1fc98cee626f60934f71c",
    ".github/workflows/ci.yml": "8b38b72ec9e6272f7e72df79465612e81a605a27f27eb086b933a0ec3be9ca2e",
    "LICENSE": "af36f33649d5faeed87733d851ae043502a23072ec1100ef6794cf53cce8d159",
    "tests/fixtures/adamantine/ai_gateway_adamantine_evidence_v1.json": "c78eb6657bc7f2b3160839a56f3a18077119e0663c910078238ac518c70f2470",
    "tests/fixtures/adamantine/ai_gateway_adamantine_evidence_v2.json": "deaa523cd28a1f8d2a97dbf681bfbc94ee7b682aa62d5c3c5747fbe244e13843",
    "tests/fixtures/canonical/ai_gateway_canonical_json_v1_vectors.json": "b14b240cd3f0bd5c9c8e7a55698a92609bcbf5ebb19dfe913514dad8802b4733",
}


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_g3_version_decision_distinguishes_tag_runtime_and_unreleased_work() -> None:
    project = tomllib.loads(_read("pyproject.toml"))["project"]
    assert project["name"] == "adamantine-ai-gateway"
    assert project["version"] == __version__ == version(project["name"]) == "1.0.0"
    assert project["authors"] == [{"name": "DarekDGB"}]
    assert PoIAdapter().manifest["adapter_version"] == "0.3.0"
    assert WalletAdapter().manifest["adapter_version"] == "0.3.0"
    for name in ("README.md", STATUS):
        text = " ".join(_read(name).split())
        for phrase in (
            "597db130a67ea366b052afac4e2b822ef3c03a7d",
            "42d8866dde3eee01552cc68d59b371d959c2c8e1",
            "unreleased",
            "distribution release number remains unassigned",
            "tag creation",
            "tag movement",
        ):
            assert phrase in text, (name, phrase)
    assert "## [Unreleased]" in _read("CHANGELOG.md")
    assert "## [v1.0.0] - 2026-04-07" in _read("CHANGELOG.md")
    assert "V4.10-G3 release truth" in _read("CHANGELOG.md")


def test_g3_frozen_runtime_contracts_metadata_workflow_and_fixtures() -> None:
    for name, expected in FROZEN_FILES.items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    for directory, pattern, count, expected in (
        ("ai_gateway", "*.py", 29, "781c646ea2918e42a814a131ae6434dae8704858797ecaeac73114c106ec3ab7"),
        ("contracts", "*.md", 11, "a9c2cec1b5a84bb307f34110af9de633372d682129454349b9ebb0e3314933b3"),
    ):
        paths = sorted((ROOT / directory).rglob(pattern))
        assert len(paths) == count
        manifest = "".join(
            f"{sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}\n"
            for path in paths
        )
        assert sha256(manifest.encode("ascii")).hexdigest() == expected, directory


def test_g3_v1_v2_identity_and_non_authority_claims_remain_separate() -> None:
    v1 = json.loads(_read("tests/fixtures/adamantine/ai_gateway_adamantine_evidence_v1.json"))
    v2 = json.loads(_read("tests/fixtures/adamantine/ai_gateway_adamantine_evidence_v2.json"))
    fields = {"evidence_version", "source", "evidence_role", "expected_context_hash", "handoff", "receipt"}
    assert set(v1) == fields
    assert set(v2) == fields | {"policy_binding"}
    assert v1["evidence_version"] == ADAMANTINE_AI_GATEWAY_EVIDENCE_V1 == "adamantine_ai_gateway_evidence_v1"
    assert v2["evidence_version"] == ADAMANTINE_AI_GATEWAY_EVIDENCE_V2 == "adamantine_ai_gateway_evidence_v2"
    for fixture in (v1, v2):
        assert fixture["source"] == ADAMANTINE_AI_GATEWAY_SOURCE == "adamantine-ai-gateway"
        assert fixture["evidence_role"] == ADAMANTINE_EVIDENCE_ROLE == "evidence_only"
        assert fixture["receipt"]["gateway_version"] == "1.0.0"
        assert fixture["receipt"]["determinism_profile"] == "canonical_sha256_no_time_v1"
    status = " ".join(_read(STATUS).split())
    for phrase in (
        "policy-identity unbound",
        "V2 with no V1 fallback",
        "exact bounded built-in dictionary",
        "does not verify Shield signatures",
        "verifier-controlled trusted local configuration",
        "deterministic declared-content linkage only",
        "`final_approval == false`",
        "producer authentication, source provenance, freshness, replay protection",
        "independent final fail-closed policy and execution boundary",
        "not Rust or SDK compatibility",
    ):
        assert phrase in status, phrase


def test_g3_standard_gate_and_candidate_counts_are_explicit() -> None:
    workflows = {p.name for p in (ROOT / ".github/workflows").iterdir() if p.is_file()}
    assert workflows == {"ci.yml"}
    config = tomllib.loads(_read("pyproject.toml"))["tool"]["coverage"]
    assert config["run"]["branch"] is True
    assert config["report"]["fail_under"] == 100
    ci = _read(".github/workflows/ci.yml")
    assert 'python-version: "3.11"' in ci
    assert "pytest --cov=ai_gateway --cov-report=term-missing --cov-fail-under=100" in ci
    assert "workflow_dispatch" not in ci
    for name in ("README.md", STATUS):
        text = " ".join(_read(name).split())
        for phrase in ("413", "419", "1117/1117", "394/394", "CPython 3.11.15", "post-commit ZIP"):
            assert phrase in text, (name, phrase)
    assert "exact-commit CI and fresh-ZIP gate pending" in _read(STATUS)
    assert "There is no native-OQS workflow to run for Gateway." in _read(STATUS)


def test_g3_documentation_links_resolve_inside_the_repository() -> None:
    for name in ("README.md", "CHANGELOG.md", STATUS):
        for target in re.findall(r"\]\(([^)]+)\)", _read(name)):
            if target.startswith(("https://", "http://", "#")):
                continue
            path = ((ROOT / name).parent / target.split("#", 1)[0]).resolve()
            assert path.is_relative_to(ROOT.resolve()), (name, target)
            assert path.is_file(), (name, target)


def test_g3_copy_files_are_ascii_lf_and_darekdgb_only() -> None:
    allowed = {"Author attribution: DarekDGB", "MIT - DarekDGB", "MIT License (c) DarekDGB"}
    for name in COPY_FILES:
        raw = (ROOT / name).read_bytes()
        assert raw and raw.isascii() and raw.endswith(b"\n"), name
        assert all(byte in (9, 10) or 32 <= byte <= 126 for byte in raw), name
        assert all(line == line.rstrip(b" \t") for line in raw.splitlines()), name
        text = raw.decode("ascii")
        for alternate in ("anth" + "ropic", "chat" + "gpt", "clau" + "de", "open" + "ai"):
            assert alternate not in text.lower(), name
        for line in text.splitlines():
            normalized = line.strip().replace("**", "")
            if normalized.lower().startswith(("author:", "author attribution:", "owner attribution:", "copyright", "mit -", "mit license (c)")):
                assert normalized in allowed, (name, normalized)
    assert "Author attribution: **DarekDGB**" in _read(STATUS)
