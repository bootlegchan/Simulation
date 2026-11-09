"""Bilateral Joint Commitments and Flow Locks."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid

class SocialCommitmentType(str, Enum):
    ROMANTIC_DATE = "ROMANTIC_DATE"
    COMMUNAL_MEAL = "COMMUNAL_MEAL"
    CONVERSATIONAL_CHAT = "CONVERSATIONAL_CHAT"
    RECREATIONAL_CONTEST = "RECREATIONAL_CONTEST"
    VOCATIONAL_MENTORSHIP = "VOCATIONAL_MENTORSHIP"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            normalized = value.upper()
            pseudo = str.__new__(cls, normalized)
            pseudo._value_ = normalized
            pseudo._name_ = normalized
            return pseudo
        return None

@dataclass
class CommitmentDefinition:
    commitment_type: str
    name: str
    base_duration_ticks: int = 60

class CommitmentRegistry:
    _instance: Optional["CommitmentRegistry"] = None

    @classmethod
    def get_instance(cls) -> "CommitmentRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.definitions: Dict[str, CommitmentDefinition] = {
            s.value: CommitmentDefinition(s.value, s.value.title()) for s in SocialCommitmentType
        }

    def register_commitment(self, definition: CommitmentDefinition) -> None:
        self.definitions[definition.commitment_type.upper()] = definition

@dataclass
class CommitmentContract:
    contract_id: str
    commitment_type: SocialCommitmentType
    participant_ids: List[str]
    location_id: str
    expected_duration_ticks: int
    ticks_elapsed: int = 0

class BilateralCommitmentEngine:
    def __init__(self):
        self.active_contracts: Dict[str, CommitmentContract] = {}

    def is_committed(self, npc_id: str) -> bool:
        return any(npc_id in c.participant_ids for c in self.active_contracts.values())

    def get_active_commitment(self, npc_id: str) -> Optional[CommitmentContract]:
        for c in self.active_contracts.values():
            if npc_id in c.participant_ids:
                return c
        return None

    def form_commitment(self, initiator: Any, peers: List[Any], c_type: SocialCommitmentType, location_id: str, dur_ticks: int, tick: int) -> CommitmentContract:
        cid = f"commit_{uuid.uuid4().hex[:6]}"
        contract = CommitmentContract(contract_id=cid, commitment_type=c_type, participant_ids=[initiator.id] + [p.id for p in peers], location_id=location_id, expected_duration_ticks=dur_ticks)
        self.active_contracts[cid] = contract
        return contract

    def evaluate_departure_permission(self, npc: Any, action_name: str, tick: int, context: Any) -> Tuple[bool, str]:
        # Preemptions or biological survival can break commitment
        if "STARVATION" in action_name or "COLLAPSE" in action_name:
            return (True, "Biological emergency")
        return (False, "Committed to joint activity")

    def complete_commitment_gracefully(self, contract_id: str, npcs: Dict[str, Any], tick: int, context: Any) -> None:
        self.active_contracts.pop(contract_id, None)

    def _cleanup_commitment(self, contract_id: str) -> None:
        self.active_contracts.pop(contract_id, None)
