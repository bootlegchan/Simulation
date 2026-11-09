"""Culinary metabolism and meal appraisal."""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

class MealTier(Enum):
    COARSE_RATION = "COARSE_RATION"
    HOMESTYLE_FAIR = "HOMESTYLE_FAIR"
    HEARTHSIDE_FEAST = "HEARTHSIDE_FEAST"
    MASTERWORK_BANQUET = "MASTERWORK_BANQUET"

@dataclass
class MealAppraisalRecord:
    appraisal_id: str
    meal_tier: MealTier
    quality_score: float

class CulinaryMetabolismEngine:
    def appraise_and_consume_meal(self, diner: Any, food_item: Any, cook: Optional[Any] = None, has_active_hearth: bool = False, current_tick: int = 0, random_roll: float = 0.5) -> MealAppraisalRecord:
        tier = MealTier.HOMESTYLE_FAIR if has_active_hearth else MealTier.COARSE_RATION
        diner.needs["hunger"] = max(0.0, diner.needs.get("hunger", 0.0) - 40.0)
        return MealAppraisalRecord(appraisal_id=f"app_{uuid.uuid4().hex[:6]}", meal_tier=tier, quality_score=65.0)
