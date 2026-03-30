import pytest

from ai_gateway.contracts.output_v1 import AI_GATEWAY_OUTPUT_V1
from ai_gateway.contracts.receipt_v1 import (
    AI_GATEWAY_RECEIPT_V1,
    RECEIPT_DETERMINISM_PROFILE_V1,
)
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.reason_ids import ReasonID
from ai_gateway.validation import validate_receipt_v1


VALID_HASH_A = "a" * 64
VALID_HASH_B = "b" * 64


def valid_receipt() -> dict:
    return {
        "receipt_version": AI_GATEWAY_RECEIPT_V1,
        "gateway_version": "0.3.0",
        "adapter_id": "poi",
        "adapter_version": "0.3.0",
        "envelope_hash": VALID_HASH_A,
        "output_hash": VALID_HASH_B,
        "policy_decision": "accepted",
        "reason_id": "ACCEPTED",
        "created_from_contract": AI_GATEWAY_OUTPUT_V1,
        "determinism_profile": RECEIPT_DETERMINISM_PROFILE_V1,
    }


def test_validate_receipt_v1_accepts_valid_receipt() -> None:
    receipt = valid_receipt()

    validated = validate_receipt_v1(receipt)

    assert validated == receipt


def test_validate_receipt_v1_rejects_unknown_field() -> None:
    receipt = valid_receipt()
    receipt["extra"] = True

    with pytest.raises(ValidationError, match=ReasonID.SCHEMA_VIOLATION.value):
        validate_receipt_v1(receipt)


def test_validate_receipt_v1_rejects_bad_policy_decision() -> None:
    receipt = valid_receipt()
    receipt["policy_decision"] = "maybe"

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_receipt_v1(receipt)


def test_validate_receipt_v1_rejects_non_hex_hash() -> None:
    receipt = valid_receipt()
    receipt["output_hash"] = "z" * 64

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_receipt_v1(receipt)


def test_validate_receipt_v1_rejects_invalid_receipt_version() -> None:
    receipt = valid_receipt()
    receipt["receipt_version"] = "wrong"

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_receipt_v1(receipt)


def test_validate_receipt_v1_rejects_missing_required_field() -> None:
    receipt = valid_receipt()
    del receipt["created_from_contract"]

    with pytest.raises(ValidationError, match=ReasonID.MISSING_REQUIRED_FIELD.value):
        validate_receipt_v1(receipt)


def test_validate_receipt_v1_rejects_wrong_created_from_contract() -> None:
    receipt = valid_receipt()
    receipt["created_from_contract"] = "wrong_contract"

    with pytest.raises(ContractError, match=ReasonID.INVALID_OUTPUT.value):
        validate_receipt_v1(receipt)
