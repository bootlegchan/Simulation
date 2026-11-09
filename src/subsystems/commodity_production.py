"""
Commodity Production & Crafting Subsystem.
Dispatches at TickStage.ECONOMIC_PRODUCTION:
Executes physical recipe transformations, manages workstation throughput,
processes periodic regional export trade caravans, and updates dynamic commodity stocks.
"""
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.economy.supply_chain import CommoditySupplyChainEngine

class CommodityProductionSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_commodity_production"
    name = "Commodity Production and Supply Chain Subsystem"
    tick_stage = TickStage.ECONOMIC_PRODUCTION
    tick_frequency = 60
    execution_priority = 18
    is_enabled = True

    def __init__(self):
        self.supply_engine = CommoditySupplyChainEngine.get_instance()
        self.production_interval: int = 60

    def initialize(self, context: WorldContext) -> None:
        context.register_service("supply_chain_engine", self.supply_engine)

    def on_tick(self, tick: int, context: WorldContext) -> None:
        self.on_tick_adaptive(tick, context, delta_ticks=1)

    def on_tick_adaptive(self, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        # Dispatched on production interval or across adaptive time leap boundaries
        is_production_due = tick > 0 and (
            tick % self.production_interval == 0 or
            (delta_ticks > 1 and (tick // self.production_interval != (tick - delta_ticks) // self.production_interval))
        )
        if is_production_due:
            self.supply_engine.process_production_cycle(context, tick, delta_ticks=delta_ticks)
            self.supply_engine.process_export_caravans(context, tick)
