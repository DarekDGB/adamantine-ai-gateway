from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
from types import ModuleType
from typing import Any

import pytest

from ai_gateway.canonical import (
    AI_GATEWAY_CANONICAL_JSON_V1,
    canonical_json_bytes,
)
from ai_gateway.errors import ValidationError
from ai_gateway.policy_binding import (
    MAX_POLICY_SNAPSHOT_CANONICAL_BYTES,
    _PreflightBudget,
    _preflight_exact_json,
)
from ai_gateway.reason_ids import ReasonID


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "tools" / "check_ai_gateway_canonical_json_v1.py"
CANONICAL_CONTRACT_PATH = REPO_ROOT / "contracts" / "AI_GATEWAY_CANONICAL_JSON_V1.md"
FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "canonical"
    / "ai_gateway_canonical_json_v1_vectors.json"
)
DIFFERENTIAL_FUZZ_SEEDS = (0xD3A00001, 0xD3A51A7E, 0x49D3A202, 0xC0DEC0DE)
DIFFERENTIAL_CASES_PER_SEED = 1_000
FIXTURE_SHA256 = "b14b240cd3f0bd5c9c8e7a55698a92609bcbf5ebb19dfe913514dad8802b4733"
EXPECTED_VECTOR_IDS = {
    "golden_vectors": (
        "null",
        "false",
        "true",
        "zero",
        "one",
        "negative-one",
        "ascii-key-order",
        "empty-key",
        "empty-values-and-nesting",
        "quote",
        "backslash",
        "raw-solidus",
        "short-controls",
        "other-controls-lowercase-hex",
        "del-u007f",
        "c1-u0080-u009f",
        "raw-non-ascii",
        "raw-line-separators",
        "astral-value",
        "astral-key",
        "bmp-before-astral-key-order",
        "nfc-e-acute",
        "nfd-e-acute",
        "array-order",
    ),
    "equivalence_pairs": (
        "object-order",
        "solidus-escape",
        "newline-short-vs-unicode",
        "tab-short-vs-unicode",
        "bmp-raw-vs-unicode",
        "astral-raw-vs-surrogate-pair",
        "insignificant-wire-whitespace",
        "negative-zero-integer",
    ),
    "injective_pairs": (
        "true-vs-one",
        "false-vs-zero",
        "nfc-vs-nfd",
        "array-order",
        "empty-array-vs-object",
        "empty-string-vs-null",
        "del-scalar-vs-six-literal-characters",
        "empty-key-vs-nonempty-key",
        "astral-vs-bmp",
        "nested-empty-shapes",
    ),
    "rejected_wire_vectors": (
        "duplicate-top-level",
        "duplicate-nested",
        "duplicate-after-escape-decoding",
        "float-zero",
        "negative-float-zero",
        "float-exponent",
        "nan",
        "infinity",
        "negative-infinity",
        "lone-high-surrogate",
        "lone-low-surrogate",
        "invalid-utf8",
        "utf8-bom",
        "trailing-second-value",
        "plus-integer",
        "leading-zero-integer",
        "unescaped-line-feed",
    ),
    "boundary_vectors": (
        "positive-4096-bit",
        "negative-4096-bit",
        "positive-4097-bit",
        "string-10000-astral-scalars",
        "string-10001-astral-scalars",
        "key-10000-astral-scalars",
        "key-10001-astral-scalars",
        "depth-10",
        "depth-11",
        "array-1000-items",
        "array-1001-items",
        "object-1000-keys",
        "object-1001-keys",
        "nodes-20000",
        "nodes-20001",
        "canonical-bytes-1048576",
        "canonical-bytes-1048577",
    ),
}


def _load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "ai_gateway_canonical_json_v1_independent_checker",
        CHECKER_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKER = _load_checker()


def _fixture() -> dict[str, Any]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="ascii"))
    assert type(value) is dict
    return value


