from ai_gateway.gateway import AIGateway
from ai_gateway.reason_ids import ReasonID
from ai_gateway.registry import AdapterRegistry


class InvalidEnvelopeContractAdapter:
    @property
    def name(self) -> str:
        return "bad-envelope-contract"

    def build_envelope(self, source_input: dict) -> dict:
        raise ValueError("invalid envelope contract_version")

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
        raise ValueError("invalid output contract_version")


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
        raise ValueError("missing required output field: context_hash")


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
        raise ValueError("accepted must be a bool")


class SchemaViolationAdapter:
    @property
    def name(self) -> str:
        return "schema-violation"

    def build_envelope(self, source_input: dict) -> dict:
        raise ValueError("value must be a dict")

    def build_output(self, envelope: dict) -> dict:
        raise AssertionError("should not be called")


class UnknownValueErrorAdapter:
    @property
    def name(self) -> str:
        return "unknown-value-error"

    def build_envelope(self, source_input: dict) -> dict:
        raise ValueError("something unmapped happened")

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


def test_gateway_maps_unknown_value_error_to_internal_error() -> None:
    registry = AdapterRegistry()
    registry.register("unknown-value-error", UnknownValueErrorAdapter())
    gateway = AIGateway(registry)

    output = gateway.process(
        "unknown-value-error",
        {"task_type": "code_review"},
    )

    assert output["accepted"] is False
    assert output["reason_id"] == ReasonID.INTERNAL_ERROR.value
