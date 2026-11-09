"""Spatial model: Room, Building, Settlement, and Graph."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

@dataclass
class Room:
    id: str
    name: str
    building_id: str
    connected_room_ids: List[str] = field(default_factory=list)
    contained_object_ids: List[str] = field(default_factory=list)
    occupant_ids: List[str] = field(default_factory=list)
    archetype: str = "ROOM"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "building_id": self.building_id,
            "connected_room_ids": self.connected_room_ids,
            "contained_object_ids": self.contained_object_ids,
            "occupant_ids": self.occupant_ids,
            "archetype": self.archetype
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Room":
        return cls(
            id=data.get("id", data.get("room_id", "room")),
            name=data.get("name", "Room"),
            building_id=data.get("building_id", "bldg"),
            connected_room_ids=list(data.get("connected_room_ids", [])),
            contained_object_ids=list(data.get("contained_object_ids", [])),
            occupant_ids=list(data.get("occupant_ids", [])),
            archetype=data.get("archetype", "ROOM")
        )

@dataclass
class Building:
    id: str
    name: str
    settlement_id: str
    rooms: Dict[str, Room] = field(default_factory=dict)
    category: str = "RESIDENTIAL"
    owner_id: Optional[str] = None
    structural_integrity: float = 100.0
    condition_state: str = "PRISTINE"
    district_id: Optional[str] = None
    property_profile: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "settlement_id": self.settlement_id,
            "rooms": {r_id: r.to_dict() for r_id, r in self.rooms.items()},
            "category": self.category,
            "owner_id": self.owner_id,
            "structural_integrity": self.structural_integrity,
            "condition_state": self.condition_state,
            "district_id": self.district_id,
            "property_profile": self.property_profile
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Building":
        rooms_dict = {}
        for r_id, r_data in data.get("rooms", {}).items():
            if isinstance(r_data, dict):
                r_data.setdefault("id", r_id)
                r_data.setdefault("building_id", data.get("id", "bldg"))
                rooms_dict[r_id] = Room.from_dict(r_data)
        return cls(
            id=data.get("id", data.get("building_id", "bldg")),
            name=data.get("name", "Building"),
            settlement_id=data.get("settlement_id", "settlement"),
            rooms=rooms_dict,
            category=data.get("category", "RESIDENTIAL"),
            owner_id=data.get("owner_id"),
            structural_integrity=float(data.get("structural_integrity", 100.0)),
            condition_state=data.get("condition_state", "PRISTINE"),
            district_id=data.get("district_id"),
            property_profile=data.get("property_profile", {})
        )

@dataclass
class Settlement:
    id: str
    name: str
    buildings: Dict[str, Building] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "buildings": {b_id: b.to_dict() for b_id, b in self.buildings.items()},
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settlement":
        bldgs = {}
        for b_id, b_data in data.get("buildings", {}).items():
            if isinstance(b_data, dict):
                b_data.setdefault("id", b_id)
                b_data.setdefault("settlement_id", data.get("id", "settlement"))
                bldgs[b_id] = Building.from_dict(b_data)
        return cls(
            id=data.get("id", "settlement"),
            name=data.get("name", "Settlement"),
            buildings=bldgs,
            metadata=data.get("metadata", {})
        )

class SpatialGraph:
    """Topological room adjacency graph and pathfinding."""

    def __init__(self):
        self.adj_list: Dict[str, Set[str]] = {}

    def build_graph(self, settlements: Dict[str, Settlement]) -> None:
        self.adj_list.clear()
        for sett in settlements.values():
            for bldg in sett.buildings.values():
                for room in bldg.rooms.values():
                    self.adj_list.setdefault(room.id, set())
                    for neighbor in room.connected_room_ids:
                        self.adj_list[room.id].add(neighbor)
                        self.adj_list.setdefault(neighbor, set()).add(room.id)

    def find_shortest_path(self, start_room: str, target_room: str) -> Optional[List[str]]:
        if start_room == target_room:
            return [start_room]
        if start_room not in self.adj_list or target_room not in self.adj_list:
            return None

        visited = {start_room}
        queue = [[start_room]]

        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == target_room:
                return path
            for neighbor in self.adj_list.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None
