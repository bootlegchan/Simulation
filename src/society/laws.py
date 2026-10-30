from typing import Any, Dict, List

class LegalSystem:
    """Evaluates witnessed vs unwitnessed illegal actions and sanctions."""

    @staticmethod
    def evaluate_crime(action_type: str, actor_id: str, witnesses: List[str]) -> Dict[str, Any]:
        is_crime = action_type in ("steal", "assault", "smuggle")
        has_witnesses = len(witnesses) > 0
        
        return {
            "is_crime": is_crime,
            "is_witnessed": is_crime and has_witnesses,
            "suspect_id": actor_id if has_witnesses else "unknown",
            "fine_amount": 50.0 if is_crime else 0.0,
            "witnesses": witnesses if is_crime else []
        }
