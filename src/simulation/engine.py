"""
Master Simulation Controller (Microkernel Architecture).
Coordinates simulation lifecycle and dispatches execution across
modular, data-driven subsystems managed by SubsystemPipelineManager.
"""
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.core.clock import SimulationClock
from src.core.errors import LifecycleError, SimulationError
from src.core.events import DomainEvent, EventBus
from src.core.randomness import SeededRandom
from src.core.context import WorldContext
from src.core.subsystem import ISimulationSubsystem, SubsystemPipelineManager, TickStage
from src.configuration.loader import ContentLoader
from src.world.model import Settlement, SpatialGraph
from src.world.spatial_index import SpatialGridIndex
from src.entities.npc import NPC
from src.entities.object import InteractiveObject
from src.entities.item import ItemDefinition
from src.economy.production import Recipe
from src.economy.finance import DebtManager
from src.society.factions import Faction
from src.society.civic import CivicOffice, MunicipalTreasury


class LifecycleState(Enum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class SimulationEngine:
    """
    Decoupled Simulation Engine Microkernel.
    Coordinates the WorldContext, EventBus, and SubsystemPipelineManager.
    All gameplay, economic, societal, and urban dynamics are modular subsystems.
    """

    def __init__(self, data_dir: Union[str, Path]):
        self.data_dir = Path(data_dir)
        self._state: LifecycleState = LifecycleState.UNINITIALIZED

        # Core context container
        self.context: WorldContext = WorldContext(data_dir=self.data_dir)
        self.pipeline_manager: SubsystemPipelineManager = SubsystemPipelineManager()
        self.loader: ContentLoader = ContentLoader(self.data_dir)

    # -------------------------------------------------------------------------
    # Backward-compatible property facades referencing WorldContext
    # -------------------------------------------------------------------------

    @property
    def clock(self) -> SimulationClock:
        return self.context.clock

    @clock.setter
    def clock(self, val: SimulationClock) -> None:
        self.context.clock = val

    @property
    def random(self) -> SeededRandom:
        return self.context.random

    @random.setter
    def random(self, val: SeededRandom) -> None:
        self.context.random = val

    @property
    def event_bus(self) -> EventBus:
        return self.context.event_bus

    @event_bus.setter
    def event_bus(self, val: EventBus) -> None:
        self.context.event_bus = val

    @property
    def spatial_graph(self) -> SpatialGraph:
        return self.context.spatial_graph

    @spatial_graph.setter
    def spatial_graph(self, val: SpatialGraph) -> None:
        self.context.spatial_graph = val

    @property
    def spatial_grid(self) -> SpatialGridIndex:
        return self.context.spatial_grid

    @spatial_grid.setter
    def spatial_grid(self, val: SpatialGridIndex) -> None:
        self.context.spatial_grid = val

    @property
    def settlements(self) -> Dict[str, Settlement]:
        return self.context.settlements

    @settlements.setter
    def settlements(self, val: Dict[str, Settlement]) -> None:
        self.context.settlements = val

    @property
    def npcs(self) -> Dict[str, NPC]:
        return self.context.npcs

    @npcs.setter
    def npcs(self, val: Dict[str, NPC]) -> None:
        self.context.npcs = val

    @property
    def objects(self) -> Dict[str, InteractiveObject]:
        return self.context.objects

    @objects.setter
    def objects(self, val: Dict[str, InteractiveObject]) -> None:
        self.context.objects = val

    @property
    def item_definitions(self) -> Dict[str, ItemDefinition]:
        return self.context.item_definitions

    @item_definitions.setter
    def item_definitions(self, val: Dict[str, ItemDefinition]) -> None:
        self.context.item_definitions = val

    @property
    def recipes(self) -> Dict[str, Recipe]:
        return self.context.recipes

    @recipes.setter
    def recipes(self, val: Dict[str, Recipe]) -> None:
        self.context.recipes = val

    @property
    def factions(self) -> Dict[str, Faction]:
        return self.context.factions

    @factions.setter
    def factions(self, val: Dict[str, Faction]) -> None:
        self.context.factions = val

    @property
    def offices(self) -> Dict[str, CivicOffice]:
        return self.context.offices

    @offices.setter
    def offices(self, val: Dict[str, CivicOffice]) -> None:
        self.context.offices = val

    @property
    def debt_manager(self) -> DebtManager:
        return self.context.debt_manager

    @debt_manager.setter
    def debt_manager(self, val: DebtManager) -> None:
        self.context.debt_manager = val

    @property
    def municipal_treasury(self) -> MunicipalTreasury:
        return self.context.municipal_treasury

    @municipal_treasury.setter
    def municipal_treasury(self, val: MunicipalTreasury) -> None:
        self.context.municipal_treasury = val

    @property
    def settings(self) -> Dict[str, Any]:
        return self.context.settings

    @settings.setter
    def settings(self, val: Dict[str, Any]) -> None:
        self.context.settings = val

    @property
    def lifecycle_state(self) -> LifecycleState:
        return self._state

    # Subsystem service facades for backwards compatibility with tests
    @property
    def urban_growth_engine(self) -> Any:
        return self.context.get_service("urban_growth_engine")

    @property
    def building_repurposing_engine(self) -> Any:
        return self.context.get_service("building_repurposing_engine")

    @property
    def civic_planning_engine(self) -> Any:
        return self.context.get_service("civic_planning_engine")

    @property
    def micro_climate_engine(self) -> Any:
        return self.context.get_service("micro_climate_engine")

    @property
    def sanitation_engine(self) -> Any:
        return self.context.get_service("sanitation_engine")

    @property
    def subjective_cognition_engine(self) -> Any:
        return self.context.get_service("subjective_cognition_engine")

    @property
    def habituation_engine(self) -> Any:
        return self.context.get_service("habituation_engine")

    @property
    def credit_manager(self) -> Any:
        return self.context.get_service("credit_instrument_manager")

    @property
    def guild_cartel_manager(self) -> Any:
        return self.context.get_service("guild_cartel_manager")

    @property
    def lineage_alliance_engine(self) -> Any:
        return self.context.get_service("lineage_alliance_engine")

    @property
    def superstition_omens_engine(self) -> Any:
        return self.context.get_service("superstition_omens_engine")

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        return self.context.get_npc(npc_id)

    def get_object(self, object_id: str) -> Optional[InteractiveObject]:
        return self.context.get_object(object_id)

    # -------------------------------------------------------------------------
    # Lifecycle & Initialization
    # -------------------------------------------------------------------------

    def initialize(self, seed: Optional[int] = None) -> None:
        self._state = LifecycleState.INITIALIZING
        try:
            content = self.loader.load_content()
            self.context.settings = content.get("settings", {})

            # Merge all loaded settings into context settings dictionary
            for key, val in content.items():
                if key not in ("settlements", "npcs", "objects", "items", "recipes", "factions", "offices"):
                    self.context.settings[key] = val

            sim_settings = self.context.settings.get("simulation", {})
            start_time = sim_settings.get("start_time_iso", "2026-01-01T06:00:00Z")
            ticks_per_min = sim_settings.get("ticks_per_minute", 1)
            self.context.clock = SimulationClock(start_time_iso=start_time, ticks_per_minute=ticks_per_min)

            selected_seed = seed if seed is not None else sim_settings.get("seed", 42)
            self.context.random = SeededRandom(seed=selected_seed)

            # Build Settlements
            self.context.settlements.clear()
            for s_id, s_data in content.get("settlements", {}).items():
                self.context.settlements[s_id] = Settlement.from_dict(s_data)
            self.context.spatial_graph.build_graph(self.context.settlements)

            # Build Items
            self.context.item_definitions.clear()
            for i_id, i_data in content.get("items", {}).items():
                self.context.item_definitions[i_id] = ItemDefinition.from_dict(i_data)

            # Build Recipes
            self.context.recipes.clear()
            for r_id, r_data in content.get("recipes", {}).items():
                self.context.recipes[r_id] = Recipe.from_dict(r_data)

            # Build Objects
            self.context.objects.clear()
            for o_id, o_data in content.get("objects", {}).items():
                obj = InteractiveObject.from_dict(o_data)
                self.context.objects[o_id] = obj
                if obj.location_id:
                    self._place_object_in_room(obj.id, obj.location_id)

            # Build NPCs
            self.context.npcs.clear()
            for n_id, n_data in content.get("npcs", {}).items():
                npc = NPC.from_dict(n_data)
                self.context.npcs[n_id] = npc
                if npc.location_id:
                    self._place_npc_in_room(npc.id, npc.location_id)

            # Build Factions
            self.context.factions.clear()
            for f_id, f_data in content.get("factions", {}).items():
                self.context.factions[f_id] = Faction(
                    faction_id=f_data["id"],
                    name=f_data["name"],
                    member_ids=f_data.get("member_ids", []),
                    leader_id=f_data.get("leader_id"),
                )

            # Dynamically instantiate and register Subsystems from JSON manifest
            subsystems_manifest = content.get("subsystems_manifest", {})
            if not subsystems_manifest or "subsystems" not in subsystems_manifest:
                # Fallback to direct file load if needed
                manifest_file = self.data_dir / "settings" / "subsystems_manifest.json"
                if manifest_file.exists():
                    import json
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        subsystems_manifest = json.load(f)

            self.pipeline_manager.load_from_manifest(subsystems_manifest, self.context)

            self.event_bus.publish(
                DomainEvent(
                    event_type="simulation_initialized",
                    tick=self.clock.current_tick,
                    source_id="engine",
                    payload={
                        "settlements_count": len(self.settlements),
                        "npcs_count": len(self.npcs),
                        "objects_count": len(self.objects),
                        "items_count": len(self.item_definitions),
                        "subsystems_count": len(self.pipeline_manager.subsystems),
                        "seed": selected_seed,
                    },
                )
            )

            self._state = LifecycleState.READY

        except Exception as e:
            self._state = LifecycleState.ERROR
            raise SimulationError(f"Initialization failed: {e}")

    def register_subsystem(self, subsystem: ISimulationSubsystem) -> None:
        """Dynamically registers an additional custom subsystem into the pipeline."""
        subsystem.initialize(self.context)
        self.pipeline_manager.register_subsystem(subsystem)

    def _place_npc_in_room(self, npc_id: str, location_id: str) -> None:
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                if location_id in bldg.rooms:
                    room = bldg.rooms[location_id]
                    if npc_id not in room.occupant_ids:
                        room.occupant_ids.append(npc_id)
                    return

    def _place_object_in_room(self, object_id: str, location_id: str) -> None:
        for sett in self.settlements.values():
            for bldg in sett.buildings.values():
                if location_id in bldg.rooms:
                    room = bldg.rooms[location_id]
                    if object_id not in room.contained_object_ids:
                        room.contained_object_ids.append(object_id)
                    return

    def start(self) -> None:
        if self._state not in (LifecycleState.READY, LifecycleState.PAUSED):
            raise LifecycleError(f"Cannot start simulation from state '{self._state.value}'")
        self.clock.resume()
        self._state = LifecycleState.RUNNING

    def pause(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise LifecycleError(f"Cannot pause simulation from state '{self._state.value}'")
        self.clock.pause()
        self._state = LifecycleState.PAUSED

    def tick(self, count: int = 1) -> int:
        if self._state not in (LifecycleState.RUNNING, LifecycleState.READY):
            raise LifecycleError(f"Cannot execute tick in state '{self._state.value}'")

        if self._state == LifecycleState.READY:
            self.start()

        for _ in range(count):
            current_tick = self.clock.advance_tick(1)
            self._update_tick(current_tick)

        return self.clock.current_tick

    def _update_tick(self, tick: int) -> None:
        """
        Dispatches tick execution through the Stage-Pipelined Subsystem Manager.
        Executes stages in topological order: PRE_TICK -> COGNITIVE -> EXECUTION -> POST_TICK.
        """
        # 1. Pipeline dispatch across all configured subsystems
        self.pipeline_manager.dispatch_tick(tick, self.context)

        # 2. Emit tick completed domain event
        self.event_bus.publish(
            DomainEvent(
                event_type="tick_completed",
                tick=tick,
                source_id="engine",
                payload={"virtual_time": self.clock.current_virtual_time_iso},
            )
        )

    def save_snapshot(self) -> Dict[str, Any]:
        if self._state == LifecycleState.UNINITIALIZED or not self.clock or not self.random:
            raise LifecycleError("Cannot save snapshot of uninitialized simulation.")

        return {
            "version": "2.0",
            "lifecycle_state": self._state.value,
            "clock": self.clock.to_dict(),
            "random": self.random.to_dict(),
            "settlements": {sid: s.to_dict() for sid, s in self.settlements.items()},
            "npcs": {nid: n.to_dict() for nid, n in self.npcs.items()},
            "objects": {oid: o.to_dict() for oid, o in self.objects.items()},
            "item_definitions": {iid: i.to_dict() for iid, i in self.item_definitions.items()},
            "subsystem_states": self.pipeline_manager.save_all_states(),
            "event_history": self.event_bus.to_dict(),
        }

    def load_snapshot(self, snapshot: Dict[str, Any]) -> None:
        if snapshot.get("version") != "2.0":
            raise SimulationError(f"Unsupported snapshot version: {snapshot.get('version')}")

        self.clock = SimulationClock.from_dict(snapshot["clock"])
        self.random = SeededRandom.from_dict(snapshot["random"])

        self.settlements = {sid: Settlement.from_dict(sdata) for sid, sdata in snapshot.get("settlements", {}).items()}
        self.npcs = {nid: NPC.from_dict(ndata) for nid, ndata in snapshot.get("npcs", {}).items()}
        self.objects = {oid: InteractiveObject.from_dict(odata) for oid, odata in snapshot.get("objects", {}).items()}
        self.item_definitions = {iid: ItemDefinition.from_dict(idata) for iid, idata in snapshot.get("item_definitions", {}).items()}

        if "subsystem_states" in snapshot:
            self.pipeline_manager.load_all_states(snapshot["subsystem_states"])

        self.event_bus.clear()
        self.event_bus.load_history(snapshot.get("event_history", []))
        self._state = LifecycleState(snapshot.get("lifecycle_state", LifecycleState.READY.value))
