import json
from typing import Any


AI_GATEWAY_CANONICAL_JSON_V1 = "ai_gateway_canonical_json_v1"


def canonical_json_bytes(value: Any) -> bytes:
    """
    Serialize a prevalidated value under AI_GATEWAY_CANONICAL_JSON_V1.

    The normative byte algorithm, supported value model, wire-parser rules,
    and governed resource limits are defined in
    contracts/AI_GATEWAY_CANONICAL_JSON_V1.md. This helper is not a raw-wire
    parser; governed callers validate the supported exact JSON domain before
    calling it. The serializer expression below is frozen by literal vectors
    and an independent implementation.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
