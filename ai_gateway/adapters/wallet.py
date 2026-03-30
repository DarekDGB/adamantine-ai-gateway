from ai_gateway.adapters.base import BaseAdapter
from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.determinism import context_hash_for_value
from ai_gateway.types import Envelope, Output
from ai_gateway.validation import validate_envelope_v1

SUPPORTED_WALLET_ACTIONS = (
    "build_transaction",
    "sign_transaction_request",
)


class WalletAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "wallet"

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
            raise ValueError(f"unsupported wallet action: {action}")

    @staticmethod
    def _require_wallet_payload(value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValueError("wallet source_input must be a dict")

        required_fields = (
            "wallet_id",
            "network",
            "asset",
            "action",
            "request_payload",
        )

        for field in required_fields:
            if field not in value:
                raise ValueError(f"missing required wallet field: {field}")

        for field in ("wallet_id", "network", "asset", "action"):
            field_value = value[field]
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"wallet field must be a non-empty string: {field}")

        if not isinstance(value["request_payload"], dict):
            raise ValueError("wallet request_payload must be a dict")

        return value
