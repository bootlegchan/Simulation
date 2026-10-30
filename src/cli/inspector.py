from typing import Any, Dict
from src.simulation.engine import SimulationEngine

class SimulationInspector:
    """Headless query inspector interface."""

    def __init__(self, engine: SimulationEngine):
        self.engine = engine

    def get_status_report(self) -> Dict[str, Any]:
        return {
            "lifecycle_state": self.engine.lifecycle_state.value,
            "current_tick": self.engine.clock.current_tick if self.engine.clock else 0,
            "virtual_time_iso": self.engine.clock.current_virtual_time_iso if self.engine.clock else None,
            "is_paused": self.engine.clock.is_paused if self.engine.clock else True,
            "settlement_count": len(self.engine.settlements),
            "npc_count": len(self.engine.npcs),
            "object_count": len(self.engine.objects),
            "item_definitions_count": len(self.engine.item_definitions),
            "recipes_count": len(self.engine.recipes),
            "factions_count": len(self.engine.factions),
            "total_events_logged": len(self.engine.event_bus.history),
        }
