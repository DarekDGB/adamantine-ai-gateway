import pytest

from ai_gateway.adapters.base import BaseAdapter


class DummyAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def manifest(self) -> dict:
        return {
            "manifest_version": "adapter_manifest_v1",
            "adapter_id": self.name,
            "adapter_version": "0.3.0",
            "entrypoint": "tests.test_adapter_base.DummyAdapter",
            "accepted_input_types": ["dummy_input"],
            "supported_actions": ["evaluate_candidate"],
            "required_payload_fields": ["candidate_id"],
            "optional_payload_fields": [],
            "output_contract": "ai_gateway_output_v1",
            "determinism_constraints": ["canonical_json_only"],
            "failure_reason_ids": ["ACCEPTED", "POLICY_DENIED"],
            "notes": "Dummy adapter for interface tests",
        }

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

    @property
    def manifest(self) -> dict:
        return BaseAdapter.manifest.fget(self)  # type: ignore[misc]

    def build_envelope(self, source_input: dict) -> dict:
        return BaseAdapter.build_envelope(self, source_input)

    def build_output(self, envelope: dict) -> dict:
        return BaseAdapter.build_output(self, envelope)


def test_base_adapter_subclass_can_define_required_interface() -> None:
    adapter = DummyAdapter()

    assert adapter.name == "dummy"
    assert adapter.manifest["adapter_id"] == "dummy"
    assert adapter.build_envelope({"candidate_id": "1"})["adapter"] == "dummy"
    assert adapter.build_output({"task_type": "code_review"})["adapter"] == "dummy"


def test_base_adapter_default_name_raises_not_implemented() -> None:
    adapter = DelegatingAdapter()

    with pytest.raises(NotImplementedError):
        _ = adapter.name


def test_base_adapter_default_manifest_raises_not_implemented() -> None:
    adapter = DelegatingAdapter()

    with pytest.raises(NotImplementedError):
        _ = adapter.manifest


def test_base_adapter_default_build_envelope_raises_not_implemented() -> None:
    adapter = DelegatingAdapter()

    with pytest.raises(NotImplementedError):
        adapter.build_envelope({})


def test_base_adapter_default_build_output_raises_not_implemented() -> None:
    adapter = DelegatingAdapter()

    with pytest.raises(NotImplementedError):
        adapter.build_output({})
