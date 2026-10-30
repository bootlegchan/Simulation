from enum import Enum
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

class CliqueMoralAlignment(Enum):
    VIRTUOUS = "VIRTUOUS"
    MERCANTILE = "MERCANTILE"
    DEVIANT_UNDERWORLD = "DEVIANT_UNDERWORLD"

class Clique:
    """An informal social group or clique with shared consensus and moral alignment standards."""

    def __init__(
        self,
        clique_id: str,
        name: str,
        leader_id: str,
        member_ids: List[str],
        moral_alignment: CliqueMoralAlignment = CliqueMoralAlignment.MERCANTILE
    ):
        self.clique_id = clique_id
        self.name = name
        self.leader_id = leader_id
        self.member_ids = list(member_ids)
        self.moral_alignment = moral_alignment
        self.target_attitudes: Dict[str, float] = {}  # target_npc_id -> collective opinion (-100 to +100)

    def update_consensus(self, target_npc_id: str, npcs: Dict[str, NPC], social_network: Any) -> float:
        """Calculates group consensus, heavily weighted by the clique leader's opinion."""
        if self.leader_id in npcs:
            leader_opinion = social_network.get_relationship(self.leader_id, target_npc_id)
        else:
            leader_opinion = 0.0

        member_opinions = [
            social_network.get_relationship(m_id, target_npc_id)
            for m_id in self.member_ids if m_id in npcs
        ]
        
        avg_member_opinion = sum(member_opinions) / len(member_opinions) if member_opinions else 0.0
        consensus = (0.6 * leader_opinion) + (0.4 * avg_member_opinion)
        self.target_attitudes[target_npc_id] = round(consensus, 2)
        return consensus

    def evaluate_peer_pressure(
        self,
        member_id: str,
        target_npc_id: str,
        npcs: Dict[str, NPC],
        social_network: Any
    ) -> Dict[str, Any]:
        """Applies peer pressure to force individual members to conform to clique consensus."""
        if member_id not in self.member_ids or member_id not in npcs:
            return {"conformed": False, "peer_pressure_applied": False}

        member_npc = npcs[member_id]
        consensus = self.target_attitudes.get(target_npc_id, 0.0)
        current_individual_op = social_network.get_relationship(member_id, target_npc_id)

        conformity = member_npc.personality.get("conscientiousness", 0.5) * 50.0
        opinion_diff = consensus - current_individual_op

        if abs(opinion_diff) > 20.0:
            shift = (opinion_diff * 0.4) * (conformity / 50.0)
            social_network.adjust_relationship(member_id, target_npc_id, shift)
            return {
                "conformed": True,
                "peer_pressure_applied": True,
                "opinion_shift": round(shift, 2),
                "new_relationship_score": social_network.get_relationship(member_id, target_npc_id)
            }

        return {"conformed": True, "peer_pressure_applied": False, "opinion_shift": 0.0}

    def evaluate_deviance_normalization(self, target_npc: NPC, event_bus: Any) -> Dict[str, Any]:
        """Deviant cliques normalize crime and lower norm friction for members."""
        if self.moral_alignment == CliqueMoralAlignment.DEVIANT_UNDERWORLD:
            return {
                "deviance_normalized": True,
                "norm_friction_reduction": 25.0,
                "clique_name": self.name
            }
        elif self.moral_alignment == CliqueMoralAlignment.VIRTUOUS:
            return {
                "deviance_normalized": False,
                "norm_friction_reduction": 0.0,
                "peer_pressure_sanction": 30.0,
                "clique_name": self.name
            }
        return {"deviance_normalized": False, "norm_friction_reduction": 0.0}

class CliqueManager:
    """Manages multi-clique loyalty tests and group dynamics across townfolk."""

    def __init__(self):
        self.cliques: Dict[str, Clique] = {}

    def register_clique(self, clique: Clique) -> None:
        self.cliques[clique.clique_id] = clique

    def evaluate_loyalty_conflict(self, npc_id: str, clique_a_id: str, clique_b_id: str) -> Dict[str, Any]:
        """Calculates social conflict when an NPC belongs to or interacts with rival cliques."""
        if clique_a_id in self.cliques and clique_b_id in self.cliques:
            clique_a = self.cliques[clique_a_id]
            clique_b = self.cliques[clique_b_id]
            if npc_id in clique_a.member_ids and npc_id in clique_b.member_ids:
                return {
                    "has_loyalty_conflict": True,
                    "conflict_stress_penalty": 25.0,
                    "rival_cliques": [clique_a.name, clique_b.name]
                }
        return {"has_loyalty_conflict": False, "conflict_stress_penalty": 0.0}
