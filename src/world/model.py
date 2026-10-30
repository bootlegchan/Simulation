from typing import Any, Dict, List, Optional
from collections import deque

class Room:
    def __init__(
        self,
        room_id: str,
        name: str,
        building_id: str,
        connected_room_ids: Optional[List[str]] = None,
        occupant_ids: Optional[List[str]] = None,
        contained_object_ids: Optional[List[str]] = None,
        archetype: str = "GENERAL",
    ):
        self.id = room_id
        self.name = name
        self.building_id = building_id
        self.connected_room_ids = connected_room_ids if connected_room_ids is not None else []
        self.occupant_ids = occupant_ids if occupant_ids is not None else []
        self.contained_object_ids = contained_object_ids if contained_object_ids is not None else []
        self.archetype = archetype

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "building_id": self.building_id,
            "connected_room_ids": self.connected_room_ids,
            "occupant_ids": self.occupant_ids,
            "contained_object_ids": self.contained_object_ids,
            "archetype": self.archetype,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Room":
        return cls(
            room_id=data["id"],
            name=data["name"],
            building_id=data.get("building_id", ""),
            connected_room_ids=data.get("connected_room_ids", []),
            occupant_ids=data.get("occupant_ids", []),
            contained_object_ids=data.get("contained_object_ids", []),
            archetype=data.get("archetype", "GENERAL"),
        )

class Building:
    def __init__(
        self,
        building_id: str,
        name: str,
        settlement_id: str,
        rooms: Optional[Dict[str, Room]] = None,
        category: str = "RESIDENTIAL",
        structural_integrity: float = 100.0,
        condition_state: str = "MAINTAINED",
        district_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        maintenance_budget: float = 5.0,
        last_maintained_tick: int = 0
    ):
        self.id = building_id
        self.name = name
        self.settlement_id = settlement_id
        self.rooms: Dict[str, Room] = rooms if rooms is not None else {}
        self.category = category
        self.structural_integrity = max(0.0, min(100.0, structural_integrity))
        self.condition_state = condition_state
        self.district_id = district_id
        self.owner_id = owner_id
        self.maintenance_budget = maintenance_budget
        self.last_maintained_tick = last_maintained_tick

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "settlement_id": self.settlement_id,
            "rooms": {r_id: r.to_dict() for r_id, r in self.rooms.items()},
            "category": self.category,
            "structural_integrity": round(self.structural_integrity, 1),
            "condition_state": self.condition_state,
            "district_id": self.district_id,
            "owner_id": self.owner_id,
            "maintenance_budget": self.maintenance_budget,
            "last_maintained_tick": self.last_maintained_tick,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Building":
        rooms = {r_id: Room.from_dict(r_data) for r_id, r_data in data.get("rooms", {}).items()}
        
        category = data.get("category")
        b_name = data.get("name", "").lower()
        b_id = data.get("id", "").lower()

        if not category:
            if any(k in b_name or k in b_id for k in ["mayor", "town_hall", "town hall", "council", "guard", "dungeon", "jail", "garrison", "town_square"]):
                category = "CIVIC"
            elif any(k in b_name or k in b_id for k in ["infirmary", "hospital", "apothecary", "healing", "clinic"]):
                category = "MEDICAL"
            elif any(k in b_name or k in b_id for k in ["forge", "smithy", "mill", "quarry", "granary", "carpenter", "tailor", "cobbler", "weaver"]):
                category = "INDUSTRIAL"
            elif any(k in b_name or k in b_id for k in ["chapel", "church", "sanctuary", "cemetery"]):
                category = "SACRED"
            elif any(k in b_name or k in b_id for k in ["vice", "gambling", "underworld", "smuggler", "outlaw", "hideout"]):
                category = "UNDERWORLD"
            elif any(k in b_name or k in b_id for k in ["store", "shop", "market", "tavern", "inn", "bar"]):
                category = "COMMERCIAL"
            else:
                category = "RESIDENTIAL"

        district_id = data.get("district_id")
        if not district_id:
            if category == "CIVIC":
                district_id = "DISTRICT_CIVIC_MARKET"
            elif category == "COMMERCIAL":
                district_id = "DISTRICT_COMMERCIAL_ARTISAN"
            elif category == "INDUSTRIAL":
                district_id = "DISTRICT_INDUSTRIAL_OUTSKIRTS"
            elif category == "SACRED":
                district_id = "DISTRICT_SACRED"
            elif category == "UNDERWORLD":
                district_id = "DISTRICT_UNDERWORLD_SLUMS"
            else:
                district_id = "DISTRICT_RESIDENTIAL"

        return cls(
            building_id=data["id"],
            name=data["name"],
            settlement_id=data.get("settlement_id", ""),
            rooms=rooms,
            category=category,
            structural_integrity=data.get("structural_integrity", 100.0),
            condition_state=data.get("condition_state", "MAINTAINED"),
            district_id=district_id,
            owner_id=data.get("owner_id"),
            maintenance_budget=data.get("maintenance_budget", 5.0),
            last_maintained_tick=data.get("last_maintained_tick", 0)
        )

class Settlement:
    def __init__(self, settlement_id: str, name: str, buildings: Optional[Dict[str, Building]] = None):
        self.id = settlement_id
        self.name = name
        self.buildings: Dict[str, Building] = buildings if buildings is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "buildings": {b_id: b.to_dict() for b_id, b in self.buildings.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settlement":
        buildings = {b_id: Building.from_dict(b_data) for b_id, b_data in data.get("buildings", {}).items()}
        return cls(
            settlement_id=data["id"],
            name=data["name"],
            buildings=buildings
        )

class SpatialGraph:
    """Graph pathfinding across room nodes."""

    def __init__(self):
        self.adj: Dict[str, List[str]] = {}

    def build_graph(self, settlements: Dict[str, Settlement]) -> None:
        self.adj.clear()
        for s in settlements.values():
            for b in s.buildings.values():
                for r_id, r in b.rooms.items():
                    if r_id not in self.adj:
                        self.adj[r_id] = []
                    for neighbor in r.connected_room_ids:
                        if neighbor not in self.adj[r_id]:
                            self.adj[r_id].append(neighbor)

    def find_shortest_path(self, start_room_id: str, target_room_id: str) -> Optional[List[str]]:
        if start_room_id == target_room_id:
            return [start_room_id]
        if start_room_id not in self.adj or target_room_id not in self.adj:
            return None

        visited = {start_room_id}
        queue = deque([[start_room_id]])

        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr == target_room_id:
                return path

            for neighbor in self.adj.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)

        return None
