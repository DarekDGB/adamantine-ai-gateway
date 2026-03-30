from ai_gateway.errors import AdapterError, ContractError, ValidationError
from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


class InvalidEnvelopeContractAdapter:
    @property
    def name(self) -> str:
        return "bad-envelope-contract"

    def build_envelope(self, source_input: dict) -> dict:
        raise ContractError(ReasonID.INVALID_ENVELOPE.value)

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class InvalidOutputContractAdapter:
    @property
    def name(self) -> str:
        return "bad-output-contract"

    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": self.name,
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"candidate_id": "abc123"},
        }

    def build_output(self, envelope: dict) -> dict:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)


class MissingOutputFieldAdapter:
    @property
    def name(self) -> str:
        return "missing-output-field"

    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": self.name,
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"candidate_id": "abc123"},
        }

    def build_output(self, envelope: dict) -> dict:
        raise ValidationError(ReasonID.MISSING_REQUIRED_FIELD.value)


class NonBoolAcceptedAdapter:
    @property
    def name(self) -> str:
        return "non-bool-accepted"

    def build_envelope(self, source_input: dict) -> dict:
        return {
            "contract_version": "ai_gateway_envelope_v1",
            "adapter": self.name,
            "task_type": "code_review",
            "model_family": "poi-v1",
            "input_payload": {"candidate_id": "abc123"},
        }

    def build_output(self, envelope: dict) -> dict:
        raise ContractError(ReasonID.INVALID_OUTPUT.value)


class SchemaViolationAdapter:
    @property
    def name(self) -> str:
        return "schema-violation"

    def build_envelope(self, source_input: dict) -> dict:
        raise ValidationError(ReasonID.SCHEMA_VIOLATION.value)

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class UnknownValidationErrorAdapter:
    @property
    def name(self) -> str:
        return "unknown-validation-error"

    def build_envelope(self, source_input: dict) -> dict:
        raise ValidationError("something-unmapped")

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class UnknownAdapterErrorAdapter:
    @property
    def name(self) -> str:
        return "unknown-adapter-error"

    def build_envelope(self, source_input: dict) -> dict:
        raise AdapterError("something-unmapped")

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


def test_gateway_maps_invalid_envelope_contract_to_invalid_envelope() -> None:
    registry = AdapterRegistry()
    registry.register("bad-envelope-contract", InvalidEnvelopeContractAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "bad-envelope-contract",
        {"task_type": "code_review"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.INVALID_ENVELOPE.value


def test_gateway_maps_invalid_output_contract_to_invalid_output() -> None:
    registry = AdapterRegistry()
    registry.register("bad-output-contract", InvalidOutputContractAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "bad-output-contract",
        {"task_type": "code_review"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.INVALID_OUTPUT.value


def test_gateway_maps_missing_output_field_to_missing_required_field() -> None:
    registry = AdapterRegistry()
    registry.register("missing-output-field", MissingOutputFieldAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "missing-output-field",
        {"task_type": "code_review"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.MISSING_REQUIRED_FIELD.value


def test_gateway_maps_non_bool_accepted_to_invalid_output() -> None:
    registry = AdapterRegistry()
    registry.register("non-bool-accepted", NonBoolAcceptedAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "non-bool-accepted",
        {"task_type": "code_review"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.INVALID_OUTPUT.value


def test_gateway_maps_schema_violation_to_schema_violation() -> None:
    registry = AdapterRegistry()
    registry.register("schema-violation", SchemaViolationAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "schema-violation",
        {"task_type": "code_review"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.SCHEMA_VIOLATION.value


def test_gateway_maps_unknown_validation_error_to_schema_violation_default() -> None:
    registry = AdapterRegistry()
    registry.register("unknown-validation-error", UnknownValidationErrorAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "unknown-validation-error",
        {"task_type": "code_review"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.SCHEMA_VIOLATION.value


def test_gateway_maps_unknown_adapter_error_to_adapter_validation_failed_default() -> None:
    registry = AdapterRegistry()
    registry.register("unknown-adapter-error", UnknownAdapterErrorAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "unknown-adapter-error",
        {"task_type": "code_review"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.ADAPTER_VALIDATION_FAILED.value

class UnexpectedExceptionAdapter:
    @property
    def name(self) -> str:
        return "unexpected-exception"

    def build_envelope(self, source_input: dict) -> dict:
        raise RuntimeError("boom")

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


def test_gateway_maps_unexpected_exception_to_internal_error() -> None:
    from ai_gateway.reason_ids import ReasonID

    registry = AdapterRegistry()
    registry.register("unexpected-exception", UnexpectedExceptionAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "unexpected-exception",
        {"task_type": "code_review"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.INTERNAL_ERROR.value
