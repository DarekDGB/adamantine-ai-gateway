from ai_gateway.adapters.base import BaseAdapter


def test_base_adapter_subclass_can_define_required_interface() -> None:
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

    adapter = DummyAdapter()

    assert adapter.name == "dummy"
    assert adapter.build_envelope({"candidate_id": "1"})["adapter"] == "dummy"
    assert adapter.build_output({"task_type": "code_review"})["adapter"] == "dummy"
