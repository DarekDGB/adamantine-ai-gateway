import json
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    """
    Serialize a Python value into deterministic canonical JSON bytes.

    Rules:
    - UTF-8 encoding
    - sorted object keys
    - no extra whitespace
    - allow only JSON-serializable structured data
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
