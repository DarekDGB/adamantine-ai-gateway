import pytest

from ai_gateway.adapters.wallet import SUPPORTED_WALLET_ACTIONS, WalletAdapter
from ai_gateway.contracts.envelope_v1 import AI_GATEWAY_ENVELOPE_V1
from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.errors import AdapterError, ValidationError
from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


def build_valid_wallet_source_input() -> dict:
    return {
        "wallet_id": "guardian-wallet-01",
        "network": "digibyte-mainnet",
        "asset": "DGB",
        "action": "build_transaction",
        "request_payload": {
            "recipients": [{"address": "DGB1example", "amount": "1000"}],
            "fee_policy": "normal",
        },
    }


def test_wallet_supported_actions_are_locked() -> None:
    assert SUPPORTED_WALLET_ACTIONS == (
        "build_transaction",
        "sign_transaction_request",
    )


def test_wallet_adapter_name_is_locked() -> None:
    assert WalletAdapter().name == "wallet"


def test_wallet_adapter_build_envelope_returns_valid_envelope() -> None:
    adapter = WalletAdapter()

    envelope = adapter.build_envelope(build_valid_wallet_source_input())

    assert envelope == {
        "contract_version": AI_GATEWAY_ENVELOPE_V1,
        "adapter": "wallet",
        "task_type": "wallet_operation",
        "model_family": "wallet-v1",
        "input_payload": {
            "wallet_id": "guardian-wallet-01",
            "network": "digibyte-mainnet",
            "asset": "DGB",
            "action": "build_transaction",
            "request_payload": {
                "recipients": [{"address": "DGB1example", "amount": "1000"}],
                "fee_policy": "normal",
            },
        },
    }


def test_wallet_adapter_build_envelope_rejects_unsupported_action() -> None:
    adapter = WalletAdapter()
    source_input = build_valid_wallet_source_input()
    source_input["action"] = "broadcast_transaction_request"

    with pytest.raises(AdapterError, match=ReasonID.ADAPTER_VALIDATION_FAILED.value):
        adapter.build_envelope(source_input)


def test_wallet_adapter_build_envelope_rejects_missing_required_field() -> None:
    adapter = WalletAdapter()
    source_input = build_valid_wallet_source_input()
    del source_input["wallet_id"]

    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        adapter.build_envelope(source_input)


def test_wallet_adapter_build_envelope_rejects_empty_string_field() -> None:
    adapter = WalletAdapter()
    source_input = build_valid_wallet_source_input()
    source_input["network"] = ""

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        adapter.build_envelope(source_input)


def test_wallet_adapter_build_envelope_rejects_non_dict_request_payload() -> None:
    adapter = WalletAdapter()
    source_input = build_valid_wallet_source_input()
    source_input["request_payload"] = []

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        adapter.build_envelope(source_input)


def test_wallet_adapter_build_output_accepts_valid_wallet_request() -> None:
    adapter = WalletAdapter()
    envelope = adapter.build_envelope(build_valid_wallet_source_input())

    output = adapter.build_output(envelope)

    assert output["contract_version"] == AI_GATEWAY_OUTPUT_V1
    assert output["adapter"] == "wallet"
    assert output["task_type"] == "wallet_operation"
    assert output["accepted"] is True
    assert output["reason_id"] == "ACCEPTED"
    assert output["output_payload"] == {
        "status": "accepted-candidate",
        "wallet_id": "guardian-wallet-01",
        "network": "digibyte-mainnet",
        "asset": "DGB",
        "action": "build_transaction",
        "request_payload": {
            "recipients": [{"address": "DGB1example", "amount": "1000"}],
            "fee_policy": "normal",
        },
    }
    assert len(output["context_hash"]) == 64


def test_wallet_adapter_output_is_deterministic() -> None:
    adapter = WalletAdapter()
    envelope = adapter.build_envelope(build_valid_wallet_source_input())

    first = adapter.build_output(envelope)
    second = adapter.build_output(envelope)

    assert first == second


def test_gateway_process_accepts_valid_wallet_request() -> None:
    registry = AdapterRegistry()
    registry.register("wallet", WalletAdapter())
    gateway = AIGateway(registry)

    output = gateway.process("wallet", build_valid_wallet_source_input())

    assert output["contract_version"] == "ai_gateway_output_v1"
    assert output["adapter"] == "wallet"
    assert output["task_type"] == "wallet_operation"
    assert output["accepted"] is True
    assert output["reason_id"] == "ACCEPTED"
    assert output["output_payload"]["action"] == "build_transaction"
    assert len(output["context_hash"]) == 64


def test_wallet_adapter_build_envelope_rejects_non_dict_source_input() -> None:
    adapter = WalletAdapter()

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        adapter.build_envelope("invalid")  # type: ignore[arg-type]


def test_gateway_process_rejects_unsupported_wallet_action_fail_closed() -> None:
    registry = AdapterRegistry()
    registry.register("wallet", WalletAdapter())
    gateway = AIGateway(registry)

    source_input = build_valid_wallet_source_input()
    source_input["action"] = "broadcast_transaction_request"

    output = gateway.process("wallet", source_input)

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value
    assert output["output_payload"] == {}
    assert output["context_hash"] == ""
