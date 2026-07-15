from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from ai_gateway.canonical import canonical_json_bytes
from ai_gateway.contracts.policy_binding_v1 import (
    AI_GATEWAY_POLICY_BINDING_V1,
    MAX_EXACT_JSON_INTEGER_BITS,
    MAX_POLICY_BINDING_ID_LENGTH,
    MAX_POLICY_SNAPSHOT_CANONICAL_BYTES,
    MAX_POLICY_SNAPSHOT_NODES,
    POLICY_BINDING_POLICY_PACK_CONTRACT_V1,
)
from ai_gateway.contracts.receipt_v1 import RECEIPT_DETERMINISM_PROFILE_V1
from ai_gateway.errors import ContractError, ValidationError
from ai_gateway.hashing import sha256_hex
from ai_gateway.reason_ids import ReasonID
from ai_gateway.validation import (
    MAX_DEPTH,
    MAX_KEYS,
    MAX_LIST_ITEMS,
    MAX_STRING_LENGTH,
    validate_envelope_v1,
    validate_handoff_v1,
    validate_output_v1,
    validate_policy_binding_v1,
    validate_policypack_v1,
    validate_receipt_v1,
)


@dataclass(frozen=True)
class _CapturedPolicyPackV1:
    canonical_bytes: bytes
    policy_pack_id: str
    policy_pack_version_id: str
    policy_pack_hash: str


@dataclass
class _PreflightBudget:
    nodes: int = 0
    text_bytes: int = 0


def _schema_violation() -> ValidationError:
    return ValidationError(ReasonID.SCHEMA_VIOLATION.value)


def _count_text(value: str, budget: _PreflightBudget) -> None:
    if len(value) > MAX_STRING_LENGTH:
        raise _schema_violation()
    try:
        encoded_length = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise _schema_violation() from exc
    budget.text_bytes += encoded_length
    if budget.text_bytes > MAX_POLICY_SNAPSHOT_CANONICAL_BYTES:
        raise _schema_violation()


def _preflight_exact_json(
    value: Any,
    *,
    depth: int,
    active_containers: set[int],
    budget: _PreflightBudget,
) -> None:
    if depth > MAX_DEPTH:
        raise _schema_violation()

    budget.nodes += 1
    if budget.nodes > MAX_POLICY_SNAPSHOT_NODES:
        raise _schema_violation()

    if type(value) is str:
        _count_text(value, budget)
        return

    if value is None or type(value) is bool:
        return

    if type(value) is int:
        if abs(value).bit_length() > MAX_EXACT_JSON_INTEGER_BITS:
            raise _schema_violation()
        budget.text_bytes += len(str(value))
        if budget.text_bytes > MAX_POLICY_SNAPSHOT_CANONICAL_BYTES:
            raise _schema_violation()
        return

    if type(value) is list:
        if len(value) > MAX_LIST_ITEMS:
            raise _schema_violation()
        identity = id(value)
        if identity in active_containers:
            raise _schema_violation()
        active_containers.add(identity)
        try:
            for item in value:
                _preflight_exact_json(
                    item,
                    depth=depth + 1,
                    active_containers=active_containers,
                    budget=budget,
                )
        finally:
            active_containers.remove(identity)
        return

    if type(value) is dict:
        if len(value) > MAX_KEYS:
            raise _schema_violation()
        identity = id(value)
        if identity in active_containers:
            raise _schema_violation()
        active_containers.add(identity)
        try:
            for key, child in value.items():
                if type(key) is not str:
                    raise _schema_violation()
                _count_text(key, budget)
                _preflight_exact_json(
                    child,
                    depth=depth + 1,
                    active_containers=active_containers,
                    budget=budget,
                )
        finally:
            active_containers.remove(identity)
        return

    raise _schema_violation()


def _capture_policy_pack_v1(policy_pack: Any) -> _CapturedPolicyPackV1:
    _preflight_exact_json(
        policy_pack,
        depth=0,
        active_containers=set(),
        budget=_PreflightBudget(),
    )

    validated = validate_policypack_v1(policy_pack)
    policy_pack_id = validated["policypack_id"]
    policy_pack_version_id = validated["policypack_version_id"]
    if len(policy_pack_id) > MAX_POLICY_BINDING_ID_LENGTH:
        raise _schema_violation()
    if len(policy_pack_version_id) > MAX_POLICY_BINDING_ID_LENGTH:
        raise _schema_violation()

    try:
        canonical_bytes = canonical_json_bytes(validated)
    except (TypeError, ValueError, UnicodeError, OverflowError) as exc:
        raise _schema_violation() from exc

    if len(canonical_bytes) > MAX_POLICY_SNAPSHOT_CANONICAL_BYTES:
        raise _schema_violation()

    policy_hash = hashlib.sha256(canonical_bytes).hexdigest()
    return _CapturedPolicyPackV1(
        canonical_bytes=canonical_bytes,
        policy_pack_id=policy_pack_id,
        policy_pack_version_id=policy_pack_version_id,
        policy_pack_hash=policy_hash,
    )


