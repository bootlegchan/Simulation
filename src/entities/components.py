from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class NeedComponent:
    needs: Dict[str, float] = field(default_factory=lambda: {"hunger": 20.0, "energy": 90.0, "social": 50.0, "romance": 50.0})
    decay_rates: Dict[str, float] = field(default_factory=lambda: {"hunger": 0.5, "energy": -0.3, "social": -0.2, "romance": -0.1})

    def apply_decay() -> None:
        for need, decay in self.decay_rates.items():
            curr = self.needs.get(need, 50.0)
            self.needs[need] = max(0.0, min(100.0, curr + decay))

@dataclass
class PersonalityComponent:
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

@dataclass
class PsychologyComponent:
    stress: float = 0.0
    resilience: float = 50.0
    coping_state: str = "NORMAL"
    trauma_anchors: List[str] = field(default_factory=list)

@dataclass
class SocialComponent:
    faction_id: Optional[str] = None
    civic_role: Optional[str] = None
    prestige: float = 50.0
    social_class: str = "CITIZEN"
    stigma: float = 0.0
    is_shunned: bool = False
