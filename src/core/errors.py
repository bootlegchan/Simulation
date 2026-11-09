"""Simulation engine exception hierarchies."""

class SimulationError(Exception):
    """Base class for all simulation domain errors."""
    pass

class LifecycleError(SimulationError):
    """Raised when an operation violates simulation lifecycle state transitions."""
    pass

class ConfigurationError(SimulationError):
    """Raised when configuration schemas or data assets are malformed."""
    pass

class SpatialError(SimulationError):
    """Raised when spatial navigation, topology, or collision invariants are breached."""
    pass
