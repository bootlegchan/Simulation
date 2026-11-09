"""Modular simulation subsystem pipeline kernel with adaptive multi-rate dispatching."""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from src.core.context import WorldContext

class TickStage(Enum):
    PRE_TICK_ENVIRONMENT = "PRE_TICK_ENVIRONMENT"
    COGNITIVE_DECISION = "COGNITIVE_DECISION"
    ACTION_EXECUTION = "ACTION_EXECUTION"
    ECONOMIC_PRODUCTION = "ECONOMIC_PRODUCTION"
    SOCIAL_AND_RELATIONAL = "SOCIAL_AND_RELATIONAL"
    URBAN_METABOLISM = "URBAN_METABOLISM"
    POST_TICK_MAINTENANCE = "POST_TICK_MAINTENANCE"

class ISimulationSubsystem(ABC):
    """Abstract contract for modular simulation subsystems."""
    subsystem_id: str = "base_subsystem"
    name: str = "Base Subsystem"
    tick_stage: TickStage = TickStage.ACTION_EXECUTION
    tick_frequency: int = 1
    execution_priority: int = 50
    is_enabled: bool = True

    @abstractmethod
    def initialize(self, context: WorldContext) -> None:
        pass

    @abstractmethod
    def on_tick(self, tick: int, context: WorldContext) -> None:
        pass

    def on_tick_adaptive(self, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        """Adaptive multi-rate tick dispatching. Defaults to calling standard on_tick."""
        self.on_tick(tick, context)

class SubsystemPipelineManager:
    """Manages ordered dispatching of subsystems per tick stage."""

    def __init__(self):
        self.subsystems: List[ISimulationSubsystem] = []

    def register_subsystem(self, subsystem: ISimulationSubsystem) -> None:
        self.subsystems.append(subsystem)
        self.subsystems.sort(key=lambda s: s.execution_priority)

    def load_from_manifest(self, manifest: Dict[str, Any], context: WorldContext) -> None:
        pass

    def dispatch_stage(self, stage: TickStage, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        for sub in self.subsystems:
            if sub.is_enabled and sub.tick_stage == stage:
                freq = max(1, sub.tick_frequency)
                # True if due on this tick or boundary was crossed during delta_ticks
                is_due = (
                    freq <= 1
                    or tick % freq == 0
                    or (delta_ticks > 1 and (tick // freq != (tick - delta_ticks) // freq))
                )
                if is_due:
                    if hasattr(sub, "on_tick_adaptive"):
                        sub.on_tick_adaptive(tick, context, delta_ticks=delta_ticks)
                    else:
                        sub.on_tick(tick, context)

    def dispatch_tick(self, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        for stage in TickStage:
            self.dispatch_stage(stage, tick, context, delta_ticks=delta_ticks)
