from typing import Any

from ai_gateway.hashing import sha256_hex


def context_hash_for_value(value: Any) -> str:
    """
    Return a deterministic context hash for a structured value.
    """
    return sha256_hex(value)
