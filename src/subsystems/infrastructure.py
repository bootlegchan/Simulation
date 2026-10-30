"""
Infrastructure & Sanitation Subsystem.
Manages water source silt accumulation, purity decay, and street drainage conditions.
"""
from typing import Any, Dict, Optional
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.world.climate_and_infrastructure import InfrastructureSanitationEngine


class InfrastructureSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_infrastructure"
    name = "Infrastructure & Sanitation Subsystem"
    tick_stage = TickStage.PRE_TICK
    tick_frequency = 1440  # Daily evaluation
    execution_priority = 20
    is_enabled = True

    def __init__(self):
        self.sanitation_engine: Optional[InfrastructureSanitationEngine] = None

    def initialize(self, context: WorldContext) -> None:
        infra_cfg = context.settings.get("infrastructure_decay")
        self.sanitation_engine = InfrastructureSanitationEngine(infra_cfg)
        context.register_service("sanitation_engine", self.sanitation_engine)

    def on_tick(self, tick: int, context: WorldContext) -> None:
        if self.sanitation_engine and tick > 0:
            self.sanitation_engine.process_daily_infrastructure_decay(context.objects, tick)
