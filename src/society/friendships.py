from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

@dataclass
class BondMilestone:
    milestone_id: str
    event_name: str
    tick: int
    bond_strength_bonus: float

class FriendshipLifecycle:
    """Manages friendship bond progression, crisis milestones, social drifting, and reconciliation."""

    def __init__(self, npc_a_id: str, npc_b_id: str):
        self.npc_a_id = npc_a_id
        self.npc_b_id = npc_b_id
        self.bond_strength = 50.0  # 0 to 100
        self.days_without_interaction = 0
        self.milestones: List[BondMilestone] = []

    def record_crisis_milestone(self, event_name: str, tick: int, bonus: float = 25.0) -> BondMilestone:
        """Surviving a crisis together permanently strengthens the bond and creates milestone protection."""
        milestone = BondMilestone(
            milestone_id=f"ms_{len(self.milestones)+1}",
            event_name=event_name,
            tick=tick,
            bond_strength_bonus=bonus
        )
        self.milestones.append(milestone)
        self.bond_strength = min(100.0, self.bond_strength + bonus)
        return milestone

    def apply_social_drifting(self) -> float:
        """Social drifting: friendships decay when NPCs stop interacting, but milestones cushion the decay."""
        self.days_without_interaction += 1
        decay_rate = 1.5
        # Protection cushion from milestones
        cushion = sum(m.bond_strength_bonus * 0.2 for m in self.milestones)
        effective_decay = max(0.2, decay_rate - cushion)
        self.bond_strength = max(0.0, self.bond_strength - effective_decay)
        return self.bond_strength

    def record_interaction(self, quality: float = 10.0) -> float:
        """Resets drifting counter and strengthens friendship."""
        self.days_without_interaction = 0
        self.bond_strength = min(100.0, self.bond_strength + quality)
        return self.bond_strength

    def attempt_mediated_reconciliation(
        self,
        mediator_npc: NPC,
        social_network: Any
    ) -> Dict[str, Any]:
        """A mutual high-trust friend mediates to bring two estranged friends together."""
        mediator_trust_a = social_network.get_relationship(mediator_npc.id, self.npc_a_id)
        mediator_trust_b = social_network.get_relationship(mediator_npc.id, self.npc_b_id)

        # High charisma and trust increase reconciliation probability
        charisma = mediator_npc.personality.get("openness", 0.5) * 40.0
        trust_avg = (mediator_trust_a + mediator_trust_b) / 2.0
        success_chance = (charisma + trust_avg) / 100.0

        if success_chance >= 0.5:
            self.bond_strength = min(100.0, self.bond_strength + 30.0)
            social_network.adjust_relationship(self.npc_a_id, self.npc_b_id, 25.0)
            social_network.adjust_relationship(self.npc_b_id, self.npc_a_id, 25.0)
            return {"reconciled": True, "new_bond_strength": self.bond_strength, "success_chance": success_chance}
        
        return {"reconciled": False, "new_bond_strength": self.bond_strength, "success_chance": success_chance}
