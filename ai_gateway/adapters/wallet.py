from ai_gateway.adapters.base import BaseAdapter
from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.manifest_v1 import ADAPTER_MANIFEST_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.determinism import context_hash_for_value
from ai_gateway.errors import AdapterError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.types import Envelope, Manifest, Output
from ai_gateway.validation import validate_envelope_v1, validate_manifest_v1

SUPPORTED_WALLET_ACTIONS = (
    "build_transaction",
    "sign_transaction_request",
)


class WalletAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "wallet"

    @property
    def manifest(self) -> Manifest:
        return validate_manifest_v1(
            {
                "manifest_version": ADAPTER_MANIFEST_V1,
                "adapter_id": self.name,
                "adapter_version": "0.3.0",
                "entrypoint": "ai_gateway.adapters.wallet.WalletAdapter",
                "accepted_input_types": ["wallet_request"],
                "supported_actions": list(SUPPORTED_WALLET_ACTIONS),
                "required_payload_fields": [
                    "wallet_id",
                    "network",
                    "asset",
                    "action",
                    "request_payload",
                ],
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
                    "INVALID_ENVELOPE",
                    "INVALID_OUTPUT",
                    "MISSING_REQUIRED_FIELD",
                    "SCHEMA_VIOLATION",
                    "ADAPTER_NOT_REGISTERED",
                    "ADAPTER_VALIDATION_FAILED",
                    "INTERNAL_ERROR",
                ],
                "notes": "Wallet adapter boundary without signing authority",
            }
        )

    def build_envelope(self, source_input: dict) -> Envelope:
        self._validate_source_input(source_input)

        envelope: Envelope = {
            "contract_version": AI_GATEWAY_ENVELOPE_V1,
            "adapter": self.name,
            "task_type": "wallet_operation",
            "model_family": "wallet-v1",
            "input_payload": {
                "wallet_id": source_input["wallet_id"],
                "network": source_input["network"],
                "asset": source_input["asset"],
                "action": source_input["action"],
                "request_payload": source_input["request_payload"],
            },
        }
        return validate_envelope_v1(envelope)

    def build_output(self, envelope: Envelope) -> Output:
        validated = validate_envelope_v1(envelope)
        payload = self._require_wallet_payload(validated["input_payload"])

        return {
            "contract_version": AI_GATEWAY_OUTPUT_V1,
            "adapter": self.name,
            "task_type": validated["task_type"],
            "accepted": True,
            "reason_id": "ACCEPTED",
            "output_payload": {
                "status": "accepted-candidate",
                "wallet_id": payload["wallet_id"],
                "network": payload["network"],
                "asset": payload["asset"],
                "action": payload["action"],
                "request_payload": payload["request_payload"],
            },
            "context_hash": context_hash_for_value(validated),
        }

    def _validate_source_input(self, source_input: dict) -> None:
        payload = self._require_wallet_payload(source_input)
        action = payload["action"]
        if action not in SUPPORTED_WALLET_ACTIONS:
            raise AdapterError(ReasonID.ADAPTER_VALIDATION_FAILED.value)

    @staticmethod
    def _require_wallet_payload(value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

        required_fields = (
            "wallet_id",
            "network",
            "asset",
            "action",
            "request_payload",
        )

        for field in required_fields:
            if field not in value:
                raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)

        for field in ("wallet_id", "network", "asset", "action"):
            field_value = value[field]
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

        if not isinstance(value["request_payload"], dict):
            raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

        return value
