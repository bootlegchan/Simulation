from typing import Dict, Any, Optional

class PsychologicalStressMeter:
    def __init__(self, npc_id: str, stress_level: float = 0.0):
        self.npc_id = npc_id
        self.stress_level = stress_level

    def add_stress(self, amount: float, cause: str = "") -> None:
        self.stress_level = min(100.0, self.stress_level + amount)

    def evaluate_coping_state(self) -> Optional[str]:
        if self.stress_level >= 70.0:
            return "TAVERN_BINGE"
        elif self.stress_level >= 50.0:
            return "ISOLATION"
        return None

class TraumaAnchor:
    def __init__(self, room_id: str, trauma_severity: float = 50.0):
        self.room_id = room_id
        self.trauma_severity = trauma_severity

    def get_action_cost_multiplier(self) -> float:
        return 1.0 + (self.trauma_severity / 100.0)
