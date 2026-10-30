from typing import Dict, Any, Tuple
from src.entities.npc import NPC

class FirstImpressionEngine:
    """Calculates dynamic first impressions when two NPCs meet for the first time."""

    @staticmethod
    def evaluate_first_impression(npc_a: NPC, npc_b: NPC, tick: int) -> Tuple[float, str]:
        # 1. Personality compatibility
        openness_diff = abs(npc_a.personality.get("openness", 0.5) - npc_b.personality.get("openness", 0.5))
        agreeableness_b = npc_b.personality.get("agreeableness", 0.5)
        compat_score = (1.0 - openness_diff) * 30.0 + (agreeableness_b * 30.0)

        # 2. Appearance & Outfit perception
        outfit_b = npc_b.appearance.get("outfit", "Plain Tunic")
        appearance_bonus = 15.0 if "Fine" in outfit_b or "Silk" in outfit_b or "Gown" in outfit_b else 0.0
        if "Ragged" in outfit_b or "Soiled" in outfit_b:
            appearance_bonus -= 15.0

        # 3. Stress / Mood penalty
        stress_a = npc_a.needs.get("hunger", 0.0) * 0.2
        stress_b = npc_b.needs.get("hunger", 0.0) * 0.2

        first_impression = compat_score + appearance_bonus - (stress_a + stress_b)
        first_impression = max(-100.0, min(100.0, first_impression))

        if first_impression >= 40.0:
            notes = f"Very Favorable ({outfit_b}; good rapport)"
        elif first_impression >= 10.0:
            notes = f"Neutral/Polite meeting"
        elif first_impression >= -20.0:
            notes = f"Slightly Distrustful ({outfit_b})"
        else:
            notes = f"Hostile First Impression"

        # Record in mental acquaintances
        npc_a.record_acquaintance(npc_b.id, npc_b.name, first_impression, notes, tick)
        npc_b.record_acquaintance(npc_a.id, npc_a.name, first_impression, f"Met {npc_a.name}", tick)

        return (first_impression, notes)
