from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.errors import AdapterError, ContractError, PolicyError, ValidationError
from ai_gateway.policy import enforce_policy_for_adapter
from ai_gateway.reason_ids import ReasonID
from ai_gateway.receipt import build_receipt_v1
from ai_gateway.registry import AdapterRegistry
from ai_gateway.types import Envelope, Output, PolicyPack, Receipt
from ai_gateway.validation import validate_envelope_v1


class AIGateway:
    def __init__(self, registry: AdapterRegistry) -> None:
        self._registry = registry

    def process(self, adapter_name: str, source_input: dict) -> Output:
        _, output = self._process_components(adapter_name, source_input)
        return output

    def process_with_policy(
        self,
        adapter_name: str,
        source_input: dict,
        policy_pack: PolicyPack,
    ) -> Output:
        try:
            self._registry.get_manifest(adapter_name)
        except AdapterError as exc:
            return self._fail_closed(
                adapter_name,
                self._reason_id_from_error(exc, ReasonID.ADAPTER_VALIDATION_FAILED),
                source_input,
            )

        _, output = self._process_components_with_policy(
            adapter_name=adapter_name,
            source_input=source_input,
            policy_pack=policy_pack,
        )
        return output

    def process_with_receipt(
        self,
        adapter_name: str,
        source_input: dict,
    ) -> dict[str, Output | Receipt | None]:
        try:
            manifest = self._registry.get_manifest(adapter_name)
        except AdapterError as exc:
            return {
                "output": self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(
                        exc,
                        ReasonID.ADAPTER_VALIDATION_FAILED,
                    ),
                    source_input,
                ),
                "receipt": None,
            }

        envelope, output = self._process_components(adapter_name, source_input)

        try:
            receipt = build_receipt_v1(
                manifest=manifest,
                envelope=envelope,
                output=output,
            )
            return {"output": output, "receipt": receipt}
        except Exception:
            fallback_envelope = self._fail_closed_envelope(adapter_name, source_input)
            fallback_output = self._fail_closed(
                adapter_name,
                ReasonID.INTERNAL_ERROR,
                source_input,
            )
            fallback_receipt = build_receipt_v1(
                manifest=manifest,
                envelope=fallback_envelope,
                output=fallback_output,
            )
            return {"output": fallback_output, "receipt": fallback_receipt}

    def _process_components(
        self,
        adapter_name: str,
        source_input: dict,
    ) -> tuple[Envelope, Output]:
        try:
            adapter = self._registry.get(adapter_name)
        except AdapterError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(exc, ReasonID.ADAPTER_NOT_REGISTERED),
                    source_input,
                ),
            )

        try:
            envelope = adapter.build_envelope(source_input)
            return envelope, adapter.build_output(envelope)

        except ValidationError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(exc, ReasonID.SCHEMA_VIOLATION),
                    source_input,
                ),
            )

        except ContractError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(exc, ReasonID.INVALID_ENVELOPE),
                    source_input,
                ),
            )

        except PolicyError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(exc, ReasonID.POLICY_DENIED),
                    source_input,
                ),
            )

        except AdapterError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(
                        exc,
                        ReasonID.ADAPTER_VALIDATION_FAILED,
                    ),
                    source_input,
                ),
            )

        except Exception:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    ReasonID.INTERNAL_ERROR,
                    source_input,
                ),
            )

    def _process_components_with_policy(
        self,
        adapter_name: str,
        source_input: dict,
        policy_pack: PolicyPack,
    ) -> tuple[Envelope, Output]:
        try:
            adapter = self._registry.get(adapter_name)
        except AdapterError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(exc, ReasonID.ADAPTER_NOT_REGISTERED),
                    source_input,
                ),
            )

        try:
            envelope = adapter.build_envelope(source_input)
            action = self._extract_action(envelope)
            enforce_policy_for_adapter(
                policy_pack=policy_pack,
                adapter_name=adapter_name,
                task_type=envelope["task_type"],
                model_family=envelope["model_family"],
                action=action,
            )
            return envelope, adapter.build_output(envelope)

        except ValidationError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(exc, ReasonID.SCHEMA_VIOLATION),
                    source_input,
                ),
            )

        except ContractError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(exc, ReasonID.INVALID_ENVELOPE),
                    source_input,
                ),
            )

        except PolicyError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(exc, ReasonID.POLICY_DENIED),
                    source_input,
                ),
            )

        except AdapterError as exc:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    self._reason_id_from_error(
                        exc,
                        ReasonID.ADAPTER_VALIDATION_FAILED,
                    ),
                    source_input,
                ),
            )

        except Exception:
            return (
                self._fail_closed_envelope(adapter_name, source_input),
                self._fail_closed(
                    adapter_name,
                    ReasonID.INTERNAL_ERROR,
                    source_input,
                ),
            )

    @staticmethod
    def _extract_action(envelope: Envelope) -> str | None:
        payload = envelope.get("input_payload")
        if not isinstance(payload, dict):
            return None

        action = payload.get("action")
        if not isinstance(action, str) or not action:
            return None

        return action

    @staticmethod
    def _fail_closed(
        adapter_name: str,
        reason_id: ReasonID,
        source_input: object,
    ) -> Output:
        task_type = "unknown"

        if isinstance(source_input, dict):
            raw_task_type = source_input.get("task_type")
            if isinstance(raw_task_type, str) and raw_task_type:
                task_type = raw_task_type
            elif adapter_name == "wallet":
                task_type = "wallet_operation"

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
    def _fail_closed_envelope(adapter_name: str, source_input: object) -> Envelope:
        task_type = "unknown"
        model_family = "fail_closed_v1"

        if isinstance(source_input, dict):
            raw_task_type = source_input.get("task_type")
            if isinstance(raw_task_type, str) and raw_task_type:
                task_type = raw_task_type
            elif adapter_name == "wallet":
                task_type = "wallet_operation"

            raw_model_family = source_input.get("model_family")
            if isinstance(raw_model_family, str) and raw_model_family:
                model_family = raw_model_family
            elif adapter_name == "wallet":
                model_family = "wallet-v1"

        envelope: Envelope = {
            "contract_version": AI_GATEWAY_ENVELOPE_V1,
            "adapter": adapter_name,
            "task_type": task_type,
            "model_family": model_family,
            "input_payload": {},
        }
        return validate_envelope_v1(envelope)

    @staticmethod
    def _reason_id_from_error(exc: Exception, default_reason: ReasonID) -> ReasonID:
        message = str(exc)

        try:
            return ReasonID(message)
        except ValueError:
            return default_reason
