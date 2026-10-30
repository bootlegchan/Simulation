"""
Economic Metabolism & Financial Subsystem.
Manages food inventory spoilage decay, compound debt interest,
informal credit promissory notes, and market order book clearing.
"""
from typing import Any, Dict, Optional
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.economy.spoilage import SpoilageTracker
from src.economy.credit_and_guilds import CreditInstrumentManager


class EconomySubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_economy"
    name = "Economy & Finance Subsystem"
    tick_stage = TickStage.POST_TICK_MAINTENANCE
    tick_frequency = 1  # Runs every tick for spoilage and debt
    execution_priority = 10
    is_enabled = True

    def __init__(self):
        self.credit_manager: Optional[CreditInstrumentManager] = None

    def initialize(self, context: WorldContext) -> None:
        credit_cfg = context.settings.get("credit_instruments")
        self.credit_manager = CreditInstrumentManager(credit_cfg)
        context.register_service("credit_instrument_manager", self.credit_manager)

    def on_tick(self, tick: int, context: WorldContext) -> None:
        # 1. Spoilage Decay
        for npc in context.npcs.values():
            SpoilageTracker.apply_spoilage(npc.inventory, context.item_definitions, in_pantry=False)

        # 2. Debt Interest Accrual
        context.debt_manager.accrue_interest()

        # 3. Daily Promissory Note overdue and default checks
        if self.credit_manager and tick > 0 and tick % 1440 == 0:
            self.credit_manager.process_daily_credit_checks(context.npcs, tick)
