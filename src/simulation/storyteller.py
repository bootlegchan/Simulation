"""
Storyteller & Game Master Engine: RimWorld Storytellers & DeepMind Concordia GM inspired event director.
Evaluates macro societal tension, wealth inequality, and stress, dynamically spawning targeted events.
"""
from typing import Any, Dict, List, Optional
from src.core.events import EventBus, DomainEvent
from src.core.randomness import SeededRandom
from src.economy.macro import MacroEconomicTracker
from src.entities.npc import NPC

class StorytellerEngine:
    """Dynamic event director injecting world narrative challenges to maintain simulation tension."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.tension_level = 0.0  # 0.0 to 100.0

    def evaluate_world_tension(
        self,
        npcs: Dict[str, NPC],
        municipal_vault: float = 0.0
    ) -> float:
        """Calculates global world tension based on Gini inequality, average stress, and poverty."""
        gini = MacroEconomicTracker.calculate_gini_coefficient(npcs)
        avg_stress = sum(npc.needs.get("stress", 0.0) for npc in npcs.values()) / max(1, len(npcs))
        poor_npcs = sum(1 for npc in npcs.values() if npc.wealth < 20.0)
        
        self.tension_level = (gini * 40.0) + (avg_stress * 0.4) + (poor_npcs * 5.0)
        return round(min(100.0, self.tension_level), 2)

    def orchestrate_narrative_event(
        self,
        npcs: Dict[str, NPC],
        random_gen: SeededRandom,
        current_tick: int,
        force_trigger: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Spawns targeted world narrative event if tension calls for intervention."""
        tension = self.evaluate_world_tension(npcs)

        # Trigger event if forced or random roll <= tension probability
        if force_trigger or (random_gen.random() * 100.0 <= min(75.0, tension)):
            roll = random_gen.random()
            if roll < 0.35:
                event_name = "MYSTERIOUS_FEVER_OUTBREAK"
                desc = "A sudden mysterious fever spreads through Oakwood's residential quarters."
                for npc in npcs.values():
                    npc.needs["stress"] = min(100.0, npc.needs.get("stress", 0.0) + 20.0)
            elif roll < 0.70:
                event_name = "TRADE_CARAVAN_EMBARGO"
                desc = "Neighboring settlements impose a trade embargo, driving up merchant prices."
            else:
                event_name = "REFUGEE_INFLUX"
                desc = "Displaced refugees arrive seeking food and sanctuary at St. Jude's Chapel."

            event_payload = {
                "event_type": "storyteller_narrative_event",
                "event_name": event_name,
                "description": desc,
                "world_tension": tension,
                "tick": current_tick
            }

            self.event_bus.publish(
                DomainEvent(
                    event_type="storyteller_event",
                    tick=current_tick,
                    source_id="storyteller_engine",
                    payload=event_payload
                )
            )

            return event_payload

        return None
