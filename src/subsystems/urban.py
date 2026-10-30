"""
Urban Growth & Building Lifecycle Subsystem.
Manages daily structural degradation, maintenance payments,
adaptive building repurposing, and responsive civic crisis planning.
"""
from typing import Any, Dict, Optional
from src.core.subsystem import ISimulationSubsystem, TickStage
from src.core.context import WorldContext
from src.world.urban_growth import (
    UrbanGrowthEngine,
    BuildingRepurposingEngine,
    ResponsiveCivicPlanningEngine,
)


class UrbanLifecycleSubsystem(ISimulationSubsystem):
    subsystem_id = "subsystem_urban_lifecycle"
    name = "Urban Lifecycle & Adaptive Repurposing Subsystem"
    tick_stage = TickStage.POST_TICK_MAINTENANCE
    tick_frequency = 1440  # Daily evaluation
    execution_priority = 30
    is_enabled = True

    def __init__(self):
        self.urban_growth_engine: Optional[UrbanGrowthEngine] = None
        self.building_repurposing_engine: Optional[BuildingRepurposingEngine] = None
        self.civic_planning_engine: Optional[ResponsiveCivicPlanningEngine] = None

    def initialize(self, context: WorldContext) -> None:
        self.urban_growth_engine = UrbanGrowthEngine(
            urban_planning_config=context.settings.get("urban_planning"),
            placement_rules=context.settings.get("placement_rules"),
            blueprints_config=context.settings.get("building_blueprints")
        )
        self.building_repurposing_engine = BuildingRepurposingEngine(
            mutation_rules_config=context.settings.get("mutation_rules")
        )
        self.civic_planning_engine = ResponsiveCivicPlanningEngine(
            civic_policies_config=context.settings.get("civic_crisis_policies"),
            urban_growth_engine=self.urban_growth_engine
        )

        context.register_service("urban_growth_engine", self.urban_growth_engine)
        context.register_service("building_repurposing_engine", self.building_repurposing_engine)
        context.register_service("civic_planning_engine", self.civic_planning_engine)

    def on_tick(self, tick: int, context: WorldContext) -> None:
        if tick <= 0:
            return

        for sett in context.settlements.values():
            # A. Daily wear-and-tear degradation & maintenance
            if self.urban_growth_engine:
                self.urban_growth_engine.process_daily_lifecycle(
                    settlement=sett,
                    npcs=context.npcs,
                    municipal_treasury=context.municipal_treasury,
                    current_tick=tick
                )

            # B. Adaptive Building Repurposing (Failing shops -> illicit vice dens, gentrification)
            if self.building_repurposing_engine:
                for bldg in list(sett.buildings.values()):
                    owner = context.npcs.get(bldg.owner_id) if bldg.owner_id else None
                    mutation_res = self.building_repurposing_engine.evaluate_and_repurpose_building(
                        building=bldg,
                        owner=owner,
                        settlement=sett,
                        objects_dict=context.objects,
                        npcs=context.npcs,
                        current_tick=tick
                    )
                    if mutation_res:
                        context.publish_event(
                            event_type="building_repurposed",
                            source_id="building_repurposing_engine",
                            payload=mutation_res
                        )

            # C. Responsive Civic Crisis Planning (Emergency clinics, watchtowers, checkpoints)
            if self.civic_planning_engine:
                mitigations = self.civic_planning_engine.evaluate_and_mitigate_crises(
                    settlement=sett,
                    municipal_treasury=context.municipal_treasury,
                    npcs=context.npcs,
                    objects_dict=context.objects,
                    spatial_graph=context.spatial_graph,
                    event_history=context.event_bus.events,
                    current_tick=tick
                )
                for m in mitigations:
                    context.publish_event(
                        event_type="civic_crisis_mitigated",
                        source_id="responsive_civic_planning_engine",
                        payload=m
                    )
