"""
Biosphere & Environmental Climate Subsystem.
Manages micro-climate ambient/indoor thermal calculations and daily natural resource replenishment.
"""
from typing import Any, Dict, Optional
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.world.climate_and_infrastructure import MicroClimateEngine
from src.world.self_contained import SelfContainedEcosystemEngine


class BiosphereSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_biosphere"
    name = "Biosphere & Climate Subsystem"
    tick_stage = TickStage.PRE_TICK
    tick_frequency = 60  # Evaluates hourly (every 60 ticks)
    execution_priority = 10
    is_enabled = True

    def __init__(self):
        self.climate_engine: Optional[MicroClimateEngine] = None
        self.ecosystem_engine: Optional[SelfContainedEcosystemEngine] = None

    def initialize(self, context: WorldContext) -> None:
        climate_cfg = context.settings.get("climate_zones")
        self.climate_engine = MicroClimateEngine(climate_cfg)
        self.ecosystem_engine = SelfContainedEcosystemEngine()

        context.register_service("micro_climate_engine", self.climate_engine)
        context.register_service("ecosystem_engine", self.ecosystem_engine)

    def on_tick(self, tick: int, context: WorldContext) -> None:
        # 1. Micro-climate room temperature and weather updates (hourly)
        if self.climate_engine:
            hour = (tick // 60) % 24
            season = "WINTER" if (tick // 1440) % 4 == 0 else "SPRING"
            ambient_temp = self.climate_engine.calculate_ambient_temperature(season, hour)

            # Check thermal comfort for all occupied rooms
            for settlement in context.settlements.values():
                for bldg in settlement.buildings.values():
                    for room in bldg.rooms.values():
                        if room.occupant_ids:
                            indoor_temp = self.climate_engine.calculate_indoor_room_temperature(
                                room=room,
                                building=bldg,
                                season=season,
                                hour=hour,
                                objects_dict=context.objects
                            )
                            # Apply thermal consequences to occupants
                            for occ_id in room.occupant_ids:
                                occ = context.get_npc(occ_id)
                                if occ:
                                    self.climate_engine.apply_temperature_consequences(occ, indoor_temp)

        # 2. Daily natural resource replenishment (at 1440 ticks)
        if self.ecosystem_engine and tick > 0 and tick % 1440 == 0:
            self.ecosystem_engine.process_daily_replenishment()
