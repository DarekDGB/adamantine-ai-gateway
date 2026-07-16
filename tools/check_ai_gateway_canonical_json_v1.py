#!/usr/bin/env python3
"""Independent checker for AI_GATEWAY_CANONICAL_JSON_V1.

This file is intentionally standard-library-only. It does not import the
Gateway serializer or hashing helper, and it does not use json.dumps.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


PROFILE_ID = "ai_gateway_canonical_json_v1"
FIXTURE_SHA256 = "b14b240cd3f0bd5c9c8e7a55698a92609bcbf5ebb19dfe913514dad8802b4733"
MAX_DEPTH = 10
MAX_KEYS = 1_000
MAX_LIST_ITEMS = 1_000
MAX_STRING_SCALARS = 10_000
MAX_INTEGER_BITS = 4_096
MAX_NODES = 20_000
MAX_CANONICAL_BYTES = 1_048_576
VECTOR_SECTIONS = (
    "golden_vectors",
    "equivalence_pairs",
    "injective_pairs",
    "rejected_wire_vectors",
    "boundary_vectors",
)


class CanonicalProfileError(ValueError):
    """The input or fixture violates the canonical profile."""


@dataclass
class _Budget:
    nodes: int = 0
    text_bytes: int = 0


def _reject_float(_value: str) -> Any:
    raise CanonicalProfileError("floating-point JSON numbers are prohibited")


def _reject_constant(_value: str) -> Any:
    raise CanonicalProfileError("non-standard JSON constants are prohibited")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise CanonicalProfileError("duplicate object key")
        value[key] = child
    return value


def strict_json_loads(raw: str | bytes) -> Any:
    """Parse one strict JSON value and reject duplicate decoded object keys."""

    if type(raw) is bytes:
        if raw.startswith(b"\xef\xbb\xbf"):
            raise CanonicalProfileError("UTF-8 BOM is prohibited")
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise CanonicalProfileError("invalid UTF-8") from exc
    elif type(raw) is str:
        text = raw
    else:
        raise CanonicalProfileError("raw JSON must be exact str or bytes")

    if text.startswith("\ufeff"):
        raise CanonicalProfileError("Unicode BOM is prohibited")

    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except CanonicalProfileError:
        raise
    except (TypeError, ValueError, UnicodeError) as exc:
        raise CanonicalProfileError("invalid strict JSON") from exc

    governed_canonical_profile_bytes(value)
    return value


def _validate_scalar_string(value: str) -> None:
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise CanonicalProfileError("surrogate code point is prohibited")


def _validate_governed_string(value: str) -> None:
    _validate_scalar_string(value)
    if len(value) > MAX_STRING_SCALARS:
        raise CanonicalProfileError("string exceeds Unicode scalar limit")


def _count_preflight_text(value: str, budget: _Budget) -> None:
    budget.text_bytes += len(value.encode("utf-8"))
    if budget.text_bytes > MAX_CANONICAL_BYTES:
        raise CanonicalProfileError("preflight text-byte budget exceeded")


def _encode_string(value: str) -> str:
    _validate_scalar_string(value)
    short_escapes = {
        0x08: "\\b",
        0x09: "\\t",
        0x0A: "\\n",
        0x0C: "\\f",
        0x0D: "\\r",
    }
    output = ['"']
    for character in value:
        codepoint = ord(character)
        if character == '"':
            output.append('\\"')
        elif character == "\\":
            output.append("\\\\")
        elif codepoint in short_escapes:
            output.append(short_escapes[codepoint])
        elif codepoint <= 0x1F:
            output.append(f"\\u{codepoint:04x}")
        else:
            output.append(character)
    output.append('"')
    return "".join(output)


def _encode_value(value: Any) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        return str(value)
    if type(value) is str:
        return _encode_string(value)
    if type(value) is list:
        return "[" + ",".join(_encode_value(child) for child in value) + "]"
    if type(value) is dict:
        for key in value:
            if type(key) is not str:
                raise CanonicalProfileError("object keys must be exact strings")
            _validate_scalar_string(key)
        fields = []
        for key in sorted(value):
            fields.append(_encode_string(key) + ":" + _encode_value(value[key]))
        return "{" + ",".join(fields) + "}"
    raise CanonicalProfileError("unsupported host value type")


def canonical_profile_bytes(value: Any) -> bytes:
    """Encode one supported value using the independent closed byte algorithm."""

    return _encode_value(value).encode("utf-8")


def _preflight_governed_value(
    value: Any,
    *,
    depth: int,
    budget: _Budget,
    active_containers: set[int],
) -> None:
    if depth > MAX_DEPTH:
        raise CanonicalProfileError("maximum depth exceeded")

    budget.nodes += 1
    if budget.nodes > MAX_NODES:
        raise CanonicalProfileError("maximum node count exceeded")

    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if abs(value).bit_length() > MAX_INTEGER_BITS:
            raise CanonicalProfileError("integer width exceeded")
        _count_preflight_text(str(value), budget)
        return
    if type(value) is str:
        _validate_governed_string(value)
        _count_preflight_text(value, budget)
        return
    if type(value) is list:
        if len(value) > MAX_LIST_ITEMS:
            raise CanonicalProfileError("array item limit exceeded")
    elif type(value) is dict:
        if len(value) > MAX_KEYS:
            raise CanonicalProfileError("object key limit exceeded")
        for key in value:
            if type(key) is not str:
                raise CanonicalProfileError("object keys must be exact strings")
            _validate_governed_string(key)
            _count_preflight_text(key, budget)
    else:
        raise CanonicalProfileError("unsupported host value type")

    identity = id(value)
    if identity in active_containers:
        raise CanonicalProfileError("container cycle is prohibited")
    active_containers.add(identity)
    try:
        children = value if type(value) is list else value.values()
        for child in children:
            _preflight_governed_value(
                child,
                depth=depth + 1,
                budget=budget,
                active_containers=active_containers,
            )
    finally:
        active_containers.remove(identity)


def governed_canonical_profile_bytes(value: Any) -> bytes:
    """Apply V4.9-D2 bounds, then encode with the independent algorithm."""

    _preflight_governed_value(
        value,
        depth=0,
        budget=_Budget(),
        active_containers=set(),
    )
    encoded = canonical_profile_bytes(value)
    if len(encoded) > MAX_CANONICAL_BYTES:
        raise CanonicalProfileError("canonical byte limit exceeded")
    return encoded


def _decode_hex(value: Any, *, field: str) -> bytes:
    if type(value) is not str:
        raise CanonicalProfileError(f"{field} must be a hex string")
    if len(value) % 2 or any(character not in "0123456789abcdef" for character in value):
        raise CanonicalProfileError(f"{field} must be contiguous lowercase hex")
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise CanonicalProfileError(f"{field} is invalid hex") from exc


def _case_value(case: dict[str, Any], *, prefix: str = "") -> Any:
    value_field = f"{prefix}value"
    wire_field = f"{prefix}wire_utf8_hex"
    if value_field in case and wire_field in case:
        raise CanonicalProfileError("fixture case has two input forms")
    if value_field in case:
        return case[value_field]
    if wire_field in case:
        return strict_json_loads(_decode_hex(case[wire_field], field=wire_field))
    raise CanonicalProfileError("fixture case has no input")


def build_boundary_value(case: dict[str, Any]) -> Any:
    kind = case.get("kind")
    if kind == "integer_bits":
        bits = int(case["bits"])
        value = 1 << (bits - 1)
        return -value if case.get("negative") else value
    if kind == "string_repeat":
        scalar = chr(int(case["scalar_codepoint"], 16))
        return scalar * int(case["count"])
    if kind == "key_repeat":
        scalar = chr(int(case["scalar_codepoint"], 16))
        return {scalar * int(case["count"]): 0}
    if kind == "nested_depth":
        value: Any = 0
        for _ in range(int(case["wrappers"])):
            value = [value]
        return value
    if kind == "list_items":
        return [0] * int(case["count"])
    if kind == "object_keys":
        return {f"k{index:04d}": 0 for index in range(int(case["count"]))}
    if kind == "node_budget":
        sublist_count = int(case["sublist_count"])
        default_items = int(case["default_items"])
        counts = [default_items] * sublist_count
        if "last_items" in case:
            counts[-1] = int(case["last_items"])
        return [[0] * count for count in counts]
    if kind == "canonical_bytes_array":
        full_count = int(case["full_string_count"])
        full_length = int(case["full_string_length"])
        tail_length = int(case["tail_string_length"])
        return ["x" * full_length for _ in range(full_count)] + ["x" * tail_length]
    raise CanonicalProfileError("unknown boundary vector kind")


def _verify_expected(case: dict[str, Any], actual: bytes, *, prefix: str = "") -> None:
    hex_field = f"{prefix}expected_canonical_utf8_hex"
    hash_field = f"{prefix}expected_sha256"
    expected = _decode_hex(case[hex_field], field=hex_field)
    if actual != expected:
        raise CanonicalProfileError(f"{case['id']}: canonical bytes mismatch")
    digest = hashlib.sha256(actual).hexdigest()
    if digest != case[hash_field]:
        raise CanonicalProfileError(f"{case['id']}: SHA-256 mismatch")


def _require_unique_case_ids(fixture: dict[str, Any], section: str) -> list[str]:
    cases = fixture.get(section)
    if type(cases) is not list:
        raise CanonicalProfileError(f"{section} must be an array")
    identifiers: list[str] = []
    for case in cases:
        if type(case) is not dict or type(case.get("id")) is not str or not case["id"]:
            raise CanonicalProfileError(f"{section} contains an invalid case ID")
        identifiers.append(case["id"])
    if len(identifiers) != len(set(identifiers)):
        raise CanonicalProfileError(f"{section} contains a duplicate case ID")
    return identifiers


def _verify_portable_vector_inventory(fixture: dict[str, Any]) -> None:
    inventory = fixture.get("required_vector_ids")
    if type(inventory) is not dict or set(inventory) != set(VECTOR_SECTIONS):
        raise CanonicalProfileError("required_vector_ids has wrong sections")

    for section in VECTOR_SECTIONS:
        declared = inventory[section]
        if type(declared) is not list or any(
            type(identifier) is not str or not identifier for identifier in declared
        ):
            raise CanonicalProfileError(f"{section} has an invalid declared inventory")
        if len(declared) != len(set(declared)):
            raise CanonicalProfileError(f"{section} has a duplicate declared case ID")
        actual = _require_unique_case_ids(fixture, section)
        if declared != actual:
            raise CanonicalProfileError(f"{section} vector inventory mismatch")


def check_fixture(fixture: dict[str, Any]) -> dict[str, int]:
    if fixture.get("profile") != PROFILE_ID:
        raise CanonicalProfileError("wrong profile identifier")
    if fixture.get("hash_algorithm") != "sha256":
        raise CanonicalProfileError("wrong hash algorithm")

    _verify_portable_vector_inventory(fixture)

    for case in fixture["golden_vectors"]:
        _verify_expected(case, canonical_profile_bytes(_case_value(case)))

    for case in fixture["equivalence_pairs"]:
        left = canonical_profile_bytes(_case_value(case, prefix="left_"))
        right = canonical_profile_bytes(_case_value(case, prefix="right_"))
        if left != right:
            raise CanonicalProfileError(f"{case['id']}: equivalence mismatch")
        _verify_expected(case, left)

    for case in fixture["injective_pairs"]:
        left = canonical_profile_bytes(_case_value(case, prefix="left_"))
        right = canonical_profile_bytes(_case_value(case, prefix="right_"))
        if left == right:
            raise CanonicalProfileError(f"{case['id']}: injectivity violation")
        _verify_expected(case, left, prefix="left_")
        _verify_expected(case, right, prefix="right_")

    for case in fixture["rejected_wire_vectors"]:
        raw = _decode_hex(case["wire_utf8_hex"], field="wire_utf8_hex")
        try:
            value = strict_json_loads(raw)
            canonical_profile_bytes(value)
        except CanonicalProfileError:
            continue
        raise CanonicalProfileError(f"{case['id']}: rejected wire value accepted")

    for case in fixture["boundary_vectors"]:
        value = build_boundary_value(case)
        expected = case.get("expected")
        if expected not in {"accept", "reject"}:
            raise CanonicalProfileError(f"{case['id']}: invalid boundary expectation")
        if expected == "reject":
            try:
                governed_canonical_profile_bytes(value)
            except CanonicalProfileError:
                continue
            raise CanonicalProfileError(f"{case['id']}: rejected boundary accepted")
        actual = governed_canonical_profile_bytes(value)
        if len(actual) != case["expected_canonical_byte_length"]:
            raise CanonicalProfileError(f"{case['id']}: boundary length mismatch")
        if hashlib.sha256(actual).hexdigest() != case["expected_sha256"]:
            raise CanonicalProfileError(f"{case['id']}: boundary hash mismatch")

    return {
        "golden": len(fixture["golden_vectors"]),
        "equivalence": len(fixture["equivalence_pairs"]),
        "injective": len(fixture["injective_pairs"]),
        "rejected": len(fixture["rejected_wire_vectors"]),
        "boundary": len(fixture["boundary_vectors"]),
    }


def load_fixture(path: Path) -> dict[str, Any]:
    try:
        fixture_bytes = path.read_bytes()
    except OSError as exc:
        raise CanonicalProfileError("fixture cannot be read") from exc
    if hashlib.sha256(fixture_bytes).hexdigest() != FIXTURE_SHA256:
        raise CanonicalProfileError("fixture SHA-256 does not match the frozen vector set")
    value = strict_json_loads(fixture_bytes)
    if type(value) is not dict:
        raise CanonicalProfileError("fixture root must be an object")
    return value


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_ai_gateway_canonical_json_v1.py FIXTURE", file=sys.stderr)
        return 2
    try:
        counts = check_fixture(load_fixture(Path(argv[1])))
    except CanonicalProfileError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = " ".join(f"{key}={value}" for key, value in counts.items())
    print(f"PASS profile={PROFILE_ID} {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
