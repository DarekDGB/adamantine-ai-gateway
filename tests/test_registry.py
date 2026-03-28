import pytest

from ai_gateway.registry import AdapterRegistry


class DummyAdapter:
    pass


def test_registry_register_and_get_adapter() -> None:
    registry = AdapterRegistry()
    adapter = DummyAdapter()

    registry.register("poi", adapter)

    assert registry.get("poi") is adapter


def test_registry_rejects_empty_name() -> None:
    registry = AdapterRegistry()

    with pytest.raises(ValueError, match="adapter name must be non-empty"):
        registry.register("", DummyAdapter())


def test_registry_rejects_duplicate_registration() -> None:
    registry = AdapterRegistry()
    registry.register("poi", DummyAdapter())

    with pytest.raises(ValueError, match="adapter already registered: poi"):
        registry.register("poi", DummyAdapter())


def test_registry_rejects_unknown_adapter_lookup() -> None:
    registry = AdapterRegistry()

    with pytest.raises(ValueError, match="adapter not registered: poi"):
        registry.get("poi")


def test_registry_names_are_sorted() -> None:
    registry = AdapterRegistry()
    registry.register("zeta", DummyAdapter())
    registry.register("alpha", DummyAdapter())

    assert registry.names() == ("alpha", "zeta")
