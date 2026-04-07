from ai_gateway.adapters.poi import PoIAdapter
from ai_gateway.adapters.wallet import SUPPORTED_WALLET_ACTIONS, WalletAdapter
from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


POI_SOURCE_INPUT = {
    "task_type": "code_review",
    "model_family": "poi-v1",
    "input_payload": {"action": "evaluate_candidate"},
}

WALLET_SOURCE_INPUT = {
    "wallet_id": "wallet-1",
    "network": "dgb",
    "asset": "dgb",
    "action": "build_transaction",
    "request_payload": {},
}


def _gateway() -> AIGateway:
    registry = AdapterRegistry()
    registry.register("poi", PoIAdapter())
    registry.register("wallet", WalletAdapter())
    return AIGateway(registry)


def _poi_policy_pack(*, task_types=None, model_families=None, actions=None) -> dict:
    return {
        "policypack_version": "policy_pack_v1",
        "policypack_id": "poi-runtime-lock",
        "policypack_version_id": "v1.0.0-lock",
        "default_decision": "deny",
        "adapter_policies": {
            "poi": {
                "allowed_task_types": task_types or ["code_review"],
                "allowed_model_families": model_families or ["poi-v1"],
                "allowed_actions": actions or ["evaluate_candidate"],
            }
        },
        "notes": "PoI manifest/runtime lock tests",
    }


def _wallet_policy_pack(*, task_types=None, model_families=None, actions=None) -> dict:
    return {
        "policypack_version": "policy_pack_v1",
        "policypack_id": "wallet-runtime-lock",
        "policypack_version_id": "v1.0.0-lock",
        "default_decision": "deny",
        "adapter_policies": {
            "wallet": {
                "allowed_task_types": task_types or ["wallet_operation"],
                "allowed_model_families": model_families or ["wallet-v1"],
                "allowed_actions": actions or ["build_transaction", "sign_transaction_request"],
            }
        },
        "notes": "Wallet manifest/runtime lock tests",
    }


def test_builtin_adapter_manifests_match_runtime_identity_and_output_contract() -> None:
    poi = PoIAdapter()
    wallet = WalletAdapter()

    assert poi.manifest["adapter_id"] == poi.name
    assert poi.manifest["entrypoint"] == "ai_gateway.adapters.poi.PoIAdapter"
    assert poi.manifest["output_contract"] == "ai_gateway_output_v1"

    assert wallet.manifest["adapter_id"] == wallet.name
    assert wallet.manifest["entrypoint"] == "ai_gateway.adapters.wallet.WalletAdapter"
    assert wallet.manifest["output_contract"] == "ai_gateway_output_v1"


def test_poi_manifest_declares_real_runtime_reason_ids() -> None:
    gateway = _gateway()
    manifest_reasons = set(PoIAdapter().manifest["failure_reason_ids"])

    accepted = gateway.process_with_policy("poi", POI_SOURCE_INPUT, _poi_policy_pack())
    unsupported_task = gateway.process_with_policy(
        "poi",
        {**POI_SOURCE_INPUT, "task_type": "documentation"},
        _poi_policy_pack(task_types=["code_review"]),
    )
    unsupported_model = gateway.process_with_policy(
        "poi",
        {**POI_SOURCE_INPUT, "model_family": "other-model"},
        _poi_policy_pack(model_families=["poi-v1"]),
    )
    denied_action = gateway.process_with_policy(
        "poi",
        {**POI_SOURCE_INPUT, "input_payload": {"action": "other-action"}},
        _poi_policy_pack(actions=["evaluate_candidate"]),
    )

    assert accepted["reason_id"] == "ACCEPTED"
    assert accepted["reason_id"] in manifest_reasons

    assert unsupported_task["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert unsupported_task["reason_id"] in manifest_reasons

    assert unsupported_model["reason_id"] == ReasonID.UNSUPPORTED_MODEL.value
    assert unsupported_model["reason_id"] in manifest_reasons

    assert denied_action["reason_id"] == ReasonID.POLICY_DENIED.value
    assert denied_action["reason_id"] in manifest_reasons


def test_wallet_manifest_declares_real_runtime_reason_ids() -> None:
    gateway = _gateway()
    manifest_reasons = set(WalletAdapter().manifest["failure_reason_ids"])

    accepted = gateway.process_with_policy("wallet", WALLET_SOURCE_INPUT, _wallet_policy_pack())
    unsupported_task = gateway.process_with_policy(
        "wallet",
        WALLET_SOURCE_INPUT,
        _wallet_policy_pack(task_types=["other_task"]),
    )
    unsupported_model = gateway.process_with_policy(
        "wallet",
        WALLET_SOURCE_INPUT,
        _wallet_policy_pack(model_families=["other-model"]),
    )
    denied_action = gateway.process_with_policy(
        "wallet",
        {**WALLET_SOURCE_INPUT, "action": "sign_transaction_request"},
        _wallet_policy_pack(actions=["build_transaction"]),
    )

    assert accepted["reason_id"] == "ACCEPTED"
    assert accepted["reason_id"] in manifest_reasons

    assert unsupported_task["reason_id"] == ReasonID.UNSUPPORTED_TASK.value
    assert unsupported_task["reason_id"] in manifest_reasons

    assert unsupported_model["reason_id"] == ReasonID.UNSUPPORTED_MODEL.value
    assert unsupported_model["reason_id"] in manifest_reasons

    assert denied_action["reason_id"] == ReasonID.POLICY_DENIED.value
    assert denied_action["reason_id"] in manifest_reasons


def test_wallet_manifest_supported_actions_match_runtime_and_reject_unknown_action() -> None:
    manifest = WalletAdapter().manifest

    assert set(manifest["supported_actions"]) == set(SUPPORTED_WALLET_ACTIONS)

    output = _gateway().process(
        "wallet",
        {**WALLET_SOURCE_INPUT, "action": "not-supported"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value
    assert output["reason_id"] in manifest["failure_reason_ids"]
