from ai_gateway.adapters.base import BaseAdapter
from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.manifest_v1 import ADAPTER_MANIFEST_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.determinism import context_hash_for_value
from ai_gateway.policy import policy_reason_for
from ai_gateway.types import Envelope, Manifest, Output
from ai_gateway.validation import validate_envelope_v1, validate_manifest_v1


class PoIAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "poi"

    @property
    def manifest(self) -> Manifest:
        return validate_manifest_v1(
            {
                "manifest_version": ADAPTER_MANIFEST_V1,
                "adapter_id": self.name,
                "adapter_version": "0.3.0",
                "entrypoint": "ai_gateway.adapters.poi.PoIAdapter",
                "accepted_input_types": ["poi_candidate"],
                "supported_actions": ["evaluate_candidate"],
                "required_payload_fields": ["task_type", "model_family", "input_payload"],
                "optional_payload_fields": [],
                "output_contract": AI_GATEWAY_OUTPUT_V1,
                "determinism_constraints": [
                    "same_input_same_envelope",
                    "same_envelope_same_output",
                    "canonical_json_only",
                    "no_time_dependency",
                    "no_randomness",
                    "no_network_calls",
                ],
                "failure_reason_ids": [
                    "ACCEPTED",
                    "UNSUPPORTED_TASK",
                    "UNSUPPORTED_MODEL",
                    "INVALID_ENVELOPE",
                    "INVALID_OUTPUT",
                    "MISSING_REQUIRED_FIELD",
                    "SCHEMA_VIOLATION",
                    "ADAPTER_VALIDATION_FAILED",
                    "POLICY_DENIED",
                    "INTERNAL_ERROR",
                ],
                "notes": "PoI adapter boundary",
            }
        )

    def build_envelope(self, source_input: dict) -> Envelope:
        envelope: Envelope = {
            "contract_version": AI_GATEWAY_ENVELOPE_V1,
            "adapter": self.name,
            "task_type": source_input.get("task_type"),
            "model_family": source_input.get("model_family"),
            "input_payload": source_input.get("input_payload"),
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

        output_payload = {"status": "accepted-candidate"} if accepted else {}

        return {
            "contract_version": AI_GATEWAY_OUTPUT_V1,
            "adapter": self.name,
            "task_type": validated["task_type"],
            "accepted": accepted,
            "reason_id": reason_id,
            "output_payload": output_payload,
            "context_hash": context_hash_for_value(validated),
        }
