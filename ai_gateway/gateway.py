from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry
from ai_gateway.types import Output


class AIGateway:
    def __init__(self, registry: AdapterRegistry) -> None:
        self._registry = registry

    def process(self, adapter_name: str, source_input: dict) -> Output:
        try:
            adapter = self._registry.get(adapter_name)
            envelope = adapter.build_envelope(source_input)
            return adapter.build_output(envelope)
        except ValueError as exc:
            reason_id = self._map_value_error_to_reason_id(str(exc))
            return {
                "contract_version": "ai_gateway_output_v1",
                "adapter": adapter_name,
                "task_type": source_input.get("task_type", "unknown"),
                "accepted": False,
                "reason_id": reason_id.value,
                "output_payload": {},
                "context_hash": "",
            }
        except Exception:
            return {
                "contract_version": "ai_gateway_output_v1",
                "adapter": adapter_name,
                "task_type": source_input.get("task_type", "unknown"),
                "accepted": False,
                "reason_id": ReasonID.INTERNAL_ERROR.value,
                "output_payload": {},
                "context_hash": "",
            }

    @staticmethod
    def _map_value_error_to_reason_id(message: str) -> ReasonID:
        if message.startswith("adapter not registered"):
            return ReasonID.ADAPTER_NOT_REGISTERED
        if "invalid envelope contract_version" in message:
            return ReasonID.INVALID_ENVELOPE
        if "missing required envelope field" in message:
            return ReasonID.MISSING_REQUIRED_FIELD
        if "invalid output contract_version" in message:
            return ReasonID.INVALID_OUTPUT
        if "missing required output field" in message:
            return ReasonID.MISSING_REQUIRED_FIELD
        if "accepted must be a bool" in message:
            return ReasonID.INVALID_OUTPUT
        if "value must be a dict" in message:
            return ReasonID.SCHEMA_VIOLATION
        return ReasonID.INTERNAL_ERROR
