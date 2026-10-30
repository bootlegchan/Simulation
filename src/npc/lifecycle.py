"""
Dynamic Life Stage Aging, Marriage Contracts, and Occupational Succession.
"""
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.npc.kinship import KinshipGraph, KinshipRelation
from src.world.demographics import DemographicPyramid, LifeStage

class LifeStageEngine:
    """Manages long-term aging across simulation years, life stage transitions, and succession."""

    @staticmethod
    def process_annual_aging(
        npcs: Dict[str, NPC],
        kinship_graph: KinshipGraph,
        event_bus: Any,
        current_tick: int
    ) -> List[Dict[str, Any]]:
        events = []

        for npc in npcs.values():
            if not hasattr(npc, "age_years"):
                npc.age_years = 30

            old_stage = DemographicPyramid.get_life_stage(npc.age_years)
            npc.age_years += 1
            new_stage = DemographicPyramid.get_life_stage(npc.age_years)

            # Update capability profile
            cap = DemographicPyramid.calculate_capabilities(npc.age_years)
            npc.decay_rates["energy"] = cap.energy_decay_rate

            if old_stage != new_stage:
                transition_evt = {
                    "npc_id": npc.id,
                    "npc_name": npc.name,
                    "old_stage": old_stage.value,
                    "new_stage": new_stage.value,
                    "new_age": npc.age_years,
                    "tick": current_tick
                }
                events.append(transition_evt)

                # Occupational transition: Youth -> Adult apprentice graduation
                if old_stage == LifeStage.YOUTH and new_stage == LifeStage.ADULT:
                    if npc.occupation.startswith("Apprentice "):
                        npc.occupation = npc.occupation.replace("Apprentice ", "Journeyman ")

        return events

    @staticmethod
    def execute_marriage_contract(
        spouse_a: NPC,
        spouse_b: NPC,
        kinship_graph: KinshipGraph,
        current_tick: int
    ) -> Dict[str, Any]:
        """Binds two consenting courting NPCs in a formal marriage contract."""
        kinship_graph.register_relation(spouse_a.id, spouse_b.id, KinshipRelation.SPOUSE)

        # Merge household residential assignment
        spouse_b.home_location_id = spouse_a.home_location_id

        return {
            "spouse_a_id": spouse_a.id,
            "spouse_b_id": spouse_b.id,
            "shared_home_id": spouse_a.home_location_id,
            "tick": current_tick
        }
