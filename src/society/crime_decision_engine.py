"""Crime Decision Engine."""
from typing import Any, Dict, List, Optional

class CrimeDecisionEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def evaluate_risk_and_modus_operandi(self, perpetrator: Any, location_id: str, is_hotspot: bool, has_lantern: bool, has_watch: bool, context: Any) -> str:
        return "LAY_LOW" if (has_watch or has_lantern) else "PROCEED"

    def select_target(self, perpetrator: Any, candidates: List[Any], context: Any) -> Any:
        return candidates[0] if candidates else None

    def select_crime_type(self, perpetrator: Any, victim: Any, context: Any, tick: int) -> str:
        return "THEFT"

    def calculate_stolen_gold(self, perpetrator: Any, victim: Any, crime_type: str, context: Any) -> float:
        return min(4.0, victim.wealth * 0.20) if victim else 2.0
