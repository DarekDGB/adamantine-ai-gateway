import pytest

from ai_gateway.adapters.base import BaseAdapter


class DummyAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "dummy"

    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": self.name,
            "task_type": "code_review",
            "model_family": "deterministic-test-model",
            "input_payload": source_input,
        }

    def build_output(self, envelope: dict) -> dict:
        return {
            "contract_version": "ai_gateway_output_v1",
            "adapter": self.name,
            "task_type": envelope["task_type"],
            "accepted": False,
            "reason_id": "POLICY_DENIED",
            "output_payload": {},
            "context_hash": "abc123",
        }


class DelegatingAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return BaseAdapter.name.fget(self)  # type: ignore[misc]

    def build_envelope(self, source_input: dict) -> dict:
        return BaseAdapter.build_envelope(self, source_input)

    def build_output(self, envelope: dict) -> dict:
        return BaseAdapter.build_output(self, envelope)


def test_base_adapter_subclass_can_define_required_interface() -> None:
    adapter = DummyAdapter()

    assert adapter.name == "dummy"
    assert adapter.build_envelope({"candidate_id": "1"})["adapter"] == "dummy"
    assert adapter.build_output({"task_type": "code_review"})["adapter"] == "dummy"


def test_base_adapter_default_name_raises_not_implemented() -> None:
    adapter = DelegatingAdapter()

    with pytest.raises(NotImplementedError):
        _ = adapter.name


def test_base_adapter_default_build_envelope_raises_not_implemented() -> None:
    adapter = DelegatingAdapter()

    with pytest.raises(NotImplementedError):
        adapter.build_envelope({})


def test_base_adapter_default_build_output_raises_not_implemented() -> None:
    adapter = DelegatingAdapter()

    with pytest.raises(NotImplementedError):
        adapter.build_output({})
