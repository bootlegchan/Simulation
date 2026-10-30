import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.world.model import Building, Room, Settlement
from src.core.randomness import SeededRandom

@dataclass
class BuildingBlueprint:
    template_id: str
    name: str
    category: str  # CIVIC, MEDICAL, INDUSTRIAL, COMMERCIAL, RESIDENTIAL, SACRED, UNDERWORLD
    room_templates: List[Dict[str, Any]]
    object_templates: List[Dict[str, Any]]
    weather_shielding: float = 0.9

class BuildingPrefabEngine:
    """Instantiates building prefabs from blueprints directly into active settlements."""

    @staticmethod
    def instantiate_prefab(
        settlement: Settlement,
        blueprint: BuildingBlueprint,
        entry_connecting_room_id: str,
        spatial_graph: Any,
        objects_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        b_id = f"bldg_{blueprint.template_id}_{uuid.uuid4().hex[:6]}"
        created_rooms = {}
        created_room_ids = []

        # Create rooms
        for r_tmpl in blueprint.room_templates:
            r_id = f"room_{r_tmpl['id_suffix']}_{uuid.uuid4().hex[:6]}"
            room = Room(
                room_id=r_id,
                name=r_tmpl["name"],
                building_id=b_id,
                connected_room_ids=list(r_tmpl.get("internal_connections", []))
            )
            created_rooms[r_id] = room
            created_room_ids.append(r_id)

        # Connect entrance room to town plaza/street
        if created_room_ids:
            entrance_room_id = created_room_ids[0]
            created_rooms[entrance_room_id].connected_room_ids.append(entry_connecting_room_id)

        building = Building(
            building_id=b_id,
            name=blueprint.name,
            settlement_id=settlement.id,
            rooms=created_rooms
        )
        settlement.buildings[b_id] = building
        spatial_graph.build_graph({settlement.id: settlement})

        return {
            "building_id": b_id,
            "building_name": blueprint.name,
            "category": blueprint.category,
            "created_room_ids": created_room_ids
        }

class ProceduralSettlementGenerator:
    """Seed-based procedural generator assembling settlements from building blueprints."""

    @staticmethod
    def generate_procedural_settlement(
        settlement_id: str,
        settlement_name: str,
        seed: int,
        blueprints: List[BuildingBlueprint],
        population_size: int = 30
    ) -> Settlement:
        random_gen = SeededRandom(seed=seed)
        settlement = Settlement(settlement_id=settlement_id, name=settlement_name, buildings={})

        # Plaza Hub
        plaza_bldg_id = f"bldg_town_square_{seed}"
        plaza_room_id = f"room_plaza_{seed}"
        plaza_room = Room(room_id=plaza_room_id, name=f"{settlement_name} Town Square", building_id=plaza_bldg_id, connected_room_ids=[])
        plaza_bldg = Building(building_id=plaza_bldg_id, name="Central Town Square", settlement_id=settlement_id, rooms={plaza_room_id: plaza_room})
        settlement.buildings[plaza_bldg_id] = plaza_bldg

        # Instantiate blueprints
        for bp in blueprints:
            r_id = f"room_{bp.template_id}_{seed}"
            r_node = Room(room_id=r_id, name=f"{bp.name} Main Hall", building_id=f"bldg_{bp.template_id}_{seed}", connected_room_ids=[plaza_room_id])
            plaza_room.connected_room_ids.append(r_id)
            bldg = Building(building_id=f"bldg_{bp.template_id}_{seed}", name=bp.name, settlement_id=settlement_id, rooms={r_id: r_node})
            settlement.buildings[bldg.id] = bldg

        return settlement
