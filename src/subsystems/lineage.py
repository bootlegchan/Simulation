"""
Lineage, Kinship Alliances & Dowry Subsystem.
Manages inter-clan marriage contracts, dowry transfers, and blood feuds.
"""
from typing import Any, Dict, Optional
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.society.lineage_and_superstitions import LineageAllianceEngine


class LineageAllianceSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_lineage"
    name = "Lineage Alliances & Dowry Subsystem"
    tick_stage = TickStage.POST_TICK_MAINTENANCE
    tick_frequency = 1440  # Daily evaluation
    execution_priority = 40
    is_enabled = True

    def __init__(self):
        self.lineage_engine: Optional[LineageAllianceEngine] = None

    def initialize(self, context: WorldContext) -> None:
        lineage_cfg = context.settings.get("lineage_rules")
        self.lineage_engine = LineageAllianceEngine(lineage_cfg)
        context.register_service("lineage_alliance_engine", self.lineage_engine)

    def on_tick(self, tick: int, context: WorldContext) -> None:
        pass
