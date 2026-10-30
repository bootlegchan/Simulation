from enum import Enum
from typing import Dict, Any, List, Optional
from src.entities.npc import NPC
from src.entities.item import ItemInstance

class ViceType(Enum):
    ALCOHOL = "ALCOHOL"
    GAMBLING = "GAMBLING"
    VICE_DEN = "VICE_DEN"
    SMUGGLING = "SMUGGLING"
    CRIME = "CRIME"

class ViceTracker:
    """Tracks NPC addictions, vice urges, and compulsive behaviors."""

    def __init__(self, npc_id: str, alcohol_dependence: float = 0.0, gambling_drive: float = 0.0, crime_propensity: float = 0.0):
        self.npc_id = npc_id
        self.alcohol_dependence = alcohol_dependence
        self.gambling_drive = gambling_drive
        self.crime_propensity = crime_propensity
        self.withdrawal_stress = 0.0

    def calculate_vice_urgency(self, current_stress: float, hour: int) -> Dict[str, float]:
        """High stress or night time triggers vice compulsion."""
        urgency = {}
        night_bonus = 30.0 if (hour >= 21 or hour < 6) else 0.0

        if self.alcohol_dependence > 20.0:
            urgency["drink_alcohol"] = (self.alcohol_dependence * 0.6) + (current_stress * 0.4) + night_bonus
        if self.gambling_drive > 20.0:
            urgency["gamble_at_vice_den"] = (self.gambling_drive * 0.7) + night_bonus
        if self.crime_propensity > 30.0:
            urgency["commit_theft_or_burglary"] = (self.crime_propensity * 0.8) + (current_stress * 0.3) + night_bonus

        return urgency

    def indulge_vice(self, vice_type: ViceType, cost: float, npc: NPC) -> Dict[str, Any]:
        """Executing vice indulgence reduces stress but drains wealth and risks addiction growth."""
        if npc.wealth >= cost:
            npc.wealth -= cost
            if vice_type == ViceType.ALCOHOL:
                self.alcohol_dependence = min(100.0, self.alcohol_dependence + 2.0)
                npc.needs["energy"] = max(0.0, npc.needs.get("energy", 50.0) - 15.0)
                return {"success": True, "stress_reduction": 35.0, "wealth_spent": cost}
            elif vice_type == ViceType.GAMBLING:
                self.gambling_drive = min(100.0, self.gambling_drive + 3.0)
                return {"success": True, "stress_reduction": 25.0, "wealth_spent": cost}
        return {"success": False, "reason": "Insufficient funds for vice"}

class DarkCrimeEngine:
    """Manages realistic non-utopian crime: theft, burglary, blackmail, and brawling."""

    @staticmethod
    def evaluate_crime_compulsion(npc: NPC, location_guards_present: int = 0) -> bool:
        """Determines if a desperate or impulsive NPC decides to commit crime."""
        crime_prop = npc.vices.get("crime_propensity", 0.0)
        poverty = max(0.0, 50.0 - npc.wealth)
        is_impulsive = npc.cognition.get("decision_quality") in ("Impulsive", "Short-sighted")
        laziness = npc.cognition.get("laziness", 0.0)

        risk_penalty = location_guards_present * 40.0
        crime_score = (crime_prop * 0.5) + (poverty * 0.8) + (laziness * 30.0) + (20.0 if is_impulsive else 0.0) - risk_penalty

        return crime_score >= 50.0

    @staticmethod
    def execute_burglary(burglar: NPC, target_pantry_or_chest: Any, witness_ids: List[str]) -> Dict[str, Any]:
        """Burglary steals wealth or items from private pantries/chests."""
        stolen_amount = min(30.0, getattr(target_pantry_or_chest, "wealth", 30.0))
        burglar.wealth += stolen_amount
        burglar.vices["crime_propensity"] = min(100.0, burglar.vices.get("crime_propensity", 0.0) + 5.0)

        is_witnessed = len(witness_ids) > 0
        return {
            "success": True,
            "stolen_amount": stolen_amount,
            "is_witnessed": is_witnessed,
            "witnesses": witness_ids
        }
