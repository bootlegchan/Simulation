"""Simulation World Context and Dynamic Service Locator."""
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.clock import SimulationClock
from src.core.randomness import SeededRandom
from src.core.events import EventBus, DomainEvent
from src.core.logging_config import SimulationLogManager

class WorldContext:
    """Central state and dynamic spatial/service query container."""

    def __init__(
        self,
        data_dir: Path,
        clock: Optional[SimulationClock] = None,
        random: Optional[SeededRandom] = None,
        event_bus: Optional[EventBus] = None,
        log_manager: Optional[SimulationLogManager] = None,
    ):
        self.data_dir = Path(data_dir)
        self.clock = clock or SimulationClock()
        self.random = random or SeededRandom(seed=42)
        self.log_manager = log_manager or SimulationLogManager.get_global_instance()
        SimulationLogManager.set_global_instance(self.log_manager)
        self.event_bus = event_bus or EventBus(log_manager=self.log_manager)

        # Entity, Spatial, and Socio-Economic Maps
        self.settlements: Dict[str, Any] = {}
        self.npcs: Dict[str, Any] = {}
        self.objects: Dict[str, Any] = {}
        self.item_definitions: Dict[str, Any] = {}
        self.recipes: Dict[str, Any] = {}
        self.factions: Dict[str, Any] = {}
        self.offices: Dict[str, Any] = {}
        self.settings: Dict[str, Any] = {}

        # Spatial topology
        from src.world.model import SpatialGraph
        self.spatial_graph = SpatialGraph()
        self.spatial_grid = None

        # Registry / Service locator map
        self._services: Dict[str, Any] = {}

    def register_service(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get_service(self, name: str) -> Optional[Any]:
        return self._services.get(name)

    def publish_event(self, event_type: str, source_id: str, payload: Optional[Dict[str, Any]] = None) -> None:
        tick = self.clock.current_tick if self.clock else 0
        evt = DomainEvent(event_type=event_type, tick=tick, source_id=source_id, payload=payload or {})
        self.event_bus.publish(evt)

    def find_npc_by_role(self, role_keywords: List[str]) -> Optional[Any]:
        for npc in self.npcs.values():
            if not getattr(npc, "is_alive", True):
                continue
            occ = (getattr(npc, "occupation", "") or "").lower()
            civic = (getattr(npc, "civic_role", "") or "").lower()
            name = (getattr(npc, "name", "") or "").lower()
            for kw in role_keywords:
                kw_l = kw.lower()
                if kw_l in occ or kw_l in civic or kw_l in name:
                    return npc
        return None

    def find_room_by_id(self, room_id: str) -> Optional[Any]:
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                if room_id in bldg.rooms:
                    return bldg.rooms[room_id]
        return None

    def find_building_by_id(self, building_id: str) -> Optional[Any]:
        for sett in self.settlements.values():
            if building_id in sett.buildings:
                return sett.buildings[building_id]
        return None

    def find_building_by_room_id(self, room_id: str) -> Optional[Any]:
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                if room_id in bldg.rooms:
                    return bldg
        return None

    def find_object_by_capability(self, capability: str) -> Optional[Any]:
        for obj in self.objects.values():
            if hasattr(obj, "has_capability") and obj.has_capability(capability):
                return obj
        return None

    def get_central_public_room(self) -> str:
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                for r in bldg.rooms.values():
                    arch = getattr(r, "archetype", "").upper()
                    if arch in ("MARKET_PLAZA", "TOWN_SQUARE", "CIRCULATION"):
                        return r.id
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                if getattr(bldg, "category", "").upper() in ("CIVIC", "CIRCULATION") and bldg.rooms:
                    return list(bldg.rooms.keys())[0]
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                if bldg.rooms:
                    return list(bldg.rooms.keys())[0]
        if hasattr(self, "spatial_graph") and getattr(self.spatial_graph, "adj_list", None):
            return list(self.spatial_graph.adj_list.keys())[0]
        return "room_village_square"

    def find_rooms_by_archetype(self, archetype: str) -> List[str]:
        res: List[str] = []
        arch_u = archetype.upper()
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                for r in bldg.rooms.values():
                    if getattr(r, "archetype", "").upper() == arch_u:
                        res.append(r.id)
        return res

    def find_rooms_by_building_category(self, category: str) -> List[str]:
        res: List[str] = []
        cat_u = category.upper()
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                if getattr(bldg, "category", "").upper() == cat_u:
                    res.extend(list(bldg.rooms.keys()))
        return res

    def find_rooms_by_keyword(self, keyword: str) -> List[str]:
        res: List[str] = []
        kw_l = keyword.lower()
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                b_name_l = bldg.name.lower()
                b_id_l = bldg.id.lower()
                match_bldg = kw_l in b_name_l or kw_l in b_id_l
                for r in bldg.rooms.values():
                    r_name_l = r.name.lower()
                    r_id_l = r.id.lower()
                    r_arch_l = getattr(r, "archetype", "").lower()
                    if match_bldg or kw_l in r_name_l or kw_l in r_id_l or kw_l in r_arch_l:
                        if r.id not in res:
                            res.append(r.id)
        return res

    def find_social_hub_room(self) -> str:
        hub_rooms = self.find_rooms_by_keyword("tavern") or self.find_rooms_by_keyword("inn") or self.find_rooms_by_keyword("common")
        if hub_rooms:
            return hub_rooms[0]
        return self.get_central_public_room()

    def find_sacred_sanctuary_room(self) -> str:
        sanctuary_rooms = self.find_rooms_by_keyword("chapel") or self.find_rooms_by_keyword("church") or self.find_rooms_by_keyword("sanctuary")
        if sanctuary_rooms:
            return sanctuary_rooms[0]
        return self.get_central_public_room()

    def find_underworld_room(self) -> str:
        shadow_rooms = self.find_rooms_by_keyword("underworld") or self.find_rooms_by_keyword("vice") or self.find_rooms_by_keyword("den") or self.find_rooms_by_keyword("cellar")
        if shadow_rooms:
            return shadow_rooms[0]
        return self.get_central_public_room()
