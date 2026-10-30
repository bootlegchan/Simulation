class SimulationError(Exception):
    """Base exception for all simulation errors."""
    pass

class LifecycleError(SimulationError):
    """Errors related to simulation engine lifecycle state transitions."""
    pass

class ConfigurationError(SimulationError):
    """Errors related to file parsing, schema validation, or missing references."""
    pass

class EntityNotFoundError(SimulationError):
    """Raised when an entity ID cannot be resolved."""
    pass

class ValidationException(ConfigurationError):
    """Schema or data invariant validation failure."""
    pass
