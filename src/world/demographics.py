"""
Demographic Pyramids, Age Brackets, and Physical/Cognitive Capability Scaling.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

class LifeStage(Enum):
    CHILD = "CHILD"        # 0 - 12 yrs
    YOUTH = "YOUTH"        # 13 - 19 yrs
    ADULT = "ADULT"        # 20 - 55 yrs
    ELDER = "ELDER"        # 56+ yrs

@dataclass
class CapabilityProfile:
    physical_work_capacity: float = 1.0   # 0.0 to 1.5 multiplier
    movement_speed_weight: float = 1.0    # 0.0 to 1.5 multiplier
    cognitive_resilience: float = 1.0     # 0.0 to 1.5 multiplier
    energy_decay_rate: float = -0.3       # Base decay rate per tick
    illness_vulnerability: float = 0.1     # Risk factor for weather shocks

class DemographicPyramid:
    """Manages age distributions, life stages, and capability scaling for town inhabitants."""

    @staticmethod
    def get_life_stage(age_years: int) -> LifeStage:
        if age_years <= 12:
            return LifeStage.CHILD
        elif age_years <= 19:
            return LifeStage.YOUTH
        elif age_years <= 55:
            return LifeStage.ADULT
        else:
            return LifeStage.ELDER

    @staticmethod
    def calculate_capabilities(age_years: int) -> CapabilityProfile:
        stage = DemographicPyramid.get_life_stage(age_years)

        if stage == LifeStage.CHILD:
            return CapabilityProfile(
                physical_work_capacity=0.2,
                movement_speed_weight=1.1,
                cognitive_resilience=0.6,
                energy_decay_rate=-0.5,
                illness_vulnerability=0.3
            )
        elif stage == LifeStage.YOUTH:
            return CapabilityProfile(
                physical_work_capacity=0.8,
                movement_speed_weight=1.3,
                cognitive_resilience=0.8,
                energy_decay_rate=-0.4,
                illness_vulnerability=0.1
            )
        elif stage == LifeStage.ADULT:
            return CapabilityProfile(
                physical_work_capacity=1.2,
                movement_speed_weight=1.0,
                cognitive_resilience=1.0,
                energy_decay_rate=-0.3,
                illness_vulnerability=0.1
            )
        else:  # ELDER
            return CapabilityProfile(
                physical_work_capacity=0.5,
                movement_speed_weight=0.7,
                cognitive_resilience=1.2,  # Experienced & resilient
                energy_decay_rate=-0.2,
                illness_vulnerability=0.4
            )

    @staticmethod
    def evaluate_settlement_demographics(npcs: Dict[str, Any]) -> Dict[str, Any]:
        counts = {LifeStage.CHILD: 0, LifeStage.YOUTH: 0, LifeStage.ADULT: 0, LifeStage.ELDER: 0}
        total_age = 0

        for npc in npcs.values():
            age = getattr(npc, "age_years", 30)
            stage = DemographicPyramid.get_life_stage(age)
            counts[stage] += 1
            total_age += age

        total = max(1, len(npcs))
        return {
            "total_population": total,
            "average_age_years": round(total_age / total, 1),
            "stage_counts": {k.value: v for k, v in counts.items()},
            "stage_ratios": {k.value: round(v / total, 3) for k, v in counts.items()}
        }
