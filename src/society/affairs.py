from enum import Enum
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.society.romance import InterpersonalBond, RelationshipStage

class AffairState(Enum):
    SECRET = "SECRET"
    SUSPECTED = "SUSPECTED"
    EXPOSED = "EXPOSED"

class ClandestineRendezvous:
    """Manages secret meetings and risk of affair discovery."""

    def __init__(self, lover_a_id: str, lover_b_id: str, secret_location_id: str):
        self.lover_a_id = lover_a_id
        self.lover_b_id = lover_b_id
        self.secret_location_id = secret_location_id
        self.state = AffairState.SECRET
        self.suspicion_score = 0.0

    def evaluate_discovery_risk(
        self,
        current_room_id: str,
        co_located_npc_ids: List[str],
        primary_partner_ids: List[str]
    ) -> Dict[str, Any]:
        """Calculates discovery risk based on location secrecy and present witnesses."""
        if current_room_id != self.secret_location_id:
            self.suspicion_score += 15.0

        is_witnessed = False
        witness_ids = []

        for npc_id in co_located_npc_ids:
            if npc_id not in (self.lover_a_id, self.lover_b_id):
                is_witnessed = True
                witness_ids.append(npc_id)
                if npc_id in primary_partner_ids:
                    # Caught directly by spouse/partner!
                    self.state = AffairState.EXPOSED
                    self.suspicion_score = 100.0
                    return {
                        "is_exposed": True,
                        "caught_by_partner": True,
                        "witness_ids": witness_ids,
                        "suspicion_score": 100.0
                    }

        if is_witnessed:
            self.suspicion_score += 25.0
            if self.suspicion_score >= 75.0:
                self.state = AffairState.EXPOSED

        return {
            "is_exposed": self.state == AffairState.EXPOSED,
            "caught_by_partner": False,
            "witness_ids": witness_ids,
            "suspicion_score": self.suspicion_score
        }

class CommunitySideTakingEngine:
    """When a breakup or exposed affair occurs, forces mutual friends to take sides."""

    @staticmethod
    def resolve_community_reaction(
        betrayed_id: str,
        culprit_id: str,
        mutual_friend_ids: List[str],
        npcs: Dict[str, NPC],
        social_network: Any
    ) -> Dict[str, Any]:
        sides = {betrayed_id: [], culprit_id: [], "neutral": []}

        for friend_id in mutual_friend_ids:
            if friend_id in npcs:
                friend_npc = npcs[friend_id]
                rel_to_betrayed = social_network.get_relationship(friend_id, betrayed_id)
                rel_to_culprit = social_network.get_relationship(friend_id, culprit_id)

                # Conscientious/Honorable friends side with the betrayed party
                honesty = friend_npc.personality.get("conscientiousness", 0.5)
                score_betrayed = rel_to_betrayed + (honesty * 30.0)
                score_culprit = rel_to_culprit - (honesty * 20.0)

                if score_betrayed > score_culprit + 10.0:
                    sides[betrayed_id].append(friend_id)
                    # Reduce relationship with culprit
                    social_network.adjust_relationship(friend_id, culprit_id, -40.0)
                elif score_culprit > score_betrayed + 10.0:
                    sides[culprit_id].append(friend_id)
                    social_network.adjust_relationship(friend_id, betrayed_id, -30.0)
                else:
                    sides["neutral"].append(friend_id)

        return sides

class UnrequitedLoveTracker:
    """Tracks one-sided romantic crushes, emotional longing, and envy."""

    def __init__(self, lover_id: str, target_id: str):
        self.lover_id = lover_id
        self.target_id = target_id
        self.longing_intensity = 20.0
        self.envy_level = 0.0

    def update_longing(self, is_target_in_relationship: bool, interaction_frequency: float) -> float:
        """Increases longing when interacting; increases envy if target is with someone else."""
        self.longing_intensity = min(100.0, self.longing_intensity + (interaction_frequency * 5.0))
        if is_target_in_relationship:
            self.envy_level = min(100.0, self.envy_level + 15.0)
        return self.longing_intensity