def _case_value(case: dict[str, Any], *, prefix: str = "") -> Any:
    value_field = f"{prefix}value"
    wire_field = f"{prefix}wire_utf8_hex"
    if value_field in case:
        return case[value_field]
    return CHECKER.strict_json_loads(bytes.fromhex(case[wire_field]))


def _governed_canonical_bytes(value: Any) -> bytes:
    _preflight_exact_json(
        value,
        depth=0,
        active_containers=set(),
        budget=_PreflightBudget(),
    )
    encoded = canonical_json_bytes(value)
    if len(encoded) > MAX_POLICY_SNAPSHOT_CANONICAL_BYTES:
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)
    return encoded


def test_profile_identifier_is_exact_and_fixture_is_ascii_literal_data() -> None:
    fixture_bytes = FIXTURE_PATH.read_bytes()
    fixture = _fixture()

    assert AI_GATEWAY_CANONICAL_JSON_V1 == "ai_gateway_canonical_json_v1"
    assert fixture["profile"] == AI_GATEWAY_CANONICAL_JSON_V1
    assert fixture["hash_algorithm"] == "sha256"
    assert fixture_bytes.isascii()
    assert hashlib.sha256(fixture_bytes).hexdigest() == FIXTURE_SHA256
    assert CHECKER.FIXTURE_SHA256 == FIXTURE_SHA256
    inventory = fixture["required_vector_ids"]
    assert type(inventory) is dict
    assert tuple(inventory) == CHECKER.VECTOR_SECTIONS
    for section, expected_ids in EXPECTED_VECTOR_IDS.items():
        cases = fixture[section]
        actual_ids = [case["id"] for case in cases]
        declared_ids = inventory[section]
        assert declared_ids == actual_ids
        assert len(declared_ids) == len(expected_ids)
        assert tuple(declared_ids) == expected_ids

    contract = CANONICAL_CONTRACT_PATH.read_text(encoding="ascii")
    assert f"Frozen fixture SHA-256: `{FIXTURE_SHA256}`" in contract
    assert FIXTURE_SHA256 not in fixture_bytes.decode("ascii")


def test_standalone_checker_imports_no_gateway_code_and_uses_no_json_dumps() -> None:
    source = CHECKER_PATH.read_text(encoding="ascii")
    tree = ast.parse(source)

    imported_modules = set()
    json_dumps_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "json"
            and node.func.attr == "dumps"
        ):
            json_dumps_calls.append(node)

    assert not any(name == "ai_gateway" or name.startswith("ai_gateway.") for name in imported_modules)
    assert json_dumps_calls == []


