"""
Politics, Town Council, Municipal Decrees, and Courtroom Trials Subsystem.
Coordinates legislative councils, political faction agendas, labor strikes, and judicial trials.
"""
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.society.factions import FactionPoliticalEngine
from src.society.municipal_decrees import MunicipalDecreeEngine

class PoliticsAndJusticeSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_politics_and_justice"
    name = "Politics, Factions, and Justice Subsystem"
    tick_stage = TickStage.POST_TICK_MAINTENANCE
    tick_frequency = 1440
    execution_priority = 25
    is_enabled = True

    def __init__(self):
        self.faction_engine = FactionPoliticalEngine.get_instance()
        self.decree_engine = MunicipalDecreeEngine.get_instance()

    def initialize(self, context: WorldContext) -> None:
        context.register_service("faction_political_engine", self.faction_engine)
        context.register_service("municipal_decree_engine", self.decree_engine)
        self.faction_engine.auto_discover_members(context)

    def on_tick(self, tick: int, context: WorldContext) -> None:
        self.on_tick_adaptive(tick, context, delta_ticks=1)

    def on_tick_adaptive(self, tick: int, context: WorldContext, delta_ticks: int = 1) -> None:
        # 1. Judicial Lawsuit Trials (every 2,880 ticks / 2 days)
        court_eng = context.get_service("courtroom_lawsuit_engine")
        is_court_due = tick > 0 and (
            tick % 2880 == 0 or (delta_ticks > 1 and (tick // 2880 != (tick - delta_ticks) // 2880))
        )
        if court_eng and court_eng.active_lawsuits and is_court_due:
            magistrate = context.find_npc_by_role(["magistrate", "mayor", "sheriff"])
            if magistrate:
                for suit_id in list(court_eng.active_lawsuits.keys()):
                    court_eng.conduct_court_trial(suit_id, magistrate, context, tick)

        # 2. Daily Political Faction Agitation & Decree Lifecycles (every 1,440 ticks / 1 day)
        is_daily_due = tick > 0 and (
            tick % 1440 == 0 or (delta_ticks > 1 and (tick // 1440 != (tick - delta_ticks) // 1440))
        )
        if is_daily_due:
            # Process expired decrees
            self.decree_engine.process_daily_decree_cycles(context.npcs, tick, context=context)

            # Evaluate faction grievances and labor strikes
            self.faction_engine.evaluate_daily_faction_agitation(self.faction_engine.factions, context.npcs, context, tick)
            self.faction_engine.process_daily_grievance_decay(self.faction_engine.factions)

        # 3. Weekly Town Council Legislative Session (every 10,080 ticks / 7 days)
        is_council_due = tick > 0 and (
            tick % 10080 == 0 or (delta_ticks > 1 and (tick // 10080 != (tick - delta_ticks) // 10080))
        )
        if is_council_due:
            self.decree_engine.convene_town_council(context, tick)
