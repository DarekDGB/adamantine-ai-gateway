from ai_gateway.determinism import context_hash_for_value


def test_context_hash_for_value_is_deterministic() -> None:
    value = {"b": 2, "a": 1}

    first = context_hash_for_value(value)
    second = context_hash_for_value({"a": 1, "b": 2})

    assert first == second
    assert len(first) == 64
