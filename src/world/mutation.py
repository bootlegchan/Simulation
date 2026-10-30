from typing import Any, Dict, List, Optional
from src.world.model import Settlement, Building, Room, SpatialGraph
from src.world.spatial_index import SpatialGridIndex
from src.entities.npc import NPC
from src.entities.object import InteractiveObject
from src.core.events import EventBus, DomainEvent

class WorldMutationEngine:
    """Manages dynamic world mutations: building destruction, new construction, and migration."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()

    def destroy_building(
        self,
        settlement: Settlement,
        building_id: str,
        spatial_graph: SpatialGraph,
        spatial_grid: Optional[SpatialGridIndex],
        npcs: Dict[str, NPC],
        objects: Dict[str, InteractiveObject],
        fallback_room_id: str = "room_village_square"
    ) -> Dict[str, Any]:
        """Destroys a building and its rooms, evicting occupants and invalidating locations."""
        if building_id not in settlement.buildings:
            return {"success": False, "reason": "Building not found"}

        building = settlement.buildings.pop(building_id)
        destroyed_room_ids = list(building.rooms.keys())

        # Evict occupants & update affected NPCs
        displaced_npc_ids = []
        unemployed_npc_ids = []

        for room_id in destroyed_room_ids:
            for npc in npcs.values():
                # If currently in room, move to fallback
                if npc.location_id == room_id:
                    npc.location_id = fallback_room_id
                    displaced_npc_ids.append(npc.id)

                # If home was in destroyed room
                if npc.home_location_id == room_id:
                    npc.home_location_id = None
                    if npc.id not in displaced_npc_ids:
                        displaced_npc_ids.append(npc.id)

                # If workplace was in destroyed room
                if npc.work_location_id == room_id:
                    npc.work_location_id = None
                    if npc.id not in unemployed_npc_ids:
                        unemployed_npc_ids.append(npc.id)

            # Remove objects contained in destroyed rooms
            destroyed_object_ids = [oid for oid, obj in objects.items() if obj.location_id == room_id]
            for oid in destroyed_object_ids:
                objects.pop(oid, None)

        # Rebuild spatial graph & grid index
        spatial_graph.build_graph({settlement.id: settlement})
        if spatial_grid:
            spatial_grid.clear()
            for bldg in settlement.buildings.values():
                for room in bldg.rooms.values():
                    spatial_grid.insert(room.id, 0.0, 0.0)  # Re-index remaining rooms

        event_payload = {
            "building_id": building_id,
            "building_name": building.name,
            "destroyed_room_ids": destroyed_room_ids,
            "displaced_npc_ids": displaced_npc_ids,
            "unemployed_npc_ids": unemployed_npc_ids,
        }

        self.event_bus.publish(
            DomainEvent(
                event_type="building_destroyed",
                tick=0,
                source_id="world_mutation_engine",
                payload=event_payload
            )
        )

        return {"success": True, "details": event_payload}

    def construct_building(
        self,
        settlement: Settlement,
        building_data: Dict[str, Any],
        spatial_graph: SpatialGraph,
        spatial_grid: Optional[SpatialGridIndex],
        objects: Dict[str, InteractiveObject]
    ) -> Dict[str, Any]:
        """Dynamically constructs a new building with rooms and interactable objects."""
        building = Building.from_dict(building_data)
        settlement.buildings[building.id] = building

        # Register contained objects
        new_object_ids = []
        for r_id, room in building.rooms.items():
            for obj_data in room.to_dict().get("objects_to_instantiate", []):
                obj = InteractiveObject.from_dict(obj_data)
                objects[obj.id] = obj
                new_object_ids.append(obj.id)

        # Rebuild spatial structures
        spatial_graph.build_graph({settlement.id: settlement})
        if spatial_grid:
            for room in building.rooms.values():
                spatial_grid.insert(room.id, 10.0, 10.0)

        event_payload = {
            "building_id": building.id,
            "building_name": building.name,
            "room_ids": list(building.rooms.keys()),
            "new_object_ids": new_object_ids,
        }

        self.event_bus.publish(
            DomainEvent(
                event_type="building_constructed",
                tick=0,
                source_id="world_mutation_engine",
                payload=event_payload
            )
        )

        return {"success": True, "details": event_payload}

    def migrate_family_in(
        self,
        family_name: str,
        npc_instances_data: List[Dict[str, Any]],
        assigned_home_room_id: str,
        npcs: Dict[str, NPC]
    ) -> List[str]:
        """Migrates a new family/household into the settlement."""
        new_npc_ids = []
        for n_data in npc_instances_data:
            n_data["home_location_id"] = assigned_home_room_id
            n_data["location_id"] = assigned_home_room_id
            npc = NPC.from_dict(n_data)
            npcs[npc.id] = npc
            new_npc_ids.append(npc.id)

        self.event_bus.publish(
            DomainEvent(
                event_type="family_migrated_in",
                tick=0,
                source_id="world_mutation_engine",
                payload={
                    "family_name": family_name,
                    "new_npc_ids": new_npc_ids,
                    "home_room_id": assigned_home_room_id,
                }
            )
        )

        return new_npc_ids
