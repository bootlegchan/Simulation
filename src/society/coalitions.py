"""
Emergent Political Faction Alliances & Coalition Voting Engine.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.society.factions import FactionHostilityMatrix
from src.society.governance import BillProposal

@dataclass
class FactionCoalition:
    coalition_id: str
    name: str
    member_faction_ids: List[str]
    cohesion_score: float = 100.0  # 0.0 to 100.0
    shared_policy_agenda: Optional[str] = None

class CoalitionManager:
    """Manages multi-faction political coalitions and unified bloc voting."""

    def __init__(self):
        self.coalitions: Dict[str, FactionCoalition] = {}

    def form_coalition(
        self,
        coalition_id: str,
        name: str,
        faction_ids: List[str],
        hostility_matrix: FactionHostilityMatrix,
        policy_agenda: Optional[str] = None
    ) -> Optional[FactionCoalition]:
        """Form coalition if mutual hostilities between member factions are low (<= 30.0)."""
        for i in range(len(faction_ids)):
            for j in range(i + 1, len(faction_ids)):
                hostility = hostility_matrix.get_hostility(faction_ids[i], faction_ids[j])
                if hostility > 30.0:
                    return None  # Hostility too high for alliance

        coalition = FactionCoalition(
            coalition_id=coalition_id,
            name=name,
            member_faction_ids=list(faction_ids),
            cohesion_score=85.0,
            shared_policy_agenda=policy_agenda,
        )
        self.coalitions[coalition_id] = coalition
        return coalition

    def cast_coalition_bloc_vote(
        self,
        coalition_id: str,
        proposal: BillProposal,
        npcs: Dict[str, NPC]
    ) -> Dict[str, Any]:
        """Cast unified votes across all coalition member NPCs."""
        if coalition_id not in self.coalitions:
            return {"votes_cast": 0, "decision": "neutral"}

        coalition = self.coalitions[coalition_id]

        # Determine bloc direction based on agenda alignment or majority preference
        favors_proposal = proposal.target_law_type == coalition.shared_policy_agenda or "Relief" in proposal.title
        voter_count = 0

        for npc in npcs.values():
            if npc.faction_id in coalition.member_faction_ids:
                if favors_proposal:
                    if npc.id not in proposal.votes_for:
                        proposal.votes_for.append(npc.id)
                    if npc.id in proposal.votes_against:
                        proposal.votes_against.remove(npc.id)
                else:
                    if npc.id not in proposal.votes_against:
                        proposal.votes_against.append(npc.id)
                    if npc.id in proposal.votes_for:
                        proposal.votes_for.remove(npc.id)
                voter_count += 1

        return {
            "coalition_id": coalition_id,
            "voter_count": voter_count,
            "decision": "FOR" if favors_proposal else "AGAINST",
            "cohesion": coalition.cohesion_score,
        }

    def adjust_cohesion(self, coalition_id: str, delta: float) -> float:
        if coalition_id in self.coalitions:
            coalition = self.coalitions[coalition_id]
            coalition.cohesion_score = max(0.0, min(100.0, coalition.cohesion_score + delta))
            return coalition.cohesion_score
        return 0.0
