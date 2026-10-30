import time
import threading
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path
from src.simulation.engine import SimulationEngine
from src.api.dtos import (
    SimulationTickBatchDTO,
    WorldStateDTO,
    NPCVisualDTO,
    InteractiveObjectDTO,
    EventDTO,
    SpatialNodeDTO,
    SpatialGraphDTO,
)
from src.economy.macro import MacroEconomicTracker

class SimulationRunner:
    """
    Real-Time Simulation Runner and Threaded Execution Loop.
    Provides live tick-by-tick execution, target TPS rate limiting, thread safety,
    and real-time subscriber event broadcasting for 2D/3D visual frontends.
    """

    def __init__(self, engine: SimulationEngine, target_tps: float = 10.0):
        self.engine = engine
        self.target_tps = target_tps  # Ticks Per Second (0.0 = uncapped maximum)
        self.is_running = False
        self.is_paused = False

        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self.subscriber_callbacks: List[Callable[[SimulationTickBatchDTO], None]] = []

    def register_subscriber(self, callback: Callable[[SimulationTickBatchDTO], None]) -> None:
        """Register a subscriber callback invoked on every completed tick."""
        with self._lock:
            if callback not in self.subscriber_callbacks:
                self.subscriber_callbacks.append(callback)

    def unregister_subscriber(self, callback: Callable[[SimulationTickBatchDTO], None]) -> None:
        with self._lock:
            if callback in self.subscriber_callbacks:
                self.subscriber_callbacks.remove(callback)

    def set_target_tps(self, target_tps: float) -> None:
        with self._lock:
            self.target_tps = max(0.0, target_tps)

    def start_live_runner(self) -> None:
        """Starts the real-time background simulation thread."""
        with self._lock:
            if self.is_running:
                return
            if self.engine.lifecycle_state.value not in ("READY", "RUNNING", "PAUSED"):
                self.engine.initialize()

            self.engine.start()
            self.is_running = True
            self.is_paused = False
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._execution_loop, daemon=True)
            self._thread.start()

    def pause_live_runner(self) -> None:
        with self._lock:
            self.is_paused = True

    def resume_live_runner(self) -> None:
        with self._lock:
            self.is_paused = False

    def stop_live_runner(self) -> None:
        self._stop_event.set()
        with self._lock:
            self.is_running = False
            self.is_paused = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def step_ticks(self, count: int = 1) -> SimulationTickBatchDTO:
        """Executes count ticks synchronously and broadcasts the resulting state batch."""
        with self._lock:
            if self.engine.lifecycle_state.value in ("READY", "PAUSED"):
                self.engine.start()
            
            start_events_len = len(self.engine.event_bus.history)
            self.engine.tick(count)
            new_events = self.engine.event_bus.history[start_events_len:]
            batch = self._build_tick_batch(new_events)

        self._notify_subscribers(batch)
        return batch

    def _execution_loop(self) -> None:
        while not self._stop_event.is_set():
            if self.is_paused:
                time.sleep(0.05)
                continue

            start_time = time.time()
            start_events_len = len(self.engine.event_bus.history)

            with self._lock:
                self.engine.tick(1)
                new_events = self.engine.event_bus.history[start_events_len:]
                batch = self._build_tick_batch(new_events)

            self._notify_subscribers(batch)

            # Target TPS rate limiter
            if self.target_tps > 0.0:
                elapsed = time.time() - start_time
                desired_interval = 1.0 / self.target_tps
                sleep_time = desired_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def _notify_subscribers(self, batch: SimulationTickBatchDTO) -> None:
        with self._lock:
            callbacks = list(self.subscriber_callbacks)
        for cb in callbacks:
            try:
                cb(batch)
            except Exception as e:
                print(f"[SimulationRunner Subscriber Error]: {e}")

    def _build_tick_batch(self, new_events: List[Any]) -> SimulationTickBatchDTO:
        gini = MacroEconomicTracker.calculate_gini_coefficient(self.engine.npcs)
        total_wealth = MacroEconomicTracker.calculate_total_currency(self.engine.npcs)

        tod = "DAY"
        clock_iso = self.engine.clock.current_virtual_time_iso if self.engine.clock else "2026-01-01T06:00:00Z"

        world_dto = WorldStateDTO(
            virtual_time_iso=clock_iso,
            current_tick=self.engine.clock.current_tick if self.engine.clock else 0,
            weather="CLEAR",
            season="SUMMER",
            time_of_day=tod,
            world_tension=10.0,
            gini_coefficient=round(gini, 3),
            total_wealth_gold=round(total_wealth, 2),
            active_npc_count=len(self.engine.npcs),
            active_object_count=len(self.engine.objects),
            is_running=self.is_running and not self.is_paused,
        )

        npc_dtos = {}
        for nid, npc in self.engine.npcs.items():
            loc = npc.location_id or "room_village_square"
            x3d, y3d, z3d = self._project_3d_coordinates(loc)
            npc_dtos[nid] = NPCVisualDTO(
                id=npc.id,
                name=npc.name,
                location_id=loc,
                current_action=getattr(npc, "current_action", "IDLE"),
                fsm_state="RUNNING",
                x_3d=x3d,
                y_3d=y3d,
                z_3d=z3d,
                needs_hunger=round(npc.needs.get("hunger", 0.0), 1),
                needs_energy=round(npc.needs.get("energy", 100.0), 1),
                needs_social=round(npc.needs.get("social", 50.0), 1),
                wealth=round(npc.wealth, 2),
                social_class=npc.social_profile.get("social_class", "COMMONER"),
                mood_icon="HAPPY" if npc.needs.get("energy", 100.0) > 50 else "TIRED",
                speech_bubble=getattr(npc, "last_spoken_dialogue", None),
                is_arrested=npc.social_profile.get("is_arrested", False),
            )

        obj_dtos = {}
        for oid, obj in self.engine.objects.items():
            loc = obj.location_id or "room_village_square"
            x3d, y3d, z3d = self._project_3d_coordinates(loc)
            obj_dtos[oid] = InteractiveObjectDTO(
                id=obj.id,
                name=obj.name,
                location_id=loc,
                x_3d=x3d,
                y_3d=y3d,
                z_3d=z3d,
                is_locked=getattr(obj, "is_locked", False),
                capabilities=obj.capabilities,
                contained_item_ids=getattr(obj, "contained_item_ids", []),
            )

        event_dtos = [
            EventDTO(
                event_id=getattr(e, "event_id", "evt"),
                event_type=getattr(e, "event_type", "tick"),
                tick=getattr(e, "tick", 0),
                source_id=getattr(e, "source_id", "engine"),
                payload=getattr(e, "payload", {}),
                timestamp_iso=getattr(e, "timestamp_iso", clock_iso),
            )
            for e in new_events
        ]

        return SimulationTickBatchDTO(
            tick=self.engine.clock.current_tick if self.engine.clock else 0,
            virtual_time_iso=clock_iso,
            world_state=world_dto,
            npcs=npc_dtos,
            objects=obj_dtos,
            events=event_dtos,
        )

    def _project_3d_coordinates(self, location_id: str) -> tuple[float, float, float]:
        """Maps abstract spatial node location to deterministic 3D coordinate vectors for visual engines."""
        hash_val = sum(ord(c) for c in location_id)
        x = (hash_val % 100) * 2.0
        y = ((hash_val // 100) % 100) * 2.0
        z = 0.0
        return (round(x, 2), round(y, 2), round(z, 2))
