from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.errors import AdapterError, ContractError, PolicyError, ValidationError
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
        except ValidationError as exc:
            return self._fail_closed(
                adapter_name,
                self._reason_id_from_error(exc, ReasonID.SCHEMA_VIOLATION),
                source_input,
            )
        except ContractError as exc:
            return self._fail_closed(
                adapter_name,
                self._reason_id_from_error(exc, ReasonID.INVALID_ENVELOPE),
                source_input,
            )
        except PolicyError as exc:
            return self._fail_closed(
                adapter_name,
                self._reason_id_from_error(exc, ReasonID.POLICY_DENIED),
                source_input,
            )
        except AdapterError as exc:
            return self._fail_closed(
                adapter_name,
                self._reason_id_from_error(exc, ReasonID.ADAPTER_VALIDATION_FAILED),
                source_input,
            )
        except Exception:
            return self._fail_closed(adapter_name, ReasonID.INTERNAL_ERROR, source_input)

    @staticmethod
    def _fail_closed(adapter_name: str, reason_id: ReasonID, source_input: object) -> Output:
        task_type = "unknown"
        if isinstance(source_input, dict):
            raw_task_type = source_input.get("task_type")
            if isinstance(raw_task_type, str) and raw_task_type:
                task_type = raw_task_type

        return {
            "contract_version": AI_GATEWAY_OUTPUT_V1,
            "adapter": adapter_name,
            "task_type": task_type,
            "accepted": False,
            "reason_id": reason_id.value,
            "output_payload": {},
            "context_hash": "",
        }

    @staticmethod
    def _reason_id_from_error(exc: Exception, default_reason: ReasonID) -> ReasonID:
        message = str(exc)
        try:
            return ReasonID(message)
        except ValueError:
            return default_reason
