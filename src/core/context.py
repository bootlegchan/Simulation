"""
WorldContext Facade & Service Container.
Provides standardized, decoupled access to simulation state, entities,
registries, and services without tight bidirectional engine dependencies.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.core.clock import SimulationClock
from src.core.events import EventBus, DomainEvent
from src.core.randomness import SeededRandom
from src.world.model import Settlement, SpatialGraph, Building, Room
from src.world.spatial_index import SpatialGridIndex
from src.entities.npc import NPC
from src.entities.object import InteractiveObject
from src.entities.item import ItemDefinition
from src.economy.production import Recipe
from src.society.factions import Faction
from src.society.civic import CivicOffice, MunicipalTreasury
from src.economy.finance import DebtManager


class WorldContext:
    """
    Unified context container provided to all simulation subsystems.
    Wraps all entity stores, topological graphs, services, and core utilities.
    """

    def __init__(
        self,
        clock: Optional[SimulationClock] = None,
        random: Optional[SeededRandom] = None,
        event_bus: Optional[EventBus] = None,
        data_dir: Optional[Union[str, Path]] = None,
        settlements: Optional[Dict[str, Settlement]] = None,
        npcs: Optional[Dict[str, NPC]] = None,
        objects: Optional[Dict[str, InteractiveObject]] = None,
        item_definitions: Optional[Dict[str, ItemDefinition]] = None,
        recipes: Optional[Dict[str, Recipe]] = None,
        factions: Optional[Dict[str, Faction]] = None,
        offices: Optional[Dict[str, CivicOffice]] = None,
        spatial_graph: Optional[SpatialGraph] = None,
        spatial_grid: Optional[SpatialGridIndex] = None,
        municipal_treasury: Optional[MunicipalTreasury] = None,
        debt_manager: Optional[DebtManager] = None,
        settings: Optional[Dict[str, Any]] = None,
    ):
        self.clock = clock or SimulationClock()
        self.random = random or SeededRandom(seed=42)
        self.event_bus = event_bus or EventBus()
        self.data_dir = Path(data_dir) if data_dir else Path(".")

        self.settlements: Dict[str, Settlement] = settlements if settlements is not None else {}
        self.npcs: Dict[str, NPC] = npcs if npcs is not None else {}
        self.objects: Dict[str, InteractiveObject] = objects if objects is not None else {}
        self.item_definitions: Dict[str, ItemDefinition] = item_definitions if item_definitions is not None else {}
        self.recipes: Dict[str, Recipe] = recipes if recipes is not None else {}
        self.factions: Dict[str, Faction] = factions if factions is not None else {}
        self.offices: Dict[str, CivicOffice] = offices if offices is not None else {}

        self.spatial_graph = spatial_graph or SpatialGraph()
        self.spatial_grid = spatial_grid or SpatialGridIndex(cell_size=10.0)
        self.municipal_treasury = municipal_treasury or MunicipalTreasury()
        self.debt_manager = debt_manager or DebtManager()
        self.settings: Dict[str, Any] = settings if settings is not None else {}

        # Service Locator Registry for domain managers & engines
        self._services: Dict[str, Any] = {}

    def register_service(self, service_name: str, service_instance: Any) -> None:
        """Registers a domain service or manager instance by name."""
        self._services[service_name] = service_instance

    def get_service(self, service_name: str, default: Any = None) -> Any:
        """Retrieves a registered domain service or manager."""
        return self._services.get(service_name, default)

    def has_service(self, service_name: str) -> bool:
        """Checks if a domain service is currently registered."""
        return service_name in self._services

    def publish_event(self, event_type: str, source_id: str, payload: Dict[str, Any]) -> DomainEvent:
        """Convenience method to construct and publish a DomainEvent to the EventBus."""
        tick = self.clock.current_tick if self.clock else 0
        evt = DomainEvent(
            event_type=event_type,
            tick=tick,
            source_id=source_id,
            payload=payload,
            timestamp_iso=self.clock.current_virtual_time_iso if self.clock else "2026-01-01T06:00:00Z"
        )
        self.event_bus.publish(evt)
        return evt

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        return self.npcs.get(npc_id)

    def get_object(self, object_id: str) -> Optional[InteractiveObject]:
        return self.objects.get(object_id)

    def get_settlement(self, settlement_id: str) -> Optional[Settlement]:
        return self.settlements.get(settlement_id)

    def find_room_by_id(self, room_id: str) -> Optional[Room]:
        """Locates a Room across all settlement buildings."""
        for s in self.settlements.values():
            for b in s.buildings.values():
                if room_id in b.rooms:
                    return b.rooms[room_id]
        return None

    def find_building_by_id(self, building_id: str) -> Optional[Building]:
        """Locates a Building across all settlements."""
        for s in self.settlements.values():
            if building_id in s.buildings:
                return s.buildings[building_id]
        return None
