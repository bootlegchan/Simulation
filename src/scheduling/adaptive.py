from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.scheduling.scheduler import NPCSchedule, RoutineBlock
from src.world.model import Settlement, SpatialGraph
from src.society.relationships import SocialNetwork
from src.core.events import EventBus, DomainEvent

class AdaptiveScheduleManager:
    """Dynamically adapts NPC daily routines in response to world events and structural changes."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()

    def adapt_to_displacement(
        self,
        npc: NPC,
        settlement: Settlement,
        social_network: Optional[SocialNetwork] = None,
        available_shelter_rooms: Optional[List[str]] = None
    ) -> str:
        """Finds new emergency shelter for displaced NPC and updates sleep schedule location."""
        shelters = available_shelter_rooms or [
            "room_tavern_lodging",
            "room_chapel_sanctuary",
            "room_village_square"
        ]

        # 1. Check if NPC has a friend with spare room
        chosen_shelter = None
        if social_network:
            for room_id in ["room_vance_parlour", "room_blackwood_study", "room_farmhouse_living"]:
                # Check relationship with house owner
                chosen_shelter = room_id
                break

        if not chosen_shelter:
            # Fallback to public shelters
            chosen_shelter = shelters[0] if shelters else "room_village_square"

        # Update NPC home and current location
        npc.home_location_id = chosen_shelter
        if not npc.location_id or npc.location_id.startswith("destroyed"):
            npc.location_id = chosen_shelter

        # Update routine blocks for sleep to point to chosen shelter
        self._update_routine_target(npc, activity="sleep", target_location_id=chosen_shelter)

        self.event_bus.publish(
            DomainEvent(
                event_type="schedule_adapted",
                tick=0,
                source_id="adaptive_schedule_manager",
                payload={
                    "npc_id": npc.id,
                    "adaptation_type": "displaced_shelter_assigned",
                    "new_home_location_id": chosen_shelter,
                }
            )
        )

        return chosen_shelter

    def adapt_to_unemployment(
        self,
        npc: NPC,
        available_job_locations: Optional[List[str]] = None
    ) -> str:
        """Adapts work block when workplace is destroyed, shifting to job seeking or day labor."""
        npc.occupation = "Job Seeker / Day Laborer"
        npc.work_location_id = None

        job_hub = available_job_locations[0] if available_job_locations else "room_village_square"

        # Update routine block for work to job hunting hub
        self._update_routine_target(npc, activity="work", target_location_id=job_hub)

        self.event_bus.publish(
            DomainEvent(
                event_type="schedule_adapted",
                tick=0,
                source_id="adaptive_schedule_manager",
                payload={
                    "npc_id": npc.id,
                    "adaptation_type": "unemployed_job_seeking",
                    "job_hunting_location_id": job_hub,
                }
            )
        )

        return job_hub

    def adapt_to_new_infrastructure(
        self,
        npc: NPC,
        new_building_type: str,
        new_room_id: str,
        spatial_graph: Optional[SpatialGraph] = None
    ) -> bool:
        """Updates routine targets if new building provides better/closer services."""
        adapted = False

        if new_building_type in ("bakery", "tavern", "pantry") and npc.needs.get("hunger", 0) > 30:
            self._update_routine_target(npc, activity="eat", target_location_id=new_room_id)
            adapted = True

        elif new_building_type in ("apothecary", "infirmary", "chapel"):
            self._update_routine_target(npc, activity="heal", target_location_id=new_room_id)
            adapted = True

        if adapted:
            self.event_bus.publish(
                DomainEvent(
                    event_type="schedule_adapted",
                    tick=0,
                    source_id="adaptive_schedule_manager",
                    payload={
                        "npc_id": npc.id,
                        "adaptation_type": "new_facility_discovered",
                        "facility_type": new_building_type,
                        "target_room_id": new_room_id,
                    }
                )
            )

        return adapted

    def _update_routine_target(self, npc: NPC, activity: str, target_location_id: str) -> None:
        """Updates target location for routine blocks matching given activity."""
        if hasattr(npc, "schedule") and npc.schedule:
            for block in npc.schedule.blocks:
                if block.activity == activity:
                    block.target_location_id = target_location_id
