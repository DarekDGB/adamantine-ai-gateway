from ai_gateway.canonical import canonical_json_bytes


def test_canonical_json_bytes_sorts_keys_and_removes_whitespace() -> None:
    value = {"b": 2, "a": 1}
    assert canonical_json_bytes(value) == b'{"a":1,"b":2}'
