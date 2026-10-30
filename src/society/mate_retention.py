"""
Daly & Wilson's Mate Retention Strategies & Intra-Sexual Rivalry Engine.
Implements protective, vigilant, and rivalry behaviors (Mate Guarding, Surveillance, Gift Giving).
"""
from typing import Any, Dict, List
from src.entities.npc import NPC

class MateRetentionEngine:
    """Manages possessive, protective, and surveillance strategies to retain romantic partners."""

    @staticmethod
    def evaluate_mate_retention_urgency(
        npc: NPC,
        suspicion_score: float,
        presence_of_rivals: bool
    ) -> Dict[str, Any]:
        """Calculates urgency for mate retention actions (GIFT_GIVING, MATE_GUARDING, CONFRONT_RIVAL)."""
        neuroticism = npc.personality.get("neuroticism", 0.5)
        extraversion = npc.personality.get("extraversion", 0.5)

        base_urgency = (suspicion_score * 0.7) + (neuroticism * 30.0) + (25.0 if presence_of_rivals else 0.0)

        if base_urgency >= 60.0 and presence_of_rivals:
            if extraversion >= 0.5:
                recommended_strategy = "CONFRONT_RIVAL"
            else:
                recommended_strategy = "SURVEILLANCE_AND_GUARDING"
        elif base_urgency >= 35.0:
            recommended_strategy = "GIFT_GIVING_AND_ATTENTION"
        else:
            recommended_strategy = "STANDARD_AFFECTION"

        return {
            "retention_urgency": round(min(100.0, base_urgency), 2),
            "recommended_strategy": recommended_strategy
        }

    @staticmethod
    def execute_mate_guarding(
        actor: NPC,
        partner: NPC,
        rival_id: str,
        social_network: Any
    ) -> Dict[str, Any]:
        """Executes active mate guarding, asserting relationship bounds and warning rivals."""
        # Increase fear/intimidation toward rival
        social_network.get_bond(rival_id, actor.id).adjust_axis("fear_intimidation", 15.0)
        # Reduce partner's attraction to rival
        social_network.get_bond(partner.id, rival_id).adjust_axis("romantic_affection", -10.0)

        return {
            "actor_id": actor.id,
            "partner_id": partner.id,
            "rival_id": rival_id,
            "strategy": "MATE_GUARDING_EXECUTED",
            "rival_fear_increased": True
        }
