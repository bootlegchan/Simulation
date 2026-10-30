from src.api.dtos import (
    SpatialNodeDTO,
    SpatialGraphDTO,
    NPCVisualDTO,
    InteractiveObjectDTO,
    WorldStateDTO,
    EventDTO,
    SimulationTickBatchDTO,
    NPCAttributeMutationDTO,
    NPCForceActionDTO,
    ObjectMutationDTO,
    EnvironmentMutationDTO,
    EventInjectionDTO,
    StateDeltaDTO,
    BridgeRPCCommandDTO,
    BridgeRPCResponseDTO,
)
from src.api.bridge import StateMutator

def __getattr__(name: str):
    if name in ("create_app", "ControlRequest", "ConnectionManager"):
        from src.api.router import create_app, ControlRequest, ConnectionManager
        mapping = {
            "create_app": create_app,
            "ControlRequest": ControlRequest,
            "ConnectionManager": ConnectionManager,
        }
        return mapping[name]
    elif name == "SimulationRunner":
        from src.simulation.runner import SimulationRunner
        return SimulationRunner
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "SpatialNodeDTO",
    "SpatialGraphDTO",
    "NPCVisualDTO",
    "InteractiveObjectDTO",
    "WorldStateDTO",
    "EventDTO",
    "SimulationTickBatchDTO",
    "NPCAttributeMutationDTO",
    "NPCForceActionDTO",
    "ObjectMutationDTO",
    "EnvironmentMutationDTO",
    "EventInjectionDTO",
    "StateDeltaDTO",
    "BridgeRPCCommandDTO",
    "BridgeRPCResponseDTO",
    "StateMutator",
    "SimulationRunner",
    "create_app",
    "ControlRequest",
    "ConnectionManager",
]
