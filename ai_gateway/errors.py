class GatewayError(Exception):
    """Base class for all gateway errors."""


class ValidationError(GatewayError):
    """Raised when input validation fails."""


class ContractError(GatewayError):
    """Raised when contract structure is invalid."""


class PolicyError(GatewayError):
    """Raised when policy rejects input."""


class AdapterError(GatewayError):
    """Raised when adapter fails processing."""


class DeterminismError(GatewayError):
    """Raised when determinism constraints are violated."""
