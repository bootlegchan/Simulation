from typing import Dict, Any

class RumorMutationEngine:
    @staticmethod
    def mutate_rumor(original_claim: str, teller_bias: float, hop_count: int) -> Dict[str, Any]:
        severity = 10.0 + (hop_count * 3.0) + (teller_bias * 5.0)
        mutated_claim = f"ESCALATED: {original_claim} (Treason/Malice Alleged)" if hop_count >= 3 else original_claim
        return {
            "mutated_claim": mutated_claim,
            "severity": severity,
            "hop_count": hop_count
        }

class SmearCampaign:
    @staticmethod
    def execute(sponsor_id: str, target_id: str, investment: float) -> Dict[str, Any]:
        damage = min(50.0, investment / 2.0)
        return {
            "sponsor_id": sponsor_id,
            "target_id": target_id,
            "prestige_damage": damage
        }
