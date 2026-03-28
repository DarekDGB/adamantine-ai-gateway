from ai_gateway.adapters.base import BaseAdapter
from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.determinism import context_hash_for_value
from ai_gateway.policy import policy_reason_for
from ai_gateway.types import Envelope, Output
from ai_gateway.validation import validate_envelope_v1


class PoIAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "poi"

    def build_envelope(self, source_input: dict) -> Envelope:
        envelope: Envelope = {
            "contract_version": AI_GATEWAY_ENVELOPE_V1,
            "adapter": self.name,
            "task_type": source_input["task_type"],
            "model_family": source_input["model_family"],
            "input_payload": source_input["input_payload"],
        }
        return validate_envelope_v1(envelope)

    def build_output(self, envelope: Envelope) -> Output:
        validated = validate_envelope_v1(envelope)

        policy_reason = policy_reason_for(
            validated["task_type"],
            validated["model_family"],
        )

        accepted = policy_reason is None
        reason_id = policy_reason.value if policy_reason is not None else "ACCEPTED"

        output_payload = (
            {"status": "accepted-candidate"}
            if accepted
            else {}
        )

        return {
            "contract_version": AI_GATEWAY_OUTPUT_V1,
            "adapter": self.name,
            "task_type": validated["task_type"],
            "accepted": accepted,
            "reason_id": reason_id,
            "output_payload": output_payload,
            "context_hash": context_hash_for_value(validated),
        }
