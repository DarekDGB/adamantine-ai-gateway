from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.errors import AdapterError, ContractError, PolicyError, ValidationError
from ai_gateway.handoff import build_handoff_v1
from ai_gateway.hashing import sha256_hex
from ai_gateway.policy import enforce_policy_for_adapter
from ai_gateway.policy_binding import (
    _build_policy_binding_v1,
    _capture_policy_pack_v1,
    _materialize_policy_pack_v1,
    _snapshot_exact_json_artifact,
)
from ai_gateway.reason_ids import ReasonID
from ai_gateway.receipt import build_receipt_v1
from ai_gateway.registry import AdapterRegistry
from ai_gateway.types import Envelope, Manifest, Output, PolicyPack, Receipt
from ai_gateway.validation import (
    MAX_STRING_LENGTH,
    validate_envelope_v1,
    validate_manifest_v1,
    validate_output_v1,
)


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
            manifest = self._registry.get_manifest(adapter_name)
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
            manifest=manifest,
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

        envelope, output = self._process_components_with_manifest(
            adapter_name=adapter_name,
            source_input=source_input,
            manifest=manifest,
        )

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

    def process_governed(
        self,
        adapter_name: str,
        source_input: dict,
        policy_pack: PolicyPack,
    ) -> dict[str, Output | Receipt | dict | None]:
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
                "handoff": None,
            }

        envelope, output = self._process_components_with_policy(
            adapter_name=adapter_name,
            source_input=source_input,
            policy_pack=policy_pack,
            manifest=manifest,
        )

        try:
            receipt = build_receipt_v1(
                manifest=manifest,
                envelope=envelope,
                output=output,
            )
            handoff = build_handoff_v1(
                envelope=envelope,
                output=output,
                receipt=receipt,
            )
            return {
                "output": output,
                "receipt": receipt,
                "handoff": handoff,
            }
        except Exception:
            fallback_envelope = self._fail_closed_envelope(adapter_name, source_input)
            fallback_output = self._fail_closed(
                adapter_name,
                ReasonID.INTERNAL_ERROR,
                source_input,
            )

            try:
                fallback_receipt = build_receipt_v1(
                    manifest=manifest,
                    envelope=fallback_envelope,
                    output=fallback_output,
                )
                fallback_handoff = build_handoff_v1(
                    envelope=fallback_envelope,
                    output=fallback_output,
                    receipt=fallback_receipt,
                )
                return {
                    "output": fallback_output,
                    "receipt": fallback_receipt,
                    "handoff": fallback_handoff,
                }
            except Exception:
                return {
                    "output": fallback_output,
                    "receipt": None,
                    "handoff": None,
                }

    def process_governed_with_policy_binding_v1(
        self,
        adapter_name: str,
        source_input: dict,
        policy_pack: PolicyPack,
    ) -> dict[str, Output | Receipt | dict | None]:
        """Produce an atomically policy-bound governed evidence chain.

        The policy pack is captured into bounded immutable canonical bytes
        before registry or adapter callbacks. Existing process_governed and all
        V1 output, receipt, and handoff shapes remain unchanged.
        """

        try:
            snapshot = _capture_policy_pack_v1(policy_pack)
            captured_policy_pack = _materialize_policy_pack_v1(snapshot)
        except (ValidationError, ContractError) as exc:
            return self._policy_binding_failure_result(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=self._reason_id_from_error(exc, ReasonID.SCHEMA_VIOLATION),
            )
        except Exception:
            return self._policy_binding_failure_result(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=ReasonID.INTERNAL_ERROR,
            )

        try:
            manifest = validate_manifest_v1(
                _snapshot_exact_json_artifact(
                    self._registry.get_manifest(adapter_name)
                )
            )
        except AdapterError as exc:
            return self._policy_binding_failure_result(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=self._reason_id_from_error(
                    exc,
                    ReasonID.ADAPTER_VALIDATION_FAILED,
                ),
            )
        except (ValidationError, ContractError) as exc:
            return self._policy_binding_failure_result(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=self._reason_id_from_error(
                    exc,
                    ReasonID.SCHEMA_VIOLATION,
                ),
            )
        except Exception:
            return self._policy_binding_failure_result(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=ReasonID.INTERNAL_ERROR,
            )

        try:
            envelope, output = self._process_components_for_policy_binding_v1(
                adapter_name=adapter_name,
                source_input=source_input,
                policy_pack=captured_policy_pack,
                manifest=manifest,
            )
            if envelope is None:
                return {
                    "output": output,
                    "receipt": None,
                    "handoff": None,
                    "policy_binding": None,
                }
            receipt = build_receipt_v1(
                manifest=manifest,
                envelope=envelope,
                output=output,
            )
            handoff = build_handoff_v1(
                envelope=envelope,
                output=output,
                receipt=receipt,
            )
            policy_binding = _build_policy_binding_v1(
                snapshot=snapshot,
                envelope=envelope,
                output=output,
                receipt=receipt,
                handoff=handoff,
            )
        except Exception:
            return self._policy_binding_failure_result(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=ReasonID.INTERNAL_ERROR,
            )

        return {
            "output": output,
            "receipt": receipt,
            "handoff": handoff,
            "policy_binding": policy_binding,
        }

    def _process_components_for_policy_binding_v1(
        self,
        *,
        adapter_name: str,
        source_input: dict,
        policy_pack: PolicyPack,
        manifest: Manifest,
    ) -> tuple[Envelope | None, Output]:
        """Process D2 evidence without converting unsafe failures into proof."""

        try:
            adapter = self._registry.get(adapter_name)
        except AdapterError as exc:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=self._reason_id_from_error(
                    exc,
                    ReasonID.ADAPTER_NOT_REGISTERED,
                ),
            )
        except Exception:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=ReasonID.INTERNAL_ERROR,
            )

        try:
            envelope = validate_envelope_v1(
                _snapshot_exact_json_artifact(
                    adapter.build_envelope(source_input)
                )
            )
        except ValidationError as exc:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=self._reason_id_from_error(
                    exc,
                    ReasonID.SCHEMA_VIOLATION,
                ),
            )
        except ContractError as exc:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=self._reason_id_from_error(
                    exc,
                    ReasonID.INVALID_ENVELOPE,
                ),
            )
        except AdapterError as exc:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=self._reason_id_from_error(
                    exc,
                    ReasonID.ADAPTER_VALIDATION_FAILED,
                ),
            )
        except Exception:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=ReasonID.INTERNAL_ERROR,
            )

        if envelope["adapter"] != adapter_name:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=ReasonID.INVALID_ENVELOPE,
            )
        if manifest["adapter_id"] != adapter_name:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=ReasonID.INVALID_ENVELOPE,
            )

        action = self._extract_action(envelope)
        if action is None or action not in manifest["supported_actions"]:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=ReasonID.ADAPTER_VALIDATION_FAILED,
            )

        try:
            enforce_policy_for_adapter(
                policy_pack=policy_pack,
                adapter_name=adapter_name,
                task_type=envelope["task_type"],
                model_family=envelope["model_family"],
                action=action,
            )
        except PolicyError as exc:
            return envelope, self._policy_binding_rejected_output(
                envelope,
                self._reason_id_from_error(exc, ReasonID.POLICY_DENIED),
            )
        except Exception:
            return None, self._policy_binding_failure_output(
                adapter_name=adapter_name,
                source_input=source_input,
                reason_id=ReasonID.INTERNAL_ERROR,
            )

        try:
            output = validate_output_v1(
                _snapshot_exact_json_artifact(adapter.build_output(envelope))
            )
            self._enforce_manifest_output_alignment(
                manifest=manifest,
                envelope=envelope,
                output=output,
            )
            return envelope, output
        except ValidationError as exc:
            reason = self._reason_id_from_error(exc, ReasonID.SCHEMA_VIOLATION)
        except ContractError as exc:
            reason = self._reason_id_from_error(exc, ReasonID.INVALID_OUTPUT)
        except PolicyError as exc:
            reason = self._reason_id_from_error(exc, ReasonID.POLICY_DENIED)
        except AdapterError as exc:
            reason = self._reason_id_from_error(
                exc,
                ReasonID.ADAPTER_VALIDATION_FAILED,
            )
        except Exception:
            reason = ReasonID.INTERNAL_ERROR

        return None, self._policy_binding_failure_output(
            adapter_name=adapter_name,
            source_input=source_input,
            reason_id=reason,
        )

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

    def _process_components_with_manifest(
        self,
        adapter_name: str,
        source_input: dict,
        manifest: Manifest,
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
            self._enforce_manifest_envelope_alignment(
                adapter_name=adapter_name,
                manifest=manifest,
                envelope=envelope,
            )

            output = adapter.build_output(envelope)
            self._enforce_manifest_output_alignment(
                manifest=manifest,
                envelope=envelope,
                output=output,
            )
            return envelope, output

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
        manifest: Manifest,
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
            self._enforce_manifest_envelope_alignment(
                adapter_name=adapter_name,
                manifest=manifest,
                envelope=envelope,
            )

            action = self._extract_action(envelope)
            enforce_policy_for_adapter(
                policy_pack=policy_pack,
                adapter_name=adapter_name,
                task_type=envelope["task_type"],
                model_family=envelope["model_family"],
                action=action,
            )

            output = adapter.build_output(envelope)
            self._enforce_manifest_output_alignment(
                manifest=manifest,
                envelope=envelope,
                output=output,
            )
            return envelope, output

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
    def _enforce_manifest_envelope_alignment(
        adapter_name: str,
        manifest: Manifest,
        envelope: Envelope,
    ) -> None:
        if envelope["adapter"] != adapter_name:
            raise ContractError(ReasonID.INVALID_ENVELOPE.value)

        if manifest["adapter_id"] != adapter_name:
            raise ContractError(ReasonID.INVALID_ENVELOPE.value)

        action = AIGateway._extract_action(envelope)
        if action is not None and action not in manifest["supported_actions"]:
            raise AdapterError(ReasonID.ADAPTER_VALIDATION_FAILED.value)

    @staticmethod
    def _enforce_manifest_output_alignment(
        manifest: Manifest,
        envelope: Envelope,
        output: Output,
    ) -> None:
        if output["adapter"] != manifest["adapter_id"]:
            raise ContractError(ReasonID.INVALID_OUTPUT.value)

        if output["contract_version"] != manifest["output_contract"]:
            raise ContractError(ReasonID.INVALID_OUTPUT.value)

        if output["task_type"] != envelope["task_type"]:
            raise ContractError(ReasonID.INVALID_OUTPUT.value)

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
    def _policy_binding_failure_result(
        *,
        adapter_name: object,
        source_input: object,
        reason_id: ReasonID,
    ) -> dict[str, Output | None]:
        safe_adapter = AIGateway._safe_failure_label(adapter_name, "unknown")
        task_type = "wallet_operation" if safe_adapter == "wallet" else "unknown"
        if type(source_input) is dict and all(
            type(key) is str for key in source_input
        ):
            candidate = source_input.get("task_type")
            task_type = AIGateway._safe_failure_label(candidate, task_type)

        output: Output = {
            "contract_version": AI_GATEWAY_OUTPUT_V1,
            "adapter": safe_adapter,
            "task_type": task_type,
            "accepted": False,
            "reason_id": reason_id.value,
            "output_payload": {},
            "context_hash": "",
        }
        return {
            "output": output,
            "receipt": None,
            "handoff": None,
            "policy_binding": None,
        }

    @staticmethod
    def _safe_failure_label(value: object, fallback: str) -> str:
        if type(value) is not str or not value.strip():
            return fallback
        if len(value) > MAX_STRING_LENGTH:
            return fallback
        try:
            value.encode("utf-8")
        except UnicodeError:
            return fallback
        return value

    @staticmethod
    def _policy_binding_failure_output(
        *,
        adapter_name: object,
        source_input: object,
        reason_id: ReasonID,
    ) -> Output:
        result = AIGateway._policy_binding_failure_result(
            adapter_name=adapter_name,
            source_input=source_input,
            reason_id=reason_id,
        )
        return result["output"]

    @staticmethod
    def _policy_binding_rejected_output(
        envelope: Envelope,
        reason_id: ReasonID,
    ) -> Output:
        return {
            "contract_version": AI_GATEWAY_OUTPUT_V1,
            "adapter": envelope["adapter"],
            "task_type": envelope["task_type"],
            "accepted": False,
            "reason_id": reason_id.value,
            "output_payload": {},
            "context_hash": sha256_hex(envelope),
        }

    @staticmethod
    def _reason_id_from_error(exc: Exception, default_reason: ReasonID) -> ReasonID:
        try:
            message = str(exc)
        except Exception:
            return default_reason

        if type(message) is not str:
            return default_reason

        try:
            return ReasonID(message)
        except ValueError:
            return default_reason
