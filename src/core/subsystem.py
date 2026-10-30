"""
Simulation Subsystem Pipeline Architecture.
Provides lifecycle contracts, execution stages, frequency scheduling,
and the SubsystemPipelineManager to eliminate monolithic engine coupling.
"""
from abc import ABC, abstractmethod
from enum import Enum
import importlib
from typing import Any, Dict, List, Optional, Type


class TickStage(Enum):
    """Execution stages executed in strict topological order within a single simulation tick."""
    PRE_TICK = "PRE_TICK"                      # Environmental conditions, climate, omens, resource replenishment
    COGNITIVE_DECISION = "COGNITIVE_DECISION"  # Senses, fog-of-war, utility evaluation, habituation, goal planning
    EXECUTION_ACTION = "EXECUTION_ACTION"      # Movement steering, action execution, market trades, rites
    POST_TICK_MAINTENANCE = "POST_TICK"        # Spoilage, debt accrual, building degradation, adaptive repurposing, crisis mitigations


class TickFrequency(Enum):
    """Standard tick frequency intervals for subsystem execution."""
    EVERY_TICK = 1
    HOURLY = 60
    DAILY = 1440
    WEEKLY = 10080
    SEASONAL = 129600


class ISimulationSubsystem(ABC):
    """
    Standard interface for all modular simulation subsystems.
    Subsystems declare their execution stage, frequency, and priority,
    allowing the engine to remain a lightweight dispatch kernel.
    """

    subsystem_id: str = "base_subsystem"
    name: str = "Base Simulation Subsystem"
    tick_stage: TickStage = TickStage.POST_TICK_MAINTENANCE
    tick_frequency: int = 1
    execution_priority: int = 100  # Lower integer executes first within stage
    is_enabled: bool = True

    @abstractmethod
    def initialize(self, context: Any) -> None:
        """Called once during engine initialization to wire services, state, and event listeners."""
        pass

    @abstractmethod
    def on_tick(self, tick: int, context: Any) -> None:
        """Executes subsystem domain logic when scheduled for the current tick."""
        pass

    def handle_event(self, event: Any, context: Any) -> None:
        """Optional hook for reacting to asynchronous DomainEvents broadcast on the EventBus."""
        pass

    def save_state(self) -> Dict[str, Any]:
        """Serializes subsystem-specific runtime state for snapshot persistence."""
        return {}

    def load_state(self, data: Dict[str, Any]) -> None:
        """Deserializes subsystem-specific runtime state from snapshot."""
        pass


class SubsystemPipelineManager:
    """
    Manages the lifecycle, topological ordering, and phased execution
    of all registered simulation subsystems. Completely data-driven via manifest.
    """

    def __init__(self):
        self.subsystems: Dict[str, ISimulationSubsystem] = {}
        self._stage_buckets: Dict[TickStage, List[ISimulationSubsystem]] = {
            stage: [] for stage in TickStage
        }

    def register_subsystem(self, subsystem: ISimulationSubsystem) -> None:
        """Registers a subsystem and places it in the appropriate sorted execution bucket."""
        self.subsystems[subsystem.subsystem_id] = subsystem
        self._rebuild_buckets()

    def unregister_subsystem(self, subsystem_id: str) -> Optional[ISimulationSubsystem]:
        """Removes a subsystem by ID."""
        removed = self.subsystems.pop(subsystem_id, None)
        if removed:
            self._rebuild_buckets()
        return removed

    def get_subsystem(self, subsystem_id: str) -> Optional[ISimulationSubsystem]:
        """Retrieves a registered subsystem by its unique ID."""
        return self.subsystems.get(subsystem_id)

    def _rebuild_buckets(self) -> None:
        """Re-sorts all stage buckets by execution priority."""
        for stage in TickStage:
            self._stage_buckets[stage] = [
                sub for sub in self.subsystems.values()
                if sub.tick_stage == stage and sub.is_enabled
            ]
            self._stage_buckets[stage].sort(key=lambda s: s.execution_priority)

    def load_from_manifest(self, manifest_data: Dict[str, Any], context: Any) -> int:
        """
        Dynamically instantiates and registers subsystems declared in an external JSON manifest.
        Ensures zero hardcoding in the core engine.
        """
        subsystems_cfg = manifest_data.get("subsystems", {})
        loaded_count = 0

        for sub_id, cfg in subsystems_cfg.items():
            if not cfg.get("enabled", True):
                continue

            module_path = cfg.get("module")
            class_name = cfg.get("class")
            if not module_path or not class_name:
                continue

            try:
                mod = importlib.import_module(module_path)
                cls: Type[ISimulationSubsystem] = getattr(mod, class_name)
                instance = cls()
                instance.subsystem_id = sub_id

                if "name" in cfg:
                    instance.name = cfg["name"]
                if "priority" in cfg:
                    instance.execution_priority = int(cfg["priority"])
                if "frequency" in cfg:
                    instance.tick_frequency = int(cfg["frequency"])
                if "stage" in cfg:
                    stage_str = cfg["stage"]
                    if hasattr(TickStage, stage_str):
                        instance.tick_stage = getattr(TickStage, stage_str)

                instance.initialize(context)
                self.register_subsystem(instance)
                loaded_count += 1
            except Exception as e:
                raise RuntimeError(f"Failed to load subsystem '{sub_id}' ({module_path}.{class_name}): {e}")

        return loaded_count

    def initialize_all(self, context: Any) -> None:
        """Initializes all registered subsystems with the shared WorldContext."""
        for sub in self.subsystems.values():
            sub.initialize(context)

    def dispatch_tick(self, tick: int, context: Any) -> None:
        """
        Dispatches tick execution in strict topological stage order:
        PRE_TICK -> COGNITIVE_DECISION -> EXECUTION_ACTION -> POST_TICK_MAINTENANCE.
        Only invokes subsystems whose tick frequency interval matches the current tick.
        """
        for stage in (
            TickStage.PRE_TICK,
            TickStage.COGNITIVE_DECISION,
            TickStage.EXECUTION_ACTION,
            TickStage.POST_TICK_MAINTENANCE,
        ):
            bucket = self._stage_buckets.get(stage, [])
            for subsystem in bucket:
                if not subsystem.is_enabled:
                    continue

                freq = max(1, subsystem.tick_frequency)
                if tick % freq == 0:
                    subsystem.on_tick(tick, context)

    def broadcast_event(self, event: Any, context: Any) -> None:
        """Broadcasts a domain event to all registered subsystems."""
        for sub in self.subsystems.values():
            if sub.is_enabled:
                sub.handle_event(event, context)

    def save_all_states(self) -> Dict[str, Any]:
        """Collects runtime state dictionaries from all registered subsystems."""
        return {
            sub_id: sub.save_state()
            for sub_id, sub in self.subsystems.items()
        }

    def load_all_states(self, states_data: Dict[str, Any]) -> None:
        """Restores runtime state dictionaries across all registered subsystems."""
        for sub_id, state in states_data.items():
            if sub_id in self.subsystems:
                self.subsystems[sub_id].load_state(state)
