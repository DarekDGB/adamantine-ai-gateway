from importlib import import_module, metadata
from pathlib import Path
import tomllib

import ai_gateway
from ai_gateway.gateway import AIGateway
from ai_gateway.receipt import build_receipt_v1
from ai_gateway.registry import AdapterRegistry
from ai_gateway.version import __version__


EXPECTED_ROOT_PUBLIC_API = [
    "__version__",
    "AIGateway",
    "AdapterRegistry",
    "build_receipt_v1",
]

EXPECTED_CONTRACTS_PUBLIC_API = [
    "AI_GATEWAY_ENVELOPE_V1",
    "REQUIRED_ENVELOPE_FIELDS",
    "ADAPTER_MANIFEST_V1",
    "ALLOWED_MANIFEST_FIELDS",
    "REQUIRED_MANIFEST_FIELDS",
    "AI_GATEWAY_OUTPUT_V1",
    "REQUIRED_OUTPUT_FIELDS",
    "POLICYPACK_V1",
    "REQUIRED_POLICYPACK_FIELDS",
    "ALLOWED_POLICYPACK_FIELDS",
    "ALLOWED_POLICYPACK_DEFAULT_DECISIONS",
    "REQUIRED_ADAPTER_POLICY_FIELDS",
    "ALLOWED_ADAPTER_POLICY_FIELDS",
    "AI_GATEWAY_HANDOFF_V1",
    "REQUIRED_HANDOFF_FIELDS",
    "ALLOWED_HANDOFF_FIELDS",
    "ALLOWED_HANDOFF_DECISIONS",
    "AI_GATEWAY_RECEIPT_V1",
    "ALLOWED_POLICY_DECISIONS",
    "RECEIPT_DETERMINISM_PROFILE_V1",
    "REQUIRED_RECEIPT_FIELDS",
]


def _project_version() -> str:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    pyproject_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return pyproject_data["project"]["version"]


def test_root_public_api_is_frozen() -> None:
    assert ai_gateway.__all__ == EXPECTED_ROOT_PUBLIC_API


def test_root_public_api_symbols_resolve_to_expected_objects() -> None:
    assert ai_gateway.__version__ == __version__
    assert ai_gateway.AIGateway is AIGateway
    assert ai_gateway.AdapterRegistry is AdapterRegistry
    assert ai_gateway.build_receipt_v1 is build_receipt_v1


def test_root_public_api_contains_no_duplicate_exports() -> None:
    assert len(ai_gateway.__all__) == len(set(ai_gateway.__all__))


def test_contracts_public_api_is_frozen() -> None:
    contracts_module = import_module("ai_gateway.contracts")
    assert contracts_module.__all__ == EXPECTED_CONTRACTS_PUBLIC_API


def test_contracts_public_api_contains_no_duplicate_exports() -> None:
    contracts_module = import_module("ai_gateway.contracts")
    assert len(contracts_module.__all__) == len(set(contracts_module.__all__))


def test_contracts_public_api_symbols_exist() -> None:
    contracts_module = import_module("ai_gateway.contracts")

    missing = [
        symbol for symbol in EXPECTED_CONTRACTS_PUBLIC_API if not hasattr(contracts_module, symbol)
    ]

    assert missing == []


def test_installed_package_metadata_version_matches_runtime_version() -> None:
    assert metadata.version("adamantine-ai-gateway") == __version__


def test_pyproject_version_matches_runtime_version() -> None:
    assert _project_version() == __version__
