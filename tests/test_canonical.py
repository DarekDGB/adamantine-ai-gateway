from ai_gateway.canonical import (
    AI_GATEWAY_CANONICAL_JSON_V1,
    canonical_json_bytes,
)


def test_canonical_json_bytes_sorts_keys_and_removes_whitespace() -> None:
    value = {"b": 2, "a": 1}
    assert AI_GATEWAY_CANONICAL_JSON_V1 == "ai_gateway_canonical_json_v1"
    assert canonical_json_bytes(value) == b'{"a":1,"b":2}'
