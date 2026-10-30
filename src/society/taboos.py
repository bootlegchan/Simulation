from typing import Dict, Any

class StigmaTracker:
    def __init__(self, npc_id: str, stigma_score: float = 0.0):
        self.npc_id = npc_id
        self.stigma_score = stigma_score

    @property
    def is_shunned(self) -> bool:
        return self.stigma_score >= 50.0

    def add_stigma(self, amount: float, reason: str = "") -> None:
        self.stigma_score = min(100.0, self.stigma_score + amount)

    def apply_penance(self, amount: float) -> None:
        self.stigma_score = max(0.0, self.stigma_score - amount)

    def to_dict(self) -> Dict[str, Any]:
        return {"npc_id": self.npc_id, "stigma_score": self.stigma_score}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StigmaTracker":
        return cls(npc_id=data["npc_id"], stigma_score=data.get("stigma_score", 0.0))
