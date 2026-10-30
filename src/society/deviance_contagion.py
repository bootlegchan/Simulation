from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

class NormFrictionTracker:
    """Tracks societal norm friction and individual moral resistance to breaking rules."""

    def __init__(self, npc_id: str):
        self.npc_id = npc_id
        # Baseline Norm Frictions (0.0 = no resistance, 100.0 = unshakeable moral compliance)
        self.norm_frictions: Dict[str, float] = {
            "honesty_in_trade": 75.0,
            "marital_fidelity": 80.0,
            "lawful_behavior": 70.0,
            "sobriety_and_order": 65.0,
        }
        self.corrupting_exposure_count = 0

    def evaluate_moral_resistance(self, npc: NPC) -> float:
        """Calculates moral resistance based on Big Five traits, social class, and stigma."""
        honor = npc.social_profile.get("moral_values", {}).get("honor", 0.5) * 40.0
        loyalty = npc.social_profile.get("moral_values", {}).get("loyalty", 0.5) * 30.0
        conscientiousness = npc.personality.get("conscientiousness", 0.5) * 30.0
        return round(honor + loyalty + conscientiousness, 2)

    def degrade_norm_friction(self, norm_type: str, corruption_index: float, npc: NPC) -> float:
        """Erodes norm friction if corrupting influence exceeds moral resistance."""
        resistance = self.evaluate_moral_resistance(npc)
        net_impact = max(0.0, corruption_index - (resistance * 0.3))
        
        current = self.norm_frictions.get(norm_type, 50.0)
        updated = max(0.0, current - net_impact)
        self.norm_frictions[norm_type] = round(updated, 2)
        self.corrupting_exposure_count += 1
        return updated

    def rehabilitate_norm_friction(self, norm_type: str, moral_authority_index: float) -> float:
        """Restores norm friction through pious or virtuous authority influence."""
        current = self.norm_frictions.get(norm_type, 50.0)
        updated = min(100.0, current + (moral_authority_index * 0.5))
        self.norm_frictions[norm_type] = round(updated, 2)
        return updated

class DevianceContagionEngine:
    """Engine for social contagion, moral degradation, and influence transmission."""

    @staticmethod
    def transmit_deviance(
        influencer: NPC,
        target: NPC,
        norm_type: str,
        target_friction_tracker: NormFrictionTracker
    ) -> Dict[str, Any]:
        """Calculates corrupting transmission from a deviant/corrupt character to a target."""
        influencer_ambition = influencer.social_profile.get("moral_values", {}).get("ambition", 0.5)
        influencer_discretion = influencer.social_profile.get("reputation_facets", {}).get("discretion", 50.0) / 100.0
        
        # Corrupting index driven by influencer charisma, ambition, and vice levels
        corrupting_index = (influencer_ambition * 40.0) + (influencer_discretion * 30.0) + 15.0
        
        new_friction = target_friction_tracker.degrade_norm_friction(norm_type, corrupting_index, target)
        is_corrupted = new_friction < 35.0

        return {
            "influencer_id": influencer.id,
            "target_id": target.id,
            "norm_type": norm_type,
            "corrupting_index": round(corrupting_index, 2),
            "new_norm_friction": new_friction,
            "is_corrupted": is_corrupted
        }

    @staticmethod
    def apply_moral_authority_rehabilitation(
        virtuous_npc: NPC,
        target: NPC,
        norm_type: str,
        target_friction_tracker: NormFrictionTracker
    ) -> Dict[str, Any]:
        """Noble/pious NPCs radiate moral authority to rehabilitate slipping citizens."""
        honor = virtuous_npc.social_profile.get("moral_values", {}).get("honor", 0.8)
        moral_authority = honor * 50.0
        new_friction = target_friction_tracker.rehabilitate_norm_friction(norm_type, moral_authority)

        return {
            "virtuous_npc_id": virtuous_npc.id,
            "target_id": target.id,
            "norm_type": norm_type,
            "moral_authority": round(moral_authority, 2),
            "rehabilitated_friction": new_friction
        }
