from typing import Any, Dict, List, Optional, Tuple

class Faction:
    """Socio-political faction or guild."""

    def __init__(self, faction_id: str, name: str, member_ids: Optional[List[str]] = None, leader_id: Optional[str] = None):
        self.id = faction_id
        self.name = name
        self.member_ids = member_ids if member_ids is not None else []
        self.leader_id = leader_id
        self.treasury_vault = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "member_ids": self.member_ids,
            "leader_id": self.leader_id,
            "treasury_vault": self.treasury_vault,
        }

class FactionHostilityMatrix:
    """Matrix tracking pairwise hostility between factions."""

    def __init__(self):
        self.hostility: Dict[Tuple[str, str], float] = {}

    def set_hostility(self, f1: str, f2: str, score: float) -> None:
        val = max(-100.0, min(100.0, score))
        self.hostility[(f1, f2)] = val
        self.hostility[(f2, f1)] = val

    def get_hostility(self, f1: str, f2: str) -> float:
        return self.hostility.get((f1, f2), 0.0)
