from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

class PersonalityEvolution:
    """Manages dynamic personality trait drift and character arc transformations over time."""

    @staticmethod
    def process_betrayal_trauma(npc: NPC, betrayal_severity: float = 50.0) -> Dict[str, float]:
        """Surviving betrayal increases paranoia/neuroticism and reduces trust/altruism."""
        old_openness = npc.personality.get("openness", 0.5)
        old_conscience = npc.personality.get("conscientiousness", 0.5)

        # Shift traits
        npc.personality["openness"] = max(0.05, round(old_openness - (betrayal_severity / 200.0), 2))
        npc.personality["conscientiousness"] = min(0.95, round(old_conscience + (betrayal_severity / 250.0), 2))

        return dict(npc.personality)

    @staticmethod
    def process_happy_marriage_or_friendship(npc: NPC, bond_duration_days: int) -> Dict[str, float]:
        """Sustained happy relationships increase openness, altruism, and emotional resilience."""
        old_openness = npc.personality.get("openness", 0.5)
        npc.personality["openness"] = min(0.95, round(old_openness + 0.01 * (bond_duration_days / 10.0), 2))
        return dict(npc.personality)

class RedemptionJourney:
    """Allows shunned/scandalized NPCs to actively win back lost prestige and social standing."""

    def __init__(self, npc_id: str):
        self.npc_id = npc_id
        self.public_penance_score = 0.0
        self.reparations_paid = 0.0
        self.apologies_offered: List[str] = []

    def offer_public_apology(self, victim_id: str, social_network: Any) -> Dict[str, Any]:
        """Apologizing to victims decays social hostility and builds forgiveness."""
        if victim_id not in self.apologies_offered:
            self.apologies_offered.append(victim_id)
            self.public_penance_score += 15.0
            social_network.adjust_relationship(victim_id, self.npc_id, 20.0)
            return {"apology_accepted": True, "penance_score": self.public_penance_score}
        return {"apology_accepted": False, "penance_score": self.public_penance_score}

    def pay_community_reparations(self, donor_npc: NPC, treasury: Any, amount: float = 50.0) -> bool:
        """Donating money to the municipal treasury for civic projects restores public prestige."""
        if donor_npc.wealth >= amount:
            donor_npc.wealth -= amount
            treasury.deposit(amount, reason="redemption_public_donation")
            self.reparations_paid += amount
            self.public_penance_score += 25.0
            return True
        return False