def test_standalone_checker_cli_validates_literal_fixture_in_isolated_mode() -> None:
    completed = subprocess.run(
        [sys.executable, "-I", str(CHECKER_PATH), str(FIXTURE_PATH)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert completed.stdout.strip() == (
        "PASS profile=ai_gateway_canonical_json_v1 "
        "golden=24 equivalence=8 injective=10 rejected=17 boundary=17"
    )


def test_fixture_checker_rejects_inventory_duplicate_ids_and_nonlowercase_hex() -> None:
    duplicate_fixture = _fixture()
    duplicate_fixture["golden_vectors"] = list(duplicate_fixture["golden_vectors"])
    duplicate_fixture["golden_vectors"][1] = duplicate_fixture["golden_vectors"][0]
    with pytest.raises(CHECKER.CanonicalProfileError, match="duplicate case ID"):
        CHECKER.check_fixture(duplicate_fixture)

    truncated_vectors = _fixture()
    truncated_vectors["golden_vectors"] = truncated_vectors["golden_vectors"][:-1]
    with pytest.raises(CHECKER.CanonicalProfileError, match="vector inventory mismatch"):
        CHECKER.check_fixture(truncated_vectors)

    truncated_inventory = _fixture()
    truncated_inventory["required_vector_ids"] = dict(
        truncated_inventory["required_vector_ids"]
    )
    truncated_inventory["required_vector_ids"]["golden_vectors"] = (
        truncated_inventory["required_vector_ids"]["golden_vectors"][:-1]
    )
    with pytest.raises(CHECKER.CanonicalProfileError, match="vector inventory mismatch"):
        CHECKER.check_fixture(truncated_inventory)

    reordered_inventory = _fixture()
    reordered_inventory["required_vector_ids"] = dict(
        reordered_inventory["required_vector_ids"]
    )
    reordered_ids = list(reordered_inventory["required_vector_ids"]["golden_vectors"])
    reordered_ids[0], reordered_ids[1] = reordered_ids[1], reordered_ids[0]
    reordered_inventory["required_vector_ids"]["golden_vectors"] = reordered_ids
    with pytest.raises(CHECKER.CanonicalProfileError, match="vector inventory mismatch"):
        CHECKER.check_fixture(reordered_inventory)

    missing_section = _fixture()
    missing_section["required_vector_ids"] = dict(missing_section["required_vector_ids"])
    missing_section["required_vector_ids"].pop("boundary_vectors")
    with pytest.raises(CHECKER.CanonicalProfileError, match="wrong sections"):
        CHECKER.check_fixture(missing_section)

    unexpected_section = _fixture()
    unexpected_section["required_vector_ids"] = dict(
        unexpected_section["required_vector_ids"]
    )
    unexpected_section["required_vector_ids"]["unexpected"] = []
    with pytest.raises(CHECKER.CanonicalProfileError, match="wrong sections"):
        CHECKER.check_fixture(unexpected_section)

    duplicate_inventory = _fixture()
    duplicate_inventory["required_vector_ids"] = dict(
        duplicate_inventory["required_vector_ids"]
    )
    duplicate_ids = list(duplicate_inventory["required_vector_ids"]["golden_vectors"])
    duplicate_ids[1] = duplicate_ids[0]
    duplicate_inventory["required_vector_ids"]["golden_vectors"] = duplicate_ids
    with pytest.raises(CHECKER.CanonicalProfileError, match="duplicate declared case ID"):
        CHECKER.check_fixture(duplicate_inventory)

    uppercase_fixture = _fixture()
    uppercase_fixture["golden_vectors"] = list(uppercase_fixture["golden_vectors"])
    uppercase_case = dict(uppercase_fixture["golden_vectors"][0])
    uppercase_case["expected_canonical_utf8_hex"] = "6E756C6C"
    uppercase_fixture["golden_vectors"][0] = uppercase_case
    with pytest.raises(CHECKER.CanonicalProfileError, match="contiguous lowercase hex"):
        CHECKER.check_fixture(uppercase_fixture)


def test_literal_golden_equivalence_and_injective_vectors_match_production_bytes() -> None:
    fixture = _fixture()

    for case in fixture["golden_vectors"]:
        expected = bytes.fromhex(case["expected_canonical_utf8_hex"])
        actual = canonical_json_bytes(_case_value(case))
        assert actual == expected, case["id"]
        assert hashlib.sha256(actual).hexdigest() == case["expected_sha256"]

    for case in fixture["equivalence_pairs"]:
        expected = bytes.fromhex(case["expected_canonical_utf8_hex"])
        left = canonical_json_bytes(_case_value(case, prefix="left_"))
        right = canonical_json_bytes(_case_value(case, prefix="right_"))
        assert left == expected, case["id"]
        assert right == expected, case["id"]
        assert hashlib.sha256(left).hexdigest() == case["expected_sha256"]

    for case in fixture["injective_pairs"]:
        left_expected = bytes.fromhex(case["left_expected_canonical_utf8_hex"])
        right_expected = bytes.fromhex(case["right_expected_canonical_utf8_hex"])
        left = canonical_json_bytes(_case_value(case, prefix="left_"))
        right = canonical_json_bytes(_case_value(case, prefix="right_"))
        assert left == left_expected, case["id"]
        assert right == right_expected, case["id"]
        assert left != right, case["id"]
        assert hashlib.sha256(left).hexdigest() == case["left_expected_sha256"]
        assert hashlib.sha256(right).hexdigest() == case["right_expected_sha256"]


def test_strict_wire_rejections_include_duplicate_decoded_keys_and_invalid_numbers() -> None:
    for case in _fixture()["rejected_wire_vectors"]:
        raw = bytes.fromhex(case["wire_utf8_hex"])
        with pytest.raises(CHECKER.CanonicalProfileError):
            CHECKER.strict_json_loads(raw)


def test_exact_governed_boundary_vectors_match_independent_checker() -> None:
    for case in _fixture()["boundary_vectors"]:
        value = CHECKER.build_boundary_value(case)
        if case["expected"] == "reject":
            with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
                _governed_canonical_bytes(value)
            with pytest.raises(CHECKER.CanonicalProfileError):
                CHECKER.governed_canonical_profile_bytes(value)
            continue

        actual = _governed_canonical_bytes(value)
        independent = CHECKER.governed_canonical_profile_bytes(value)
        assert actual == independent, case["id"]
        assert len(actual) == case["expected_canonical_byte_length"]
        assert hashlib.sha256(actual).hexdigest() == case["expected_sha256"]


def test_closed_integer_bytes_are_separate_from_d2_governed_limit() -> None:
    value = 1 << 4096

    assert canonical_json_bytes(value) == CHECKER.canonical_profile_bytes(value)
    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        _governed_canonical_bytes(value)
    with pytest.raises(CHECKER.CanonicalProfileError, match="integer width exceeded"):
        CHECKER.governed_canonical_profile_bytes(value)


_STRING_TOKENS = (
    "",
    "a",
    '"',
    "\\",
    "/",
    "\b",
    "\t",
    "\n",
    "\f",
    "\r",
    chr(0x00),
    chr(0x1B),
    chr(0x1F),
    chr(0x7F),
    chr(0x80),
    chr(0x9F),
    chr(0xE9),
    "e" + chr(0x301),
    chr(0xE000),
    chr(0x10000),
    chr(0x1F600),
    chr(0x2028),
    chr(0x2029),
)


def _random_string(rng: random.Random) -> str:
    return "".join(rng.choice(_STRING_TOKENS) for _ in range(rng.randrange(0, 8)))


def _random_integer(rng: random.Random) -> int:
    bits = rng.choice((0, 1, 7, 8, 31, 32, 63, 64, 255, 256, 4095, 4096))
    if bits == 0:
        return 0
    value = rng.getrandbits(bits - 1) | (1 << (bits - 1))
    return -value if rng.randrange(2) else value


def _random_scalar(rng: random.Random) -> Any:
    kind = rng.randrange(5)
    if kind == 0:
        return None
    if kind == 1:
        return bool(rng.randrange(2))
    if kind == 2:
        return _random_integer(rng)
    return _random_string(rng)


def _random_value(rng: random.Random, *, depth: int = 0) -> Any:
    if depth >= 4 or rng.randrange(4) == 0:
        return _random_scalar(rng)
    kind = rng.randrange(3)
    if kind == 0:
        return _random_scalar(rng)
    if kind == 1:
        return [_random_value(rng, depth=depth + 1) for _ in range(rng.randrange(6))]

    result: dict[str, Any] = {}
    target = rng.randrange(6)
    while len(result) < target:
        result[_random_string(rng)] = _random_value(rng, depth=depth + 1)
    return result


def test_seeded_differential_fuzz_compares_bytes_before_hashes() -> None:
    for seed in DIFFERENTIAL_FUZZ_SEEDS:
        rng = random.Random(seed)
        for case_index in range(DIFFERENTIAL_CASES_PER_SEED):
            value = _random_value(rng)
            production = canonical_json_bytes(value)
            independent = CHECKER.canonical_profile_bytes(value)
            assert production == independent, (
                f"seed={seed} case={case_index} value={value!r}"
            )
            assert hashlib.sha256(production).digest() == hashlib.sha256(independent).digest()
