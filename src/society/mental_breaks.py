"""
Mental Break Engine: RimWorld & Dwarf Fortress inspired psychological breakdowns.
Triggers emotional break states when psychological stress or grief crosses critical thresholds.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

class MentalBreakType(Enum):
    CATATONIC_RETREAT = "CATATONIC_RETREAT"    # Refuses to work, hides in room
    TAVERN_RAMPAGE = "TAVERN_RAMPAGE"          # Brawls and hurls insults at co-located NPCs
    SADISTIC_VANDALISM = "SADISTIC_VANDALISM"  # Destroys room items/objects
    DESPERATE_FLIGHT = "DESPERATE_FLIGHT"      # Flees town to wilderness

class MentalBreakEngine:
    """Evaluates psychological stress thresholds and triggers break behaviors."""

    @staticmethod
    def evaluate_break_risk(
        npc: NPC,
        stress_level: float,
        grief_level: float = 0.0,
        trauma_level: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        """Evaluates whether psychological stress triggers a mental break state."""
        total_strain = stress_level + (grief_level * 0.5) + (trauma_level * 0.5)
        
        # Threshold: Extreme strain > 80.0
        if total_strain >= 80.0:
            neuroticism = npc.personality.get("neuroticism", 0.5)
            impulsivity = 1.0 - npc.personality.get("conscientiousness", 0.5)

            # Determine break type based on personality and vices
            if neuroticism > 0.7:
                break_type = MentalBreakType.CATATONIC_RETREAT
                description = f"{npc.name} succumbed to despair and retreated into catatonic isolation."
            elif impulsivity > 0.6:
                break_type = MentalBreakType.TAVERN_RAMPAGE
                description = f"{npc.name} entered a violent rampage, attacking and insulting anyone nearby."
            else:
                break_type = MentalBreakType.SADISTIC_VANDALISM
                description = f"{npc.name} snapped, vandalizing nearby property and breaking stored supplies."

            npc.current_state = f"MENTAL_BREAK_{break_type.value}"

            return {
                "triggered": True,
                "break_type": break_type.value,
                "total_strain": round(total_strain, 2),
                "description": description,
                "npc_id": npc.id
            }

        return {"triggered": False, "break_type": None, "total_strain": round(total_strain, 2)}
