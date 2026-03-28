import hashlib
from typing import Any

from ai_gateway.canonical import canonical_json_bytes


def sha256_hex(value: Any) -> str:
    """
    Hash a structured value via canonical JSON serialization and return
    a lowercase SHA-256 hex digest.
    """
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