def _snapshot_exact_json_artifact(value: Any) -> Any:
    """Return a bounded built-in JSON snapshot or fail before comparisons."""

    _preflight_exact_json(
        value,
        depth=0,
        active_containers=set(),
        budget=_PreflightBudget(),
    )
    try:
        canonical_bytes = canonical_json_bytes(value)
    except (TypeError, ValueError, UnicodeError, OverflowError) as exc:
        raise _schema_violation() from exc
    if len(canonical_bytes) > MAX_POLICY_SNAPSHOT_CANONICAL_BYTES:
        raise _schema_violation()
    try:
        return json.loads(canonical_bytes.decode("utf-8"))
    except (TypeError, ValueError, UnicodeError) as exc:
        raise _schema_violation() from exc


def _materialize_policy_pack_v1(snapshot: _CapturedPolicyPackV1) -> dict:
    if type(snapshot) is not _CapturedPolicyPackV1:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)
    if type(snapshot.canonical_bytes) is not bytes:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)

    try:
        materialized = json.loads(snapshot.canonical_bytes.decode("utf-8"))
        validated = validate_policypack_v1(materialized)
        canonical_bytes = canonical_json_bytes(validated)
    except (TypeError, ValueError, UnicodeError, OverflowError) as exc:
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value) from exc

    if canonical_bytes != snapshot.canonical_bytes:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)
    if validated["policypack_id"] != snapshot.policy_pack_id:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)
    if validated["policypack_version_id"] != snapshot.policy_pack_version_id:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)
    if hashlib.sha256(canonical_bytes).hexdigest() != snapshot.policy_pack_hash:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)
    return validated


def _require_equal(actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)


def _validate_reason_semantics(output: dict, policy_decision: str) -> None:
    reason_id = output["reason_id"]
    if policy_decision == "accepted":
        _require_equal(reason_id, "ACCEPTED")
        return
    if reason_id == "ACCEPTED":
        raise ContractError(ReasonID.INVALID_OUTPUT.value)
    try:
        ReasonID(reason_id)
    except ValueError as exc:
        raise ContractError(ReasonID.INVALID_OUTPUT.value) from exc


def _build_policy_binding_v1(
    *,
    snapshot: _CapturedPolicyPackV1,
    envelope: dict,
    output: dict,
    receipt: dict,
    handoff: dict,
) -> dict:
    artifacts = _snapshot_exact_json_artifact(
        {
            "envelope": envelope,
            "output": output,
            "receipt": receipt,
            "handoff": handoff,
        }
    )
    validated_envelope = validate_envelope_v1(artifacts["envelope"])
    validated_output = validate_output_v1(artifacts["output"])
    validated_receipt = validate_receipt_v1(artifacts["receipt"])
    validated_handoff = validate_handoff_v1(artifacts["handoff"])

    policy_decision = "accepted" if validated_output["accepted"] else "rejected"
    _validate_reason_semantics(validated_output, policy_decision)

    envelope_hash = sha256_hex(validated_envelope)
    output_hash = sha256_hex(validated_output)

    _require_equal(validated_envelope["adapter"], validated_output["adapter"])
    _require_equal(validated_envelope["task_type"], validated_output["task_type"])
    _require_equal(validated_receipt["adapter_id"], validated_output["adapter"])
    _require_equal(validated_handoff["adapter"], validated_output["adapter"])
    _require_equal(validated_handoff["task_type"], validated_output["task_type"])
    _require_equal(validated_receipt["envelope_hash"], envelope_hash)
    _require_equal(validated_handoff["envelope_hash"], envelope_hash)
    _require_equal(validated_receipt["output_hash"], output_hash)
    _require_equal(validated_handoff["output_hash"], output_hash)
    _require_equal(validated_receipt["policy_decision"], policy_decision)
    _require_equal(validated_handoff["policy_decision"], policy_decision)
    _require_equal(validated_receipt["reason_id"], validated_output["reason_id"])
    _require_equal(validated_handoff["reason_id"], validated_output["reason_id"])
    _require_equal(validated_handoff["context_hash"], validated_output["context_hash"])
    _require_equal(validated_output["context_hash"], envelope_hash)
    _require_equal(
        validated_receipt["determinism_profile"],
        RECEIPT_DETERMINISM_PROFILE_V1,
    )

    binding = {
        "policy_binding_version": AI_GATEWAY_POLICY_BINDING_V1,
        "policy_pack_contract_version": POLICY_BINDING_POLICY_PACK_CONTRACT_V1,
        "policy_pack_id": snapshot.policy_pack_id,
        "policy_pack_version_id": snapshot.policy_pack_version_id,
        "policy_pack_hash": snapshot.policy_pack_hash,
        "receipt_hash": sha256_hex(validated_receipt),
        "handoff_hash": sha256_hex(validated_handoff),
    }
    return validate_policy_binding_v1(binding)
