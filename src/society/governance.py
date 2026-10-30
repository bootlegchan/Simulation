from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC

@dataclass
class BillProposal:
    bill_id: str
    title: str
    proposer_id: str
    target_law_type: str  # e.g., "tax_rate", "curfew_hour", "contraband_ban"
    proposed_value: Any
    votes_for: List[str] = field(default_factory=list)
    votes_against: List[str] = field(default_factory=list)
    is_enacted: bool = False

class GovernanceEngine:
    """Manages bill proposals, civic voting cycles weighted by prestige, and law enactment."""

    def __init__(self):
        self.proposals: Dict[str, BillProposal] = {}
        self.active_warrants: Dict[str, str] = {}  # suspect_id -> crime_type
        self.detained_npcs: Dict[str, int] = {}  # npc_id -> remaining_sentence_ticks

    def propose_bill(
        self,
        bill_id: str,
        title: str,
        proposer_id: str,
        target_law_type: str,
        proposed_value: Any
    ) -> BillProposal:
        proposal = BillProposal(bill_id, title, proposer_id, target_law_type, proposed_value)
        self.proposals[bill_id] = proposal
        return proposal

    def cast_vote(self, bill_id: str, voter: NPC, vote_for: bool) -> bool:
        if bill_id not in self.proposals:
            return False
        prop = self.proposals[bill_id]
        
        # Remove previous vote if exists
        if voter.id in prop.votes_for:
            prop.votes_for.remove(voter.id)
        if voter.id in prop.votes_against:
            prop.votes_against.remove(voter.id)

        if vote_for:
            prop.votes_for.append(voter.id)
        else:
            prop.votes_against.append(voter.id)

        return True

    def evaluate_proposal_outcome(self, bill_id: str, npcs: Dict[str, NPC]) -> bool:
        """Evaluate bill outcome weighted by voters' prestige scores."""
        if bill_id not in self.proposals:
            return False
        prop = self.proposals[bill_id]

        weight_for = sum(npcs[v_id].personality.get("conscientiousness", 0.5) * 10.0 for v_id in prop.votes_for if v_id in npcs)
        weight_against = sum(npcs[v_id].personality.get("conscientiousness", 0.5) * 10.0 for v_id in prop.votes_against if v_id in npcs)

        if weight_for > weight_against:
            prop.is_enacted = True
            return True
        return False

    def issue_warrant(self, suspect_id: str, crime_type: str) -> None:
        self.active_warrants[suspect_id] = crime_type

    def detain_suspect(self, npc_id: str, sentence_ticks: int = 10) -> None:
        if npc_id in self.active_warrants:
            del self.active_warrants[npc_id]
        self.detained_npcs[npc_id] = sentence_ticks

    def tick_sentence_counts(self) -> List[str]:
        released = []
        for npc_id, remaining in list(self.detained_npcs.items()):
            if remaining <= 1:
                released.append(npc_id)
                del self.detained_npcs[npc_id]
            else:
                self.detained_npcs[npc_id] = remaining - 1
        return released
