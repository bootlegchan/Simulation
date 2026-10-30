from enum import Enum
from typing import Dict, Any, Union

class SocialClass(Enum):
    NOBILITY = "NOBILITY"
    GENTRY = "GENTRY"
    CITIZEN = "CITIZEN"
    LABORER = "LABORER"
    OUTCAST = "OUTCAST"

    @classmethod
    def get_class_for_prestige(cls, prestige: float) -> "SocialClass":
        if prestige >= 80.0:
            return cls.NOBILITY
        elif prestige >= 60.0:
            return cls.GENTRY
        elif prestige >= 40.0:
            return cls.CITIZEN
        elif prestige >= 20.0:
            return cls.LABORER
        else:
            return cls.OUTCAST

class PrestigeCalculator:
    @staticmethod
    def calculate_prestige(
        target: Union[float, Any] = 50.0,
        civic_office_tier: int = 0,
        public_opinion: float = 50.0,
        faction_standing: float = 50.0,
        criminal_record_count: int = 0,
        **kwargs
    ) -> float:
        """Calculates prestige from net worth or an NPC object."""
        net_worth = kwargs.get("net_worth", None)
        if net_worth is not None:
            nw_val = float(net_worth)
        elif hasattr(target, "wealth"):
            nw_val = getattr(target, "wealth", 50.0)
            civic_role = getattr(target, "civic_role", None)
            if civic_role == "Mayor":
                civic_office_tier = 2
            elif civic_role == "Sheriff":
                civic_office_tier = 1
        else:
            nw_val = float(target)

        wealth_score = min(40.0, nw_val / 25.0)
        office_score = civic_office_tier * 15.0
        opinion_score = (public_opinion / 100.0) * 20.0
        faction_score = (faction_standing / 100.0) * 15.0
        criminal_penalty = criminal_record_count * 25.0

        prestige = wealth_score + office_score + opinion_score + faction_score - criminal_penalty
        return max(0.0, min(100.0, prestige))
